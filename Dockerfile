# Use Python 3.10
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (optional, but safe)
RUN apt-get update && apt-get install -y build-essential

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files into container
COPY . .

# Run bot.py
CMD ["python", "bot.py"]
