# Use Python 3.11 slim image
FROM python:3.11-slim

# ---------------------------
# Environment settings
# ---------------------------
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Hugging Face token (to be injected via build arg)
ARG HF_TOKEN
ENV HUGGINGFACE_HUB_TOKEN=$HF_TOKEN

# ---------------------------
# Set working directory
# ---------------------------
WORKDIR /app

# ---------------------------
# System dependencies
# ---------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------
# Install Python dependencies
# ---------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt 

# ---------------------------
# Copy project files
# ---------------------------
COPY . .
# COPY /home/mon/ai/dino_main_50_class.pt ./app/ai/dino_main_50_class.pt
# COPY /home/mon/ai/yolo.pt ./app/ai/yolo.pt

# ---------------------------
# Pre-login to Hugging Face (optional)
# ---------------------------
RUN test -n "$HUGGINGFACE_HUB_TOKEN" && hf auth login --token "$HUGGINGFACE_HUB_TOKEN"

# ---------------------------
# Expose port for FastAPI/Uvicorn
# ---------------------------
EXPOSE 8000

# ---------------------------
# Run the app
# ---------------------------
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]