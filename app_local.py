import os
import argparse

from fastapi import BackgroundTasks, FastAPI
from src.api.transcript import _fetch_transcript
from src.api.invalids import _fetch_invalid_segments, _override_invalid
from src.api.process_all import _process_all
from src.api.status import _get_status
from src.api.transcribe import _transcribe_video
from src.api.trim import _trim
from src.api.upload_file import _upload_file
from src.models.invalid_model import InvalidModel
from src.models.metadata_model import MetadataModel
from src.models.response_model import ResponseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()


app = FastAPI(title="AI Video Editor API", 
        description="API for automatically trimming videos based on content analysis")

        # Add CORS middleware to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Video Editor API"}

@app.post("/upload")
def upload_file(file_path: str):
    print("we got")
    print("[DEBUG] Uploading file:", file_path)
    return _upload_file(file_path)

@app.post("/process_all", response_model=ResponseModel)
async def process_all(job_id:str, background_tasks:BackgroundTasks):
    return _process_all(job_id, background_tasks)

@app.get("/status/{job_id}", response_model=ResponseModel)
async def get_status(job_id: str):
    return await _get_status(job_id)

@app.post("/trim", response_model=ResponseModel)
async def trim(job_id: str, background_tasks: BackgroundTasks):
    return _trim(job_id, background_tasks)

@app.post("/transcribe", response_model=ResponseModel)
async def transcribe_video(job_id:str, background_tasks: BackgroundTasks):
    return _transcribe_video(job_id, background_tasks)

@app.get("/transcript/{job_id}", response_model=ResponseModel)
def get_transcript(job_id: str):
    return _fetch_transcript(job_id)

@app.get("/invalids/{job_id}", response_model=ResponseModel)
def get_invalids(job_id:str):
    return _fetch_invalid_segments(job_id)

@app.post("/override_invalids/{job_id}", response_model=ResponseModel)
def override_invalids(job_id:str, invalids: list[InvalidModel]):
    return _override_invalid(job_id, invalids)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app_local:app", host="0.0.0.0", port=8000, reload=True)