# app.py
import os
import shutil
import uuid
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.llm.llm import llm_call_analyse_sent, llm_call_analyse_word
from src.models.invalid_model import InvalidModel
from src.transcribe.deepgram_transcriber import deepgram_transcribe
from src.utils.json_parser import llm_json_parser
from src.utils.transcript_format import format_deepgram_transcript_sent, format_deepgram_transcript_word
from src.utils.video_trimmer import trim_video as video_trimmer
from dotenv import load_dotenv
import json


load_dotenv()

app = FastAPI(title="AI Video Editor API", 
              description="API for automatically trimming videos based on content analysis")

# Create temporary directory for file storage
UPLOAD_DIR = "temp/uploads"
RESULTS_DIR = "temp/results"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# Keep track of processed files
processing_tasks = {}

class TranscriptionResponse(BaseModel):
    job_id: str
    transcript_path: str
    message: str

class TranscriptionAnalysisResponse(BaseModel):
    job_id: str
    sent_analysis_path: Optional[str] = None
    word_analysis_path: Optional[str] = None
    message: str

class TrimVideoRequest(BaseModel):
    job_id: str

class TrimVideoResponse(BaseModel):
    job_id: str
    output_path: str
    download_url: str
    message: str

class TaskStatusResponse(BaseModel):
    job_id: str
    status: str
    output_path: Optional[str] = None
    download_url: Optional[str] = None

@app.post("/upload/", response_model=TranscriptionResponse)
async def upload_video(file: UploadFile = File(...)):
    """Upload a video file for processing."""
    job_id = str(uuid.uuid4())
    
    # Create a job directory
    job_dir = os.path.join(RESULTS_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    
    # Save the uploaded file
    file_path = os.path.join(UPLOAD_DIR, f"{job_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Update task status
    processing_tasks[job_id] = {
        "status": "uploaded",
        "input_path": file_path,
        "job_dir": job_dir
    }
    
    return TranscriptionResponse(
        job_id=job_id,
        transcript_path=file_path,
        message=f"Video uploaded successfully. Use this job_id for further processing: {job_id}"
    )

@app.post("/transcribe/{job_id}", response_model=TranscriptionResponse)
async def transcribe_video(job_id: str, background_tasks: BackgroundTasks):
    """Transcribe an uploaded video using Deepgram."""
    if job_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="Job not found")
    
    task_info = processing_tasks[job_id]
    video_path = task_info["input_path"]
    job_dir = task_info["job_dir"]
    
    # Define paths for outputs
    transcript_path = os.path.join(job_dir, "transcript.json")
    
    def process_transcription():
        try:
            # Update status
            processing_tasks[job_id]["status"] = "transcribing"
            
            # Transcribe the video
            transcript = deepgram_transcribe(video_path)
            
            # Save transcript
            with open(transcript_path, "w") as f:
                f.write(transcript)
            
            # Update status
            processing_tasks[job_id]["status"] = "transcribed"
            processing_tasks[job_id]["transcript_path"] = transcript_path
        except Exception as e:
            processing_tasks[job_id]["status"] = "failed"
            processing_tasks[job_id]["error"] = str(e)
    
    # Run transcription in the background
    background_tasks.add_task(process_transcription)
    
    return TranscriptionResponse(
        job_id=job_id,
        transcript_path=transcript_path,
        message="Transcription started. Check status with /status/{job_id} endpoint."
    )

@app.post("/analyze/{job_id}", response_model=TranscriptionAnalysisResponse)
async def analyze_transcript(job_id: str, background_tasks: BackgroundTasks):
    """Analyze transcript for content to trim."""
    if job_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="Job not found")
    
    task_info = processing_tasks[job_id]
    
    if task_info["status"] != "transcribed":
        raise HTTPException(status_code=400, detail="Video must be transcribed first")
    
    transcript_path = task_info["transcript_path"]
    job_dir = task_info["job_dir"]
    
    # Define paths for outputs
    sent_analysis_path = os.path.join(job_dir, "sent_analysis.json")
    word_analysis_path = os.path.join(job_dir, "word_analysis.json")
    
    def process_analysis():
        try:
            # Update status
            processing_tasks[job_id]["status"] = "analyzing"
            
            # Load transcript
            with open(transcript_path, "r") as f:
                transcript = f.read()
            
            # Parse transcript
            transcript_json = llm_json_parser(transcript)
            
            # Sentence analysis
            formatted_sent = format_deepgram_transcript_sent(transcript_json)
            sent_response = llm_call_analyse_sent(formatted_sent)
            sent_response_json = llm_json_parser(sent_response)
            
            # Save sentence analysis
            with open(sent_analysis_path, "w") as f:
                json.dump(sent_response_json, f, indent=2)
            
            # Process invalids from sentence analysis
            invalids = [InvalidModel.from_dict(item) for item in sent_response_json['data']]
            invalids.sort(key=lambda x: x.start_time)
            
            # Word analysis
            word_inv = format_deepgram_transcript_word(transcript_json, invalids)
            word_response = llm_call_analyse_word(word_inv)
            word_response_json = llm_json_parser(word_response)
            
            # Save word analysis
            with open(word_analysis_path, "w") as f:
                json.dump(word_response_json, f, indent=2)
            
            # Update status
            processing_tasks[job_id]["status"] = "analyzed"
            processing_tasks[job_id]["sent_analysis_path"] = sent_analysis_path
            processing_tasks[job_id]["word_analysis_path"] = word_analysis_path
            
            # Prepare invalids for trimming
            invalids_entire = [item for item in invalids if item.is_entire]
            invalids_word = [InvalidModel.from_dict(item) for item in word_response_json['data']]
            invalids_word.sort(key=lambda x: x.start_time)
            
            # Merge invalids
            all_invalids = invalids_entire + invalids_word
            processing_tasks[job_id]["invalids"] = all_invalids
            
        except Exception as e:
            processing_tasks[job_id]["status"] = "failed"
            processing_tasks[job_id]["error"] = str(e)
    
    # Run analysis in the background
    background_tasks.add_task(process_analysis)
    
    return TranscriptionAnalysisResponse(
        job_id=job_id,
        sent_analysis_path=sent_analysis_path,
        word_analysis_path=word_analysis_path,
        message="Analysis started. Check status with /status/{job_id} endpoint."
    )

@app.post("/trim/{job_id}", response_model=TrimVideoResponse)
async def trim_video(job_id: str, background_tasks: BackgroundTasks, output_filename: str = Query(None)):
    """Trim video based on analysis results."""
    if job_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="Job not found")
    
    task_info = processing_tasks[job_id]
    
    if task_info["status"] != "analyzed":
        raise HTTPException(status_code=400, detail="Video must be analyzed first")
    
    video_path = task_info["input_path"]
    job_dir = task_info["job_dir"]
    
    # Set output path
    if output_filename:
        output_path = os.path.join(job_dir, output_filename)
    else:
        input_filename = os.path.basename(video_path)
        output_filename = os.path.splitext(input_filename)[0] + "_trimmed.mp4"
        output_path = os.path.join(job_dir, output_filename)
    
    # Get invalids
    invalids = task_info["invalids"]
    
    def process_trimming():
        try:
            # Update status
            processing_tasks[job_id]["status"] = "trimming"
            
            # Trim video
            video_trimmer(video_path, invalids, output_path)
            
            # Update status
            processing_tasks[job_id]["status"] = "completed"
            processing_tasks[job_id]["output_path"] = output_path
            processing_tasks[job_id]["download_url"] = f"/download/{job_id}"
            
        except Exception as e:
            processing_tasks[job_id]["status"] = "failed"
            processing_tasks[job_id]["error"] = str(e)
    
    # Run trimming in the background
    background_tasks.add_task(process_trimming)
    
    download_url = f"/download/{job_id}"
    
    return TrimVideoResponse(
        job_id=job_id,
        output_path=output_path,
        download_url=download_url,
        message="Trimming started. Check status with /status/{job_id} endpoint."
    )

@app.get("/status/{job_id}", response_model=TaskStatusResponse)
async def check_status(job_id: str):
    """Check the status of a processing job."""
    if job_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="Job not found")
    
    task_info = processing_tasks[job_id]
    
    response = TaskStatusResponse(
        job_id=job_id,
        status=task_info["status"]
    )
    
    if task_info["status"] == "completed":
        response.output_path = task_info["output_path"]
        response.download_url = task_info["download_url"]
    elif task_info["status"] == "failed":
        response.status = f"failed: {task_info.get('error', 'Unknown error')}"
    
    return response

@app.get("/download/{job_id}")
async def download_file(job_id: str):
    """Download the processed video."""
    if job_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="Job not found")
    
    task_info = processing_tasks[job_id]
    
    if task_info["status"] != "completed":
        raise HTTPException(status_code=400, detail="Processing not completed yet")
    
    output_path = task_info["output_path"]
    
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Output file not found")
    
    return FileResponse(
        path=output_path, 
        filename=os.path.basename(output_path),
        media_type="video/mp4"
    )

@app.post("/process/", response_model=TrimVideoResponse)
async def process_all(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Process a video through all steps (upload, transcribe, analyze, trim) in one request."""
    # Upload
    job_id = str(uuid.uuid4())
    job_dir = os.path.join(RESULTS_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    
    file_path = os.path.join(UPLOAD_DIR, f"{job_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    output_filename = os.path.splitext(file.filename)[0] + "_trimmed.mp4"
    output_path = os.path.join(job_dir, output_filename)
    
    processing_tasks[job_id] = {
        "status": "uploaded",
        "input_path": file_path,
        "job_dir": job_dir
    }
    
    def process_complete_flow():
        try:
            # Transcribe
            processing_tasks[job_id]["status"] = "transcribing"
            transcript = deepgram_transcribe(file_path)
            transcript_path = os.path.join(job_dir, "transcript.json")
            with open(transcript_path, "w") as f:
                f.write(transcript)
            processing_tasks[job_id]["transcript_path"] = transcript_path
            processing_tasks[job_id]["status"] = "transcribed"
            
            # Analyze
            processing_tasks[job_id]["status"] = "analyzing"
            transcript_json = llm_json_parser(transcript)
            
            # Sentence analysis
            formatted_sent = format_deepgram_transcript_sent(transcript_json)
            sent_response = llm_call_analyse_sent(formatted_sent)
            sent_response_json = llm_json_parser(sent_response)
            
            sent_analysis_path = os.path.join(job_dir, "sent_analysis.json")
            with open(sent_analysis_path, "w") as f:
                f.write(str(sent_response_json))
            
            # Process invalids from sentence analysis
            invalids = [InvalidModel.from_dict(item) for item in sent_response_json['data']]
            invalids.sort(key=lambda x: x.start_time)
            
            # Word analysis
            word_inv = format_deepgram_transcript_word(transcript_json, invalids)
            word_response = llm_call_analyse_word(word_inv)
            word_response_json = llm_json_parser(word_response)
            
            word_analysis_path = os.path.join(job_dir, "word_analysis.json")
            with open(word_analysis_path, "w") as f:
                f.write(str(word_response_json))
            
            # Prepare invalids for trimming
            invalids_entire = [item for item in invalids if item.is_entire]
            invalids_word = [InvalidModel.from_dict(item) for item in word_response_json['data']]
            invalids_word.sort(key=lambda x: x.start_time)
            
            # Merge invalids
            all_invalids = invalids_entire + invalids_word
            processing_tasks[job_id]["status"] = "analyzed"
            
            # Trim
            processing_tasks[job_id]["status"] = "trimming"
            video_trimmer(file_path, all_invalids, output_path)
            
            # Complete
            processing_tasks[job_id]["status"] = "completed"
            processing_tasks[job_id]["output_path"] = output_path
            processing_tasks[job_id]["download_url"] = f"/download/{job_id}"
            
        except Exception as e:
            processing_tasks[job_id]["status"] = "failed"
            processing_tasks[job_id]["error"] = str(e)
    
    # Run the complete process in the background
    background_tasks.add_task(process_complete_flow)
    
    return TrimVideoResponse(
        job_id=job_id,
        output_path=output_path,
        download_url=f"/download/{job_id}",
        message="Processing started. Check status with /status/{job_id} endpoint."
    )

@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job and its associated files."""
    if job_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="Job not found")
    
    task_info = processing_tasks[job_id]
    
    # Delete input file
    if "input_path" in task_info and os.path.exists(task_info["input_path"]):
        os.remove(task_info["input_path"])
    
    # Delete job directory
    if "job_dir" in task_info and os.path.exists(task_info["job_dir"]):
        shutil.rmtree(task_info["job_dir"])
    
    # Remove from tasks dictionary
    del processing_tasks[job_id]
    
    return {"message": f"Job {job_id} deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)