
from pydantic import BaseModel


class ResponseModel(BaseModel):
    status: str
    message: str
    job_id: str
    project_status: str | None
    data: dict | None = None
