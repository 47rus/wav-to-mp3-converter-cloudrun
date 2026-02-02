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

# Copy the application code into the container
COPY ./app .

# Expose the port the app runs on
EXPOSE 8000

# Run the Uvicorn server when the container launches, using the port defined by Cloud Run
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
