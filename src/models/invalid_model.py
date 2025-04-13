from pydantic import BaseModel
from typing import Optional, Literal

class InvalidModel(BaseModel):
    start_time: float = 0.48
    end_time: float = 7.12
    type: Literal["repetition", "filler_word", "long_pause"] = "repetition"
    is_entire: bool = True
    
    def to_dict(self):
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data):
        data['start_time'] = float(data['start_time']) - 0.09
        data['end_time'] = float(data['end_time'])
        data['is_entire'] = data.get('is_entire', True)
        return cls(**data)
