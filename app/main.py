from fastapi import FastAPI, UploadFile, File, HTTPException
from pydub import AudioSegment
import os
import shutil
import google.auth
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import logging
import tempfile
from typing import Optional

app = FastAPI()

# --- Google Drive Configuration ---
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

@app.post("/convert/")
async def convert_wav_to_mp3(
    file: UploadFile = File(...),
    chunk_length_sec: Optional[int] = None,
    overlap_sec: int = 0  # New parameter defaulting to 0 seconds
):
    if not file.filename.endswith(".wav"):
        raise HTTPException(status_code=400, detail="Only .wav files are supported")

    # Prevent infinite loops if user sets overlap >= chunk length
    if chunk_length_sec and overlap_sec >= chunk_length_sec:
        raise HTTPException(status_code=400, detail="Overlap must be less than chunk length")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, file.filename)
            base_name = file.filename.replace(".wav", "")
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            audio = AudioSegment.from_wav(file_path)
            audio = audio.set_channels(1) 
            audio = audio.set_frame_rate(16000)

            results = []

            # If chunking is requested
            if chunk_length_sec and chunk_length_sec > 0:
                chunk_length_ms = chunk_length_sec * 1000
                overlap_ms = overlap_sec * 1000
                step_ms = chunk_length_ms - overlap_ms # This dictates how far we move forward each loop
                
                start_time = 0
                part_number = 1
                
                # Use a while loop to slide the window across the audio
                while start_time < len(audio):
                    end_time = start_time + chunk_length_ms
                    audio_chunk = audio[start_time:end_time]
                    
                    chunk_name = f"{base_name}_part{part_number}.mp3"
                    chunk_path = os.path.join(temp_dir, chunk_name)
                    
                    audio_chunk.export(chunk_path, format="mp3", bitrate="64k")
                    download_link = upload_to_drive(chunk_path, chunk_name)
                    
                    results.append({"filename": chunk_name, "download_link": download_link})
                    
                    start_time += step_ms
                    part_number += 1
            
            # If no chunk length is provided, process whole file
            else:
                converted_file_name = f"{base_name}.mp3"
                converted_file_path = os.path.join(temp_dir, converted_file_name)
                
                audio.export(converted_file_path, format="mp3", bitrate="64k")
                download_link = upload_to_drive(converted_file_path, converted_file_name)
                
                results.append({"filename": converted_file_name, "download_link": download_link})

            return {"processed_files": results}

    except Exception as e:
        logging.exception("An error occurred during file conversion and upload.")
        raise HTTPException(status_code=500, detail=f"Conversion failed: {e}")