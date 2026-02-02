# WAV to MP3 Converter API for Cloud Run

## Overview

This project provides a simple API service to convert WAV audio files to MP3 format, optimized for voice transcription. The backend is built with FastAPI and is designed for easy deployment on Google Cloud Run using Docker.

The service accepts a `.wav` file, converts it to a 16kHz mono `.mp3` file, uploads it to a specified Google Drive folder, and returns a publicly downloadable link.

## Features

-   Accepts `.wav` file uploads via an API endpoint.
-   Converts WAV files to MP3 format (mono, 16kHz sample rate).
-   Uploads the converted MP3 file to a designated Google Drive folder.
-   Returns a JSON response containing the filename and a public download link.
-   Containerized with Docker for easy and consistent deployment.

## Project Structure

```
.
├── app/
│   └── main.py
├── Dockerfile
└── requirements.txt
```

-   `app/main.py`: The FastAPI application that handles the API endpoint, file conversion, and Google Drive upload.
-   `Dockerfile`: Defines the Docker image for the application.
-   `requirements.txt`: Lists the Python dependencies.

## Prerequisites

### For Local Development & Deployment

-   Python 3.9+ & `pip`
-   `ffmpeg`: Required for audio conversion. Install via your system's package manager (e.g., `sudo apt-get install ffmpeg` on Debian/Ubuntu or `brew install ffmpeg` on macOS).
-   Docker
-   Google Cloud SDK (for deploying to Cloud Run)

### Google Drive Configuration

1.  **Google Drive Folder:** Create a folder in Google Drive where the converted files will be stored. Note its `FOLDER_ID` from the URL (`https://drive.google.com/drive/folders/FOLDER_ID`).
2.  **Service Account:**
    -   Create a Google Cloud Service Account.
    -   Enable the Google Drive API for your project.
    -   Grant the service account the "Editor" role on the Google Drive folder you created.
    -   Download the service account's JSON key file.

## Local Development

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/47rus/wav-to-mp3-converter-cloudrun.git
    cd wav-to-mp3-converter-cloudrun
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment:**
    -   Rename your downloaded service account key to `wav-converter-service-account` and place it in the `app/` directory.
    -   Set the `FOLDER_ID` environment variable:
        ```bash
        export FOLDER_ID="your_google_drive_folder_id"
        ```

4.  **Run the application:**
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8000
    ```

5.  **Test the API:**
    Use a tool like `curl` to send a POST request to the `/convert/` endpoint with a WAV file.
    ```bash
    curl -X POST -F "file=@/path/to/your/audio.wav" http://localhost:8000/convert/
    ```
    You should receive a JSON response with the download link.

## Deployment to Google Cloud Run

1.  **Build the Docker image:**
    ```bash
    gcloud builds submit --tag gcr.io/[YOUR_PROJECT_ID]/wav-to-mp3-converter
    ```
    Replace `[YOUR_PROJECT_ID]` with your actual Google Cloud Project ID.

2.  **Deploy to Cloud Run:**
    -   Deploy the image, making sure to mount the service account key as a secret and set the `FOLDER_ID` environment variable.
    -   **Via Command Line:**
        ```bash
        # Create the secret from your key file
        gcloud secrets create wav-converter-service-account --data-file=app/wav-converter-service-account

        # Deploy the service
        gcloud run deploy wav-to-mp3-converter \
          --image gcr.io/[YOUR_PROJECT_ID]/wav-to-mp3-converter \
          --platform managed \
          --region [YOUR_REGION] \
          --allow-unauthenticated \
          --set-env-vars="FOLDER_ID=[YOUR_FOLDER_ID]" \
          --add-volume="name=sa-volume,secret=name=wav-converter-service-account,items=[key=latest,path=wav-converter-service-account]" \
          --add-volume-mount="volume=sa-volume,mount-path=/app"
        ```
    Replace `[YOUR_PROJECT_ID]`, `[YOUR_REGION]`, and `[YOUR_FOLDER_ID]`.

3.  **Access the deployed service:**
    Cloud Run will provide a URL for your service. Use this URL to make API requests as shown in the local testing section.

## Contributing

Feel free to fork the repository, make improvements, and submit pull requests.