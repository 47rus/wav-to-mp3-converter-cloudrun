# WAV to MP3 Converter for Cloud Run

## Overview

This project provides a simple web application to convert WAV audio files to MP3 format. The backend is built with FastAPI, and the frontend is a basic HTML page with Bootstrap CSS. The application is designed to be easily deployable on Google Cloud Run using Docker.

## Features

-   Upload WAV files via a web interface.
-   Convert uploaded WAV files to MP3 format.
-   Download the converted MP3 files.
-   Containerized with Docker for easy deployment.

## Project Structure

```
.
├── app/
│   ├── static/
│   │   └── index.html
│   └── main.py
├── Dockerfile
└── requirements.txt
```

-   `app/main.py`: The FastAPI application that handles file uploads, conversion, and serves the frontend.
-   `app/static/index.html`: The HTML frontend for user interaction.
-   `Dockerfile`: Defines the Docker image for the application.
-   `requirements.txt`: Lists the Python dependencies.

## Local Development

### Prerequisites

-   Python 3.9+
-   `pip` (Python package installer)
-   `ffmpeg` (for audio conversion, install via your system's package manager, e.g., `sudo apt-get install ffmpeg` on Debian/Ubuntu or `brew install ffmpeg` on macOS)

### Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/47rus/wav-to-mp3-converter-cloudrun.git
    cd wav-to-mp3-converter-cloudrun
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application:**
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8000
    ```

    The application will be accessible at `http://localhost:8000`.

## Deployment to Google Cloud Run

### Prerequisites

-   Google Cloud SDK installed and configured.
-   A Google Cloud project with Cloud Run API enabled.

### Steps

1.  **Build the Docker image:**
    ```bash
    gcloud builds submit --tag gcr.io/<YOUR_PROJECT_ID>/wav-to-mp3-converter
    ```
    Replace `<YOUR_PROJECT_ID>` with your actual Google Cloud Project ID.

2.  **Deploy to Cloud Run:**
    ```bash
    gcloud run deploy wav-to-mp3-converter --image gcr.io/<YOUR_PROJECT_ID>/wav-to-mp3-converter --platform managed --region <YOUR_REGION> --allow-unauthenticated
    ```
    Replace `<YOUR_PROJECT_ID>` and `<YOUR_REGION>` (e.g., `us-central1`). The `--allow-unauthenticated` flag makes the service publicly accessible. Adjust as needed for your security requirements.

3.  **Access the deployed service:**
    After deployment, Cloud Run will provide a URL for your service. Navigate to this URL in your browser to use the converter.

## Usage

1.  Open the application in your web browser.
2.  Click "Choose File" and select a `.wav` file from your computer.
3.  Click "Convert to MP3".
4.  Once the conversion is complete, a "Download MP3" button will appear. Click it to download your converted file.

## Contributing

Feel free to fork the repository, make improvements, and submit pull requests.