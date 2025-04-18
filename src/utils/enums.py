from enum import Enum

class ProjectStatus(str,Enum):
    CREATED = 'created'
    UPLOADED = 'uploaded'
    TRANSCRIPT_START = 'transcript_start'
    TRANSCRIPT_COMPLETE = 'transcript_complete'
    SENT_ANALYSIS_START = 'sent_analysis_start'
    SENT_ANALYSIS_END = 'sent_analysis_end'
    WORD_ANALYSIS_START = 'word_analysis_start'
    WORD_ANALYSIS_END = 'word_analysis_end'
    INVALID = 'invalid'
    UPDATED = 'updated'
    COMPLETED = 'completed'

    @classmethod
    def from_string(cls, status_str):
        """Convert string to enum value"""
        for status in cls:
            if status.value == status_str:
                return status
        raise ValueError(f"No matching status for: {status_str}")

    
    def __str__(self):
        return self.value
    
    def __repr__(self):
        return self.value
        
    def toJSON(self):
        return self.value