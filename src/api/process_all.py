
import json
import os

from fastapi import BackgroundTasks
from src.llm.llm import llm_call_analyse_sent, llm_call_analyse_word
from src.models.invalid_model import InvalidModel
from src.models.metadata_model import MetadataModel
from src.models.project_status import ProjectStatus
from src.models.response_model import ResponseModel
from src.transcribe.deepgram_transcriber import deepgram_transcribe
from src.utils.constants import TEMP_DIR
from src.utils.json_parser import llm_json_parser
from src.utils.transcript_format import dummy_word_transcript, format_deepgram_transcript_sent, format_deepgram_transcript_word
import time
import random


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
        meta.status = ProjectStatus.PROCESSED_INVALID_SEGMENT
        meta.is_processing = False
        meta.save_metadata()
        print(f"[DEBUG] Processing completed successfully for job {meta.job_id}")
        
    except Exception as e:
        print(f"[DEBUG] Error during processing: {str(e)}")
        meta.is_processing = False
        meta.save_metadata()
        raise e

def dummy_process_together(meta: MetadataModel):
    """
    A dummy implementation of process_together that simulates the processing flow
    by changing the status every second until completion.
    """
    if meta.is_processing:
        raise ValueError("Processing is already in progress.")
    
    try:
        print(f"[DEBUG] Starting dummy processing for job {meta.job_id}")
        meta.is_processing = True
        meta.save_metadata()
        
        # Create necessary directories
        job_dir = os.path.join(TEMP_DIR, meta.job_id)
        os.makedirs(job_dir, exist_ok=True)
        
        # Simulate the processing steps with delays
        statuses = [
            ProjectStatus.TRANSCRIPT_START,
            ProjectStatus.TRANSCRIPT_COMPLETE,
            ProjectStatus.SENT_ANALYSIS_START,
            ProjectStatus.SENT_ANALYSIS_END,
            ProjectStatus.WORD_ANALYSIS_START,
            ProjectStatus.WORD_ANALYSIS_END,
            ProjectStatus.PROCESSED_INVALID_SEGMENT
        ]
        
        for status in statuses:
            meta.status = status
            meta.save_metadata()
            print(f"[DEBUG] Status changed to {status.to_string()} for job {meta.job_id}")
            
            # Create dummy files for each step
            if status == ProjectStatus.TRANSCRIPT_COMPLETE:
                with open(os.path.join(job_dir, "transcript.json"), "w") as f:
                    json.dump(dummy_word_transcript(), f)
            elif status == ProjectStatus.SENT_ANALYSIS_END:
                dummy_analysis = {"data": [{"start_time": i, "end_time": i+1, "text": f"Sample text {i}", "is_entire": random.choice([True, False])} for i in range(5)]}
                with open(os.path.join(job_dir, "analysis_sent.json"), "w") as f:
                    json.dump(dummy_analysis, f)
            elif status == ProjectStatus.WORD_ANALYSIS_END:
                dummy_word_analysis = {"data": [{"start_time": i+0.2, "end_time": i+0.3, "text": f"word {i}", "is_entire": False} for i in range(10)]}
                with open(os.path.join(job_dir, "analysis_word.json"), "w") as f:
                    json.dump(dummy_word_analysis, f)
            elif status == ProjectStatus.PROCESSED_INVALID_SEGMENT:
                all_invalids = {"data": [InvalidModel().to_dict() for i in range(2)]}
                with open(os.path.join(job_dir, "all_invalids.json"), "w") as f:
                    json.dump(all_invalids, f)
            
            # Sleep for 1 second to simulate processing time
            time.sleep(1)
        
        meta.is_processing = False
        meta.save_metadata()
        print(f"[DEBUG] Dummy processing completed successfully for job {meta.job_id}")
        
    except Exception as e:
        print(f"[DEBUG] Error during dummy processing: {str(e)}")
        meta.is_processing = False
        meta.save_metadata()
        raise e

async def _process_all(job_id:str, background_tasks:BackgroundTasks):
    try:
        print(f"[DEBUG] Received process_all request for job_id: {job_id}")
        meta = MetadataModel.load_metadata(job_id)
        if not meta:
            raise ValueError("Metadata not found for the given job_id.")

        if meta.is_processing:
            raise ValueError("Processing is already in progress.")

        if meta.status >= ProjectStatus.PROCESSED_INVALID_SEGMENT:
            raise ValueError("Video has already been processed.")
        if meta.status != ProjectStatus.UPLOADED:
            raise ValueError("Project status is not valid for processing.")

        # Start the transcription process    
        print(f"[DEBUG] Starting background task for job_id: {job_id}")
        background_tasks.add_task(dummy_process_together, meta)

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
