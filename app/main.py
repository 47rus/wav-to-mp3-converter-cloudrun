from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydub import AudioSegment
import os
import shutil

app = FastAPI()

# Mount static files to serve the HTML frontend
app.mount("/static", StaticFiles(directory="app/static"), name="static")

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

        # Convert WAV to MP3 using pydub
        audio = AudioSegment.from_wav(file_path)
        audio.export(converted_file_path, format="mp3")

        # Return the converted MP3 file
        return FileResponse(path=converted_file_path, media_type="audio/mpeg", filename=converted_file_name)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {e}")
    finally:
        # Clean up temporary files
        if os.path.exists(file_path):
            os.remove(file_path)
        # The converted file is returned, so we don't remove it immediately
        # It will be handled by the client or a separate cleanup process if needed

@app.get("/")
async def read_root(request: Request):
    with open("app/static/index.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)
