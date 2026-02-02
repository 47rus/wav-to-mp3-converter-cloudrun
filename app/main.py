from fastapi import FastAPI, UploadFile, File, HTTPException
from pydub import AudioSegment
import os
import shutil
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

app = FastAPI()

# Application is API-only, no static files are served.
# --- Google Drive Configuration ---
# The application uses a service account to authenticate with the Google Drive API.
# The service account credentials should be stored in a file named 'service_account.json'.
# When deploying to Cloud Run, this file should be mounted as a secret.
#
# The ID of the Google Drive folder where the files will be uploaded should be
# set as an environment variable named 'FOLDER_ID'.

SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_FILE = 'service_account.json'
FOLDER_ID = os.environ.get('FOLDER_ID')

def get_drive_service():
    """Authenticates with the Google Drive API and returns a service object."""
    creds = None
    if os.path.exists(SERVICE_ACCOUNT_FILE):
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    else:
        # If the service account file is not found, you can add other
        # authentication methods here, for example, using the gcloud credentials.
        # For this example, we will raise an exception.
        raise FileNotFoundError(f"Service account file not found at {SERVICE_ACCOUNT_FILE}")

    return build('drive', 'v3', credentials=creds)

def upload_to_drive(file_path, file_name):
    """Uploads a file to the specified Google Drive folder and returns a downloadable link."""
    if not FOLDER_ID:
        raise ValueError("The FOLDER_ID environment variable is not set.")

    service = get_drive_service()
    file_metadata = {
        'name': file_name,
        'parents': [FOLDER_ID]
    }
    media = MediaFileUpload(file_path, mimetype='audio/mpeg')
    file = service.files().create(body=file_metadata,
                                    media_body=media,
                                    fields='id').execute()
    file_id = file.get('id')

    # Make the file publicly readable
    permission = {'type': 'anyone', 'role': 'reader'}
    service.permissions().create(fileId=file_id, body=permission).execute()

    # Get the file's metadata again to retrieve the downloadable link
    file_metadata = service.files().get(fileId=file_id, fields='webContentLink').execute()
    return file_metadata.get('webContentLink')


UPLOAD_DIRECTORY = "./temp_uploads"
CONVERTED_DIRECTORY = "./temp_converted"

# Ensure upload and converted directories exist
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
os.makedirs(CONVERTED_DIRECTORY, exist_ok=True)

@app.post("/convert/")
async def convert_wav_to_mp3(file: UploadFile = File(...)):
    if not file.filename.endswith(".wav"):
        raise HTTPException(status_code=400, detail="Only .wav files are supported")

    file_path = os.path.join(UPLOAD_DIRECTORY, file.filename)
    converted_file_name = file.filename.replace(".wav", ".mp3")
    converted_file_path = os.path.join(CONVERTED_DIRECTORY, converted_file_name)

    try:
        # Save the uploaded WAV file temporarily
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Convert WAV to MP3 using pydub, optimized for voice transcription
        audio = AudioSegment.from_wav(file_path)
        audio = audio.set_channels(1) # Convert to mono
        audio = audio.set_frame_rate(16000) # Set sample rate to 16kHz
        audio.export(converted_file_path, format="mp3", bitrate="64k")

        # Upload the converted file to Google Drive
        download_link = upload_to_drive(converted_file_path, converted_file_name)

        return {"filename": converted_file_name, "download_link": download_link}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {e}")
    finally:
        # Clean up temporary files
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(converted_file_path):
            os.remove(converted_file_path)
