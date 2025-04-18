
import json
import os
from pydantic import BaseModel
from src.utils.constants import TEMP_DIR
from src.utils.enums import ProjectStatus


class MetadataModel(BaseModel):
    input_path: str
    job_id: str
    file_extension: str
    output_name: str = "output"
    status:ProjectStatus = ProjectStatus.CREATED

    def to_dict(self):
        return self.model_dump()

    def save_metadata(self):
        try:
            if self.job_id is None:
                raise ValueError("job_id is not set")

            project_dir = os.path.join(TEMP_DIR, self.job_id)
            os.makedirs(project_dir, exist_ok=True)
            meta_path = os.path.join(project_dir, "metadata.json")
            with open(meta_path, "w") as f:
                json.dump(self.to_dict(), f)

            print("Metadata saved successfully.")
        except Exception as e:
            raise Exception(f"Failed to save metadata: {str(e)}")

    @classmethod
    def load_metadata(self, job_id: str):
        try:
            project_dir = os.path.join(TEMP_DIR, str(job_id))
            meta_path = os.path.join(project_dir, "metadata.json")
            if os.path.exists(meta_path):
                with open(meta_path, "r") as f:
                    data = json.load(f)
                    return self.from_dict(data)
            else:
                raise FileNotFoundError(f"Metadata file not found for job_id {job_id}")
        except Exception as e:
            raise Exception(f"Failed to load metadata: {str(e)}")


# test

if __name__ == "__main__":
    meta = MetadataModel(
        input_path="test.mp4",
        job_id="12345",
        file_extension=".mp4"
    )

    meta.save_metadata()