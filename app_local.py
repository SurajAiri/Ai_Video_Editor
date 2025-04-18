import os
import argparse

from fastapi import BackgroundTasks, FastAPI
from src.api.process_all import _process_all
from src.api.status import _get_status
from src.api.transcribe import _transcribe_video
from src.api.trim import _trim
from src.api.upload_file import _upload_file
from src.models.metadata_model import MetadataModel
from src.models.response_model import ResponseModel
from dotenv import load_dotenv

load_dotenv()


app = FastAPI(title="AI Video Editor API", 
        description="API for automatically trimming videos based on content analysis")


@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Video Editor API"}

@app.post("/upload", response_model=ResponseModel)
def upload_file(file_path: str):
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




if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app_local:app", host="0.0.0.0", port=8000, reload=True)