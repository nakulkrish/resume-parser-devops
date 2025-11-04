FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies for pdfplumber
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first (for Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy ALL application code (this is critical!)
COPY . .

# Set PYTHONPATH so Python can find app.py
ENV PYTHONPATH=/app

# Create uploads directory
RUN mkdir -p uploads

# Expose Flask port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:5000/health', timeout=5)" || exit 1

# Run the application
CMD ["python", "app.py"]