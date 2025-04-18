
import os
from fastapi import BackgroundTasks
from src.models.metadata_model import MetadataModel
from src.models.project_status import ProjectStatus
from src.models.response_model import ResponseModel
from src.transcribe.deepgram_transcriber import deepgram_transcribe
from src.utils.constants import TEMP_DIR


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
        meta.status = ProjectStatus.PROCESSED_INVALID_SEGMENT
        meta.save_metadata()
        raise e
    

async def _transcribe_video(job_id:str, background_tasks: BackgroundTasks):
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
    
