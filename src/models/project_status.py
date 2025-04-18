from enum import Enum

class ProjectStatus(str, Enum):
    CREATED = ('created', 1)
    UPLOADED = ('uploaded', 2)
    TRANSCRIPT_START = ('transcript_start', 3)
    TRANSCRIPT_COMPLETE = ('transcript_complete', 4)
    SENT_ANALYSIS_START = ('sent_analysis_start', 5)
    SENT_ANALYSIS_END = ('sent_analysis_end', 6)
    WORD_ANALYSIS_START = ('word_analysis_start', 7)
    WORD_ANALYSIS_END = ('word_analysis_end', 8)
    PROCESSED_INVALID_SEGMENT = ('processed_invalid_segment', 9) 
    TRIM_START = ('trim_start', 10)
    COMPLETED = ('completed', 11)
    
    def __new__(cls, value, order):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.order = order
        return obj

    @classmethod
    def from_string(cls, status_str):
        """Convert string to enum value"""
        for status in cls:
            if status.value == status_str:
                return status
        raise ValueError(f"No matching status for: {status_str}")

    def to_string(self):
        """Convert enum value to string"""
        return self.value
    
    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.order < other.order
        return NotImplemented
    
    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.order <= other.order
        return NotImplemented
    
    def __ge__(self, value):
        if self.__class__ is value.__class__:
            return self.order >= value.order
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.order > other.order
        return NotImplemented
    

# Test the ProjectStatus enum
if __name__ == "__main__":

    # test status comparison for all possible combinations
    statuses = list(ProjectStatus)
    for i in range(len(statuses)):
        for j in range(len(statuses)):
            if i != j:
                assert statuses[i] < statuses[j] or statuses[i] > statuses[j], f"Comparison failed for {statuses[i]} and {statuses[j]}"
    print("All status comparisons are valid.")
    
    # test status conversion from string to enum
    status_str = "transcript_complete"
    status_enum = ProjectStatus.from_string(status_str)
    print(f"Converted string '{status_str}' to enum: {status_enum}")