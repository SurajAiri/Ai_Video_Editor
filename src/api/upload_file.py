import os
from uuid import uuid4

from src.models.metadata_model import MetadataModel
from src.models.project_status import ProjectStatus
from src.models.response_model import ResponseModel
from src.utils.constants import TEMP_DIR


def _already_uploaded(file_path: str) -> MetadataModel | None:
    """
    Check if the file has already uploaded checking all metadata files
    in the sub-directory of TEMP_DIR.
    :param file_path: The path of the file to check.
    :return: job_id if the file has already been uploaded, None otherwise.
    """

    try:

        for dir in os.listdir(TEMP_DIR):
            meta = MetadataModel.load_metadata(dir)
            if meta.input_path == file_path:
                return meta

        return None
    except Exception as e:
        return None


def _upload_file(file_path: str):
    try:
        # Check if the file exists
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File {file_path} does not exist.")
        # Check if the file is a video
        if not file_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            raise ValueError("File is not a valid video format.")

        # Check if the file has already been uploaded
        meta = _already_uploaded(file_path)
        if meta:
            return ResponseModel(
                status="success",
                message="File already uploaded",
                job_id=meta.job_id,
                data=meta.to_dict(),
                project_status=meta.status.to_string(),
            )

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
            data=meta.to_dict(),
            project_status=meta.status.to_string(),
        )
    
    except Exception as e:
        return ResponseModel(
            status="error",
            message=f"Error uploading file: {str(e)}",
            job_id="",
            project_status=None,
            data=None
        )
    
