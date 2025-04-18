import os
import argparse

from fastapi import BackgroundTasks, FastAPI
from src.models.invalid_model import InvalidModel
from pydantic import BaseModel
from src.llm.llm import llm_call_analyse_sent, llm_call_analyse_word
from src.models.invalid_model import InvalidModel
from src.models.metadata_model import MetadataModel
from src.transcribe.deepgram_transcriber import deepgram_transcribe
from src.utils.constants import TEMP_DIR
from src.models.project_status import ProjectStatus
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


@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Video Editor API"}

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
    

def process_transcription(meta: MetadataModel):
    if meta.is_processing:
        raise ValueError("Processing is already in progress.")
    try:
        meta.status = ProjectStatus.TRANSCRIPT_START
        meta.is_processing = True
        meta.save_metadata()

        # Transcribe the video
        transcription = deepgram_transcribe(meta.input_path)
        if not transcription:
            raise ValueError("Transcription failed.")
        
        # Save the transcription to a file
        transcript_path = os.path.join(TEMP_DIR, meta.job_id, "transcript.json")
        with open(transcript_path, "w") as f:
            f.write(transcription)

        # update metadata
        meta.status = ProjectStatus.TRANSCRIPT_COMPLETE
        meta.is_processing = False
        meta.save_metadata()

    except Exception as e:
        meta.status = ProjectStatus.PROCESS_INVALID
        meta.save_metadata()
        raise e
    
def process_together(meta: MetadataModel, is_debug=False):
    if meta.is_processing:
        raise ValueError("Processing is already in progress.")
    try:
        print(f"[DEBUG] Starting processing for job {meta.job_id}")
        meta.status = ProjectStatus.TRANSCRIPT_START
        meta.is_processing = True
        meta.save_metadata()

        # Transcribe the video
        print(f"[DEBUG] Starting video transcription")
        transcription = deepgram_transcribe(meta.input_path)
        if not transcription:
            raise ValueError("No transcription data received.")
        
        # Save the transcription to a file
        transcript_path = os.path.join(TEMP_DIR, meta.job_id, "transcript.json")
        with open(transcript_path, "w") as f:
            f.write(transcription)

        # update metadata
        meta.status = ProjectStatus.TRANSCRIPT_COMPLETE
        meta.is_processing = False
        meta.save_metadata()
        print(f"[DEBUG] Transcription completed successfully")
        
        with open(transcript_path, "r") as f:
            transcription = json.load(f)
        transcription_sent = format_deepgram_transcript_sent(transcription)

        # Perform sentence analysis
        print(f"[DEBUG] Starting sentence analysis")
        meta.status = ProjectStatus.SENT_ANALYSIS_START
        meta.save_metadata()
        analysis_sent = llm_call_analyse_sent(transcription_sent)
        analysis_sent = llm_json_parser(analysis_sent)
        if not analysis_sent or analysis_sent == {}:
            raise ValueError("Sentence analysis failed.")
        
        # Save the sentence analysis to a file
        analysis_sent_path = os.path.join(TEMP_DIR, meta.job_id, "analysis_sent.json")
        with open(analysis_sent_path, "w") as f:
            json.dump(analysis_sent, f)
        
        # completed sentence analysis
        meta.status = ProjectStatus.SENT_ANALYSIS_END
        meta.save_metadata()
        print(f"[DEBUG] Sentence analysis completed successfully")

        # Process invalids from sentence analysis
        invalids = [InvalidModel.from_dict(item) for item in analysis_sent['data']]
        invalids.sort(key=lambda x: x.start_time)
        print(f"[DEBUG] Found {len(invalids)} invalid segments from sentence analysis")

        # Perform word analysis
        print(f"[DEBUG] Starting word analysis")
        meta.status = ProjectStatus.WORD_ANALYSIS_START
        meta.save_metadata()

        # word analysis
        transcription_word = format_deepgram_transcript_word(transcription, invalids)
        analysis_word = llm_call_analyse_word(transcription_word)
        analysis_word = llm_json_parser(analysis_word)
        if not analysis_word or analysis_word == {}:
            raise ValueError("Word analysis failed.")
        
        # Save the word analysis to a file
        analysis_word_path = os.path.join(TEMP_DIR, meta.job_id, "analysis_word.json")
        with open(analysis_word_path, "w") as f:
            json.dump(analysis_word, f)

        # completed word analysis
        meta.status = ProjectStatus.WORD_ANALYSIS_END
        meta.save_metadata()
        print(f"[DEBUG] Word analysis completed successfully")

        # Prepare invalids for trimming
        invalids_entire = [item for item in invalids if item.is_entire]
        invalids_word = [InvalidModel.from_dict(item) for item in analysis_word['data']]
        invalids_word.sort(key=lambda x: x.start_time)
        print(f"[DEBUG] Found {len(invalids_entire)} entire segments and {len(invalids_word)} word segments to remove")

        # Merge invalids
        all_invalids = invalids_entire + invalids_word
        all_invalids.sort(key=lambda x: x.start_time)
        # Save the merged invalids to a file
        all_invalids_path = os.path.join(TEMP_DIR, meta.job_id, "all_invalids.json")
        with open(all_invalids_path, "w") as f:
            res = {"data": [item.to_dict() for item in all_invalids]}
            json.dump(res, f)
        meta.status = ProjectStatus.PROCESS_INVALID
        meta.is_processing = False
        meta.save_metadata()
        print(f"[DEBUG] Processing completed successfully for job {meta.job_id}")
        
    except Exception as e:
        print(f"[DEBUG] Error during processing: {str(e)}")
        meta.is_processing = False
        meta.save_metadata()
        raise e

@app.post("/process_all", response_model=ResponseModel)
async def process_all(job_id:str, background_tasks:BackgroundTasks):
    try:
        print(f"[DEBUG] Received process_all request for job_id: {job_id}")
        meta = MetadataModel.load_metadata(job_id)
        if not meta:
            raise ValueError("Metadata not found for the given job_id.")

        if meta.is_processing:
            raise ValueError("Processing is already in progress.")

        if meta.status >= ProjectStatus.PROCESS_INVALID:
            raise ValueError("Video has already been processed.")
        if meta.status != ProjectStatus.UPLOADED:
            raise ValueError("Project status is not valid for processing.")

        # Start the transcription process    
        print(f"[DEBUG] Starting background task for job_id: {job_id}")
        background_tasks.add_task(process_together, meta)

        return ResponseModel(
            status="success",
            message="Processing started successfully",
            job_id=job_id,
            project_status=meta.status.to_string(),
            data=None
        )

    except Exception as e:
        print(f"[DEBUG] Error in process_all endpoint: {str(e)}")
        return ResponseModel(
            status="error",
            message=f"Error processing video: {str(e)}",
            job_id=job_id,
            project_status="failed",
            data=None
        )


@app.post("/transcribe", response_model=ResponseModel)
async def transcribe_video(job_id:str, background_tasks: BackgroundTasks):
    try:
        meta = MetadataModel.load_metadata(job_id)
        if not meta:
            raise ValueError("Metadata not found for the given job_id.")

        if meta.status != ProjectStatus.UPLOADED:
            raise ValueError("Project status is not valid for processing.")

        # Start the transcription process    
        background_tasks.add_task(process_transcription, meta)

        return ResponseModel(
            status="success",
            message="Transcription started successfully",
            job_id=job_id,
            project_status=meta.status.to_string(),
            data=None
        )

    except Exception as e:
        return ResponseModel(
            status="error",
            message=f"Error processing video: {str(e)}",
            job_id=job_id,
            project_status="failed",
            data=None
        )
    


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)