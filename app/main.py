from typing import Optional

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