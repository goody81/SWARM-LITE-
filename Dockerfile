FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV SWARM_LITE_LOG_LEVEL=INFO

# Run the system
CMD ["python", "main.py"]
