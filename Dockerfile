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
RUN pip install --no-cache-dir -r requirements.txt accelerate

# ---------------------------
# Copy project files
# ---------------------------
COPY . .

# ---------------------------
# Pre-login to Hugging Face (optional)
# ---------------------------
RUN python -c "from huggingface_hub import login; import os; login(os.environ['HUGGINGFACE_HUB_TOKEN'])"

# ---------------------------
# Expose port for FastAPI/Uvicorn
# ---------------------------
EXPOSE 8000

# ---------------------------
# Run the app
# ---------------------------
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]