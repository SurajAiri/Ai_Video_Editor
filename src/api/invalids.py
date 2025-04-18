   
import json
import os
from src.models.invalid_model import InvalidModel
from src.models.metadata_model import MetadataModel
from src.models.project_status import ProjectStatus
from src.models.response_model import ResponseModel
from src.utils.constants import TEMP_DIR


def _fetch_invalid_segments(job_id: str) -> str:
    try:
        # Load metadata
        meta = MetadataModel.load_metadata(job_id)
        if not meta:
            raise ValueError("Metadata not found for the given job_id.")
        
        # Check if the invalid segments are available
        if meta.status < ProjectStatus.PROCESSED_INVALID_SEGMENT:
            raise ValueError("Invalid segments are not available.")
        
        # Fetch the invalid segments
        all_invalids_path = os.path.join(TEMP_DIR, job_id, "all_invalids.json")
        if not os.path.exists(all_invalids_path):
            raise ValueError("Invalid segments file not found.")
        
        with open(all_invalids_path, "r") as f:
            invalids = json.load(f)

        return ResponseModel(
            status="success",
            message="Invalid segments fetched successfully",
            job_id=job_id,
            project_status=meta.status.to_string(),
            data={"invalids": invalids['data']}
        )
    except Exception as e:
        return ResponseModel(
            status="error",
            message=f"Error fetching invalid segments: {str(e)}",
            job_id=job_id,
            project_status="failed",
            data=None
        )
    

def _override_invalid(job_id: str, invalids: list[InvalidModel]) -> str:
    try:
        # Load metadata
        meta = MetadataModel.load_metadata(job_id)
        
        if not meta:
            raise ValueError("Metadata not found for the given job_id.")
        
        meta.is_processing = True
        meta.save_metadata()

        # Check if the invalid segments are available
        if meta.status < ProjectStatus.TRANSCRIPT_COMPLETE:
            raise ValueError("Transcription is not complete.")
        
        # Update the invalid segments
        all_invalids_path = os.path.join(TEMP_DIR, job_id, "all_invalids.json")
        
        # Convert InvalidModel objects to dictionaries
        invalid_dicts = [invalid.to_dict() for invalid in invalids]
        
        with open(all_invalids_path, "w") as f:
            json.dump({"data": invalid_dicts}, f)
        
        # Update metadata
        meta.status = ProjectStatus.PROCESSED_INVALID_SEGMENT
        meta.is_processing = False
        meta.save_metadata()
        
        return ResponseModel(
            status="success",
            message="Invalid segments updated successfully",
            job_id=job_id,
            project_status=meta.status.to_string(),
        )
    except Exception as e:
        return ResponseModel(
            status="error",
            message=f"Error updating invalid segments: {str(e)}",
            job_id=job_id,
            project_status="failed",
            data=None
        )