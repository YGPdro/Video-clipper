import os
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp
from moviepy.editor import VideoFileClip

app = FastAPI(title="Video Clipper API")

DOWNLOAD_DIR = "downloads"
OUTPUT_DIR = "outputs"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

class ClipRequest(BaseModel):
    url: str
    start_time: float
    end_time: float

@app.post("/clip")
def create_clip(request: ClipRequest):
    if request.start_time >= request.end_time:
        raise HTTPException(status_code=400, detail="start_time must be less than end_time")
    
    unique_id = str(uuid.uuid4())
    raw_video_path = os.path.join(DOWNLOAD_DIR, f"{unique_id}.mp4")
    clipped_video_path = os.path.join(OUTPUT_DIR, f"clip_{unique_id}.mp4")

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': raw_video_path,
        'quiet': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([request.url])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download video: {str(e)}")

    try:
        with VideoFileClip(raw_video_path) as clip:
            subclip = clip.subclip(request.start_time, min(request.end_time, clip.duration))
            subclip.write_videofile(clipped_video_path, codec="libx264", audio_codec="aac")
    except Exception as e:
        if os.path.exists(raw_video_path):
            os.remove(raw_video_path)
        raise HTTPException(status_code=500, detail=f"Failed to process clip: {str(e)}")

    if os.path.exists(raw_video_path):
        os.remove(raw_video_path)

    return FileResponse(
        path=clipped_video_path, 
        media_type="video/mp4", 
        filename=f"clip_{unique_id}.mp4"
    )
