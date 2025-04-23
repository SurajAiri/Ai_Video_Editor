
import json
import os

from fastapi import BackgroundTasks
from src.models.invalid_model import InvalidModel
from src.models.metadata_model import MetadataModel
from src.models.project_status import ProjectStatus
from src.models.response_model import ResponseModel
from src.utils.video_trimmer import trim_video as video_trimmer
from src.utils.constants import TEMP_DIR


def _trim_video(meta: MetadataModel):
    if meta.is_processing:
        raise ValueError("Processing is already in progress.")
    try:
        meta.status = ProjectStatus.TRIM_START
        meta.is_processing = True
        meta.save_metadata()

        # Load invalid segments
        all_invalids_path = os.path.join(TEMP_DIR, meta.job_id, "all_invalids.json")
        with open(all_invalids_path, "r") as f:
            invalids = json.load(f)
            invalids = [InvalidModel.from_dict(item) for item in invalids['data']]
            invalids.sort(key=lambda x: x.start_time)

        # Trim the video
        output_path = os.path.join(TEMP_DIR, meta.job_id, "trimmed_video"+meta.file_extension)
        if not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path))
        if not invalids:
            raise ValueError("No invalid segments found for trimming.")
        if not meta.input_path or not os.path.isfile(meta.input_path):
            raise ValueError("File not found.")
        video_trimmer(meta.input_path, invalids, output_path)

        # Update metadata
        meta.status = ProjectStatus.COMPLETED
        meta.is_processing = False
        meta.save_metadata()

    except Exception as e:
        print(f"[DEBUG] Error during video trimming: {str(e)}")
        meta.is_processing = False
        meta.status = ProjectStatus.PROCESSED_INVALID_SEGMENT
        meta.save_metadata()
        raise e
    

async def _trim(job_id: str, background_tasks: BackgroundTasks):
    try:
        meta = MetadataModel.load_metadata(job_id)
        if not meta:
            raise ValueError("Metadata not found for the given job_id.")

        if meta.is_processing:
            raise ValueError("Processing is already in progress.")

        if meta.status != ProjectStatus.PROCESSED_INVALID_SEGMENT:
            raise ValueError("Project status is not valid for trimming.")

        # Start the trimming process    
        background_tasks.add_task(_trim_video, meta)

        return ResponseModel(
            status="success",
            message="Trimming started successfully",
            job_id=job_id,
            project_status=meta.status.to_string(),
            data=None
        )
    except Exception as e:
        return ResponseModel(
            status="error",
            message=f"Error trimming video: {str(e)}",
            job_id=job_id,
            project_status="failed",
            data=None
        )
    