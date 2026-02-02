# Use an official Python runtime as a parent image
FROM python:3.11-slim-bullseye

# Set the working directory in the container
WORKDIR /app

# Install ffmpeg, which pydub depends on
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project context into the container
COPY . .

# Expose the port the app runs on
EXPOSE 8080

# Run the production server Gunicorn with a Uvicorn worker using shell form
CMD gunicorn -w 1 -k uvicorn.workers.UvicornWorker --forwarded-allow-ips='*' --bind 0.0.0.0:$PORT app.main:app
