def generate_sent_analysis_prompt(transcript:str)->str:
    """
    Generate the prompt for the analysis of the transcript
    """

    prompt = f"""
You are an assistant designed to process speech transcripts.

This is transcript of raw  recorded video with timestamps. As speaker might not go through whole script in a single go. They will repeat same sentence if they are not satisfied with their previous sentence.
Your task is to identify such case and mark all repeated segments as 'repetition' except last one.

### Rules:
1. Only the **last occurrence** of a repeated sentence or meaningfully similar sentence is considered valid.
2. All **previous occurrences** (spoken before the last one) are marked as `"repetition"`.
3. Start analysis from starting in chronological order.

Your job is to return a JSON array, where each element is an object with the following keys:
- `"startTime"`: Timestamp in format `SS.sss`
- `"endTime"`: Timestamp in format `SS.sss`
- `"type"`: Always `"repetition"`
- `"isEntire"`: true if the whole segment is a repetition, false if only part of it is

### Input Transcript:
Format: start_time end_time text
{transcript}

### Example output:
{{
    "data": [
        {{
            "startTime": "2.32",
            "endTime": "2.50",
            "type": "repetition",
            "isEntire": true
        }}
    ]
}}

Only return the JSON and strictly follow the format.
"""

    return prompt