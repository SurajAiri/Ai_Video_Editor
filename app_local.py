import os
import argparse

from fastapi import FastAPI
from src.models.invalid_model import InvalidModel
from pydantic import BaseModel
from src.llm.llm import llm_call_analyse_sent, llm_call_analyse_word
from src.models.invalid_model import InvalidModel
from src.models.metadata_model import MetadataModel
from src.transcribe.deepgram_transcriber import deepgram_transcribe
from src.utils.constants import TEMP_DIR
from src.utils.enums import ProjectStatus
from src.utils.json_parser import llm_json_parser
from src.utils.transcript_format import format_deepgram_transcript_sent, format_deepgram_transcript_word
from src.utils.video_trimmer import trim_video as video_trimmer
from dotenv import load_dotenv
from uuid import uuid4
from pathlib import Path
import json

load_dotenv()


app = FastAPI(title="AI Video Editor API", 
        description="API for automatically trimming videos based on content analysis")


class ResponseModel(BaseModel):
    status: str
    message: str
    job_id: str
    project_status: str | None
    data: dict | None


@app.post("/upload", response_model=ResponseModel)
def upload_file(file_path: str):
    try:
        # Check if the file exists
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File {file_path} does not exist.")
        # Check if the file is a video
        if not file_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            raise ValueError("File is not a valid video format.")

        job_id = str(uuid4())
        file_extension = os.path.splitext(file_path)[1]
        input_path = os.path.abspath(file_path)
        # output_name = os.path.splitext(os.path.basename(file_path))[0]

        meta = MetadataModel(
            input_path=input_path,
            job_id=job_id,
            file_extension=file_extension,
            status=ProjectStatus.UPLOADED
        )
        # Save metadata to a file or database
        meta.save_metadata()
        
        return ResponseModel(
            status="success",
            message="File uploaded successfully",
            job_id=meta.job_id,
            # data=meta.to_dict()
            project_status=meta.status.to_string(),
            data=None
        )
    
    except Exception as e:
        return ResponseModel(
            status="error",
            message=f"Error uploading file: {str(e)}",
            job_id="",
            project_status=None,
            data=None
        )

@app.post("/process_video", response_model=ResponseModel)
def process_video(job_id:str):
    try:
        meta = MetadataModel.load_metadata(job_id)
        if not meta:
            raise ValueError("Metadata not found for the given job_id.")
        

    except Exception as e:
        return ResponseModel(
            status="error",
            message=f"Error processing video: {str(e)}",
            job_id=job_id,
            project_status="failed",
            data=None
        )