def generate_sent_analysis_prompt(transcript:str)->str:
    """
    Generate the prompt for the analysis of the transcript
    """

    prompt = f"""
You are an assistant designed to process speech transcripts from recorded videos with timestamps. Speakers may repeat portions of their script; your task is to identify all repeated segments and mark them as "repetition" except for the very last occurrence. Use the rules below to guide your analysis:

RULES:
1. Process the transcript in chronological order.
2. For any sentence or meaningfully similar sentence that appears multiple times (even with minor modifications), consider only the very last occurrence as valid.
3. Mark every previous occurrence (i.e., every occurrence that comes before the final one) as a repetition.
4. The repetition status can be flagged per sentence or per partial segment within a sentence:
    - If the entire sentence (or meaning) is repeated earlier, mark it as `"isEntire": true`.
    - If only a part of the sentence is repeated and later completed, mark it as `"isEntire": false`.
5. Do NOT alter any original timestamps. Return them exactly as provided.
6. Analysis must consider the context of the transcript, so even if sentences are slightly modified, treat them as the same if their meaning is essentially identical.

INPUT FORMAT:
The transcript will be provided as follows:
Format: start_time end_time text
{transcript} 

OUTPUT FORMAT:
Return a JSON object with a single key "data", which contains an array of objects. Each object should have these keys:
- "startTime": Timestamp (SS.sss)
- "endTime": Timestamp (SS.sss)
- "type": Always "repetition"
- "isEntire": true or false

Only include objects for segments that are repetitions (i.e., all the repeated occurrences except the final instance).

EXAMPLE:

Transcript:
0.32 2.26 hi everyone  
3.4 4.89 hello everyone! Happy to see you all.

Analysis:
- "hi everyone" repeats as part of "hello everyone! Happy to see you all." So the first instance ("hi everyone") is marked as repetition (even though it is shorter, consider it a full repetition if the meaning is repeated).
Output:
{{
    "data": [
        {{
            "startTime": "0.32",
            "endTime": "2.26",
            "type": "repetition",
            "isEntire": true
        }}
    ]
}}

Another Example:
Transcript:
12.32 16.65 you can you can do it. just do it.

Analysis:
- "you can" repeats before being followed by "do it. just do it." only in the beginning.
So the earlier occurrence ("you can") is marked as repetition (with "isEntire": false) and only the final complete sentence is left unmarked.

Final Note:
Always assume that the LAST occurrence in chronological order is the valid, corrected/revised sentence, and mark all previous occurrences as repetitions.

Return only the JSON output (as specified in the format) without extra commentary.
"""

    return prompt