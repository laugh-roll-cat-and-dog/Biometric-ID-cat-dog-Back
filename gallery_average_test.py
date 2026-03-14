from pathlib import Path
import torch.nn.functional as F
from app.config.database import SessionLocal
from app.models import DogPhoto
from app.utils.embedding import embed_image
import torch
import os


def evaluate_gallery_tests(source_dir: str) -> None:
    """Evaluate test images by matching each against DB embeddings.

    Expected layout per dog: gallery_data/<dog_id>/test/*.jpg
    """

    pathlist = []
    print(f"Source directory: {source_dir}")
    for file_name in os.listdir(source_dir):
        if not file_name.startswith("."):
            pathlist.append(file_name)
    pathlist.sort()
    # print("list", pathlist)

    source_path = Path(source_dir)
    print(f"Source directory: {source_path}")
    db = SessionLocal()

    try:
        all_photos = db.query(DogPhoto).all()
        if not all_photos:
            print("[WARN] No photos found in database.")
            return

        # Keep normalized DB embeddings per photo so we can compute per-photo scores first.
        db_embeddings: list[tuple[int, torch.Tensor]] = []
        for photo in all_photos:
            if photo.embedding is None:
                raise ValueError(f"Missing embedding for photo_id={photo.id}")
            emb_tensor = torch.tensor(photo.embedding, dtype=torch.float32).squeeze()
            norm_emb = F.normalize(emb_tensor, p=2, dim=0)
            db_embeddings.append((photo.dog_id, norm_emb))

        if not db_embeddings:
            print("[WARN] No valid embeddings found in database.")
            return

        total = 0
        correct = 0

        for dog_name in pathlist:
            test_folder = source_path / dog_name / "test"
            if not test_folder.exists():
                print(f"[WARN] Test folder not found for {dog_name} at {test_folder}. Skipping.")
                continue

            image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}
            images = [
                f for f in test_folder.iterdir()
                if f.is_file() and f.suffix.lower() in image_extensions
            ]

            if not images:
                print(f"[WARN] No test images found for {dog_name} in {test_folder}. Skipping.")
                continue

            print(f"[INFO] Evaluating {len(images)} test images for dog {dog_name}")
            expected_dog_id = int(dog_name)

            for image_file in images:
                query = embed_image(image_file)
                query_emb = F.normalize(query[0], p=2, dim=0)

                # 1) Compute similarity per database photo.
                photo_results: list[dict[str, float | int]] = []
                for db_dog_id, db_emb in db_embeddings:
                    similarity = torch.matmul(query_emb, db_emb).item()
                    photo_results.append(
                        {
                            "dog_id": db_dog_id,
                            "similarity_score": similarity,
                        }
                    )

                # 2) Group photo scores by dog_id.
                grouped_scores: dict[int, list[float]] = {}
                for result in photo_results:
                    dog_id = int(result["dog_id"])
                    grouped_scores.setdefault(dog_id, []).append(float(result["similarity_score"]))

                # 3) Compute average similarity per dog.
                dog_averages: list[dict[str, float | int]] = []
                for dog_id, scores in grouped_scores.items():
                    avg_similarity = sum(scores) / len(scores)
                    dog_averages.append(
                        {
                            "dog_id": dog_id,
                            "avg_similarity": avg_similarity,
                        }
                    )

                # 4) Sort descending by average similarity and choose the best one.
                dog_averages.sort(key=lambda x: float(x["avg_similarity"]), reverse=True)

                best_dog_id = int(dog_averages[0]["dog_id"])
                best_avg_score = float(dog_averages[0]["avg_similarity"])

                is_correct = best_dog_id == expected_dog_id
                total += 1
                if is_correct:
                    correct += 1

                print(
                    f"[TEST] image={image_file.name} expected={expected_dog_id} "
                    f"predicted={best_dog_id} avg_score={best_avg_score:.4f} correct={is_correct}"
                )

        if total == 0:
            print("[WARN] No test images evaluated.")
            return

        accuracy = correct / total
        print("\n===== Evaluation Summary =====")
        print(f"Total images: {total}")
        print(f"Correct top-1: {correct}")
        print(f"Top-1 accuracy: {accuracy:.4f} ({accuracy * 100:.2f}%)")
    finally:
        db.close()

if __name__ == "__main__":
    gallery_path = "/Users/withwws/Documents/FinalProject/APP dev/Biometric-ID-cat-dog-Back/gallery_data"

    evaluate_gallery_tests(gallery_path)
