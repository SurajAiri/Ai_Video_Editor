import json
import os
from src.models.invalid_model import InvalidModel
from src.models.metadata_model import MetadataModel
from src.models.project_status import ProjectStatus
from src.models.response_model import ResponseModel
from src.utils.constants import TEMP_DIR

def format_word_transcript(transcript: dict) -> dict:
    return transcript['results']['channels'][0]['alternatives'][0]['words']

def _fetch_transcript(job_id: str) -> str:
    """
    Fetch the transcript from the given job ID.
    """
    try:
        # Load metadata
        meta = MetadataModel.load_metadata(job_id)
        if not meta:
            raise ValueError("Metadata not found for the given job_id.")
        
        # Check if the transcription is complete
        if meta.status < ProjectStatus.TRANSCRIPT_COMPLETE:
            raise ValueError("Transcription is not complete.")
        
        # Fetch the transcript
        transcript_path = os.path.join(TEMP_DIR, job_id, "transcript.json")
        if not os.path.exists(transcript_path):
            raise ValueError("Transcript file not found.")
        
        with open(transcript_path, "r") as f:
            transcript = json.load(f)

        return ResponseModel(
            status="success",
            message="Transcript fetched successfully",
            job_id=job_id,
            project_status=meta.status.to_string(),
            data={"transcript": format_word_transcript(transcript)}
        )
    except Exception as e:
        return ResponseModel(
            status="error",
            message=f"Error fetching transcript: {str(e)}",
            job_id=job_id,
            project_status="failed",
            data=None
        )
 