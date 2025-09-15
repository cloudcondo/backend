# Python base
FROM python:3.12-slim

# Prevent Python from buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# OS packages (add build deps only if needed later)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

# Workdir
WORKDIR /app

# Install Python deps first (better Docker layer caching)
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . /app/

# Runtime env (safe defaults; we’ll override in ECS later)
ENV DJANGO_SETTINGS_MODULE=condo_backend.settings \
    PORT=8000

# Expose port for container platforms
EXPOSE 8000

# Start Gunicorn (Django’s WSGI server)
CMD ["gunicorn", "condo_backend.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
