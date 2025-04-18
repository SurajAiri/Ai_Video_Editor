
from src.models.metadata_model import MetadataModel
from src.models.response_model import ResponseModel


async def _get_status(job_id: str):
    try:
        meta = MetadataModel.load_metadata(job_id)
        if not meta:
            raise ValueError("Metadata not found for the given job_id.")

        return ResponseModel(
            status="success",
            message="Status retrieved successfully",
            job_id=job_id,
            project_status=meta.status.to_string(),
            data=meta.to_dict()
        )

    except Exception as e:
        return ResponseModel(
            status="error",
            message=f"Error retrieving status: {str(e)}",
            job_id=job_id,
            project_status="failed",
            data=None
        )
    