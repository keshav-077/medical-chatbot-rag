FROM python:3.11-slim-bookworm

WORKDIR /app

# Install system dependencies for psycopg2-binary
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set production environment
ENV FLASK_ENV=production

# Expose port
EXPOSE 8080

# Run the application
CMD ["python", "app.py"]