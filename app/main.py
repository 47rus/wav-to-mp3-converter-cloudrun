from fastapi import FastAPI, UploadFile, File, HTTPException
from pydub import AudioSegment
import os
import shutil
import google.auth
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

import logging



app = FastAPI()



# Application is API-only, no static files are served.



# --- Google Drive Configuration ---
# The application uses the runtime service account's Application Default Credentials
# to authenticate with the Google Drive API. Ensure the Cloud Run service's
# service account has the "Editor" role on the target Google Drive folder.
#
# The ID of the Google Drive folder where the files will be uploaded should be
# set as an environment variable named 'FOLDER_ID'.

SCOPES = ['https://www.googleapis.com/auth/drive.file']
FOLDER_ID = os.environ.get('FOLDER_ID')

def get_drive_service():
    """Authenticates with the Google Drive API using Application Default
    Credentials and returns a service object."""
    creds, _ = google.auth.default(scopes=SCOPES)
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
                                    fields='id',
                                    supportsAllDrives=True).execute()
    file_id = file.get('id')

    # Make the file publicly readable
    permission = {'type': 'anyone', 'role': 'reader'}
    service.permissions().create(fileId=file_id,
                                 body=permission,
                                 supportsAllDrives=True).execute()

    # Get the file's metadata again to retrieve the downloadable link
    file_metadata = service.files().get(fileId=file_id,
                                        fields='webContentLink',
                                        supportsAllDrives=True).execute()
    return file_metadata.get('webContentLink')


import tempfile

@app.post("/convert/")
async def convert_wav_to_mp3(file: UploadFile = File(...)):
    if not file.filename.endswith(".wav"):
        raise HTTPException(status_code=400, detail="Only .wav files are supported")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, file.filename)
            converted_file_name = file.filename.replace(".wav", ".mp3")
            converted_file_path = os.path.join(temp_dir, converted_file_name)

            # Save the uploaded WAV file temporarily
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Convert WAV to MP3 using pydub, optimized for voice transcription
            audio = AudioSegment.from_wav(file_path)
            audio = audio.set_channels(1)  # Convert to mono
            audio = audio.set_frame_rate(16000)  # Set sample rate to 16kHz
            audio.export(converted_file_path, format="mp3", bitrate="64k")

            # Upload the converted file to Google Drive
            download_link = upload_to_drive(converted_file_path, converted_file_name)

            return {"filename": converted_file_name, "download_link": download_link}

    except Exception as e:
        logging.exception("An error occurred during file conversion and upload.")
        raise HTTPException(status_code=500, detail=f"Conversion failed: {e}")
