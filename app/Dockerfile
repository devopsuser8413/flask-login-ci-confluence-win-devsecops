# Use official Python runtime as a parent image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

COPY ../requirements.txt ./requirements.txt

# Copy files
COPY . /app

# Install dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Expose Flask port
EXPOSE 5000

# Run the Flask app
CMD ["python", "app.py"]
