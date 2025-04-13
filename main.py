import os
from src.llm.llm import llm_call_analyse_sent, llm_call_analyse_word
from src.models.invalid_model import InvalidModel
from src.transcribe.deepgram_transcriber import deepgram_transcribe
from src.utils.json_parser import llm_json_parser
from src.utils.transcript_format import format_deepgram_transcript_sent, format_deepgram_transcript_word
from src.utils.video_trimmer import trim_video as video_trimmer
from dotenv import load_dotenv

load_dotenv()

def trim_video(video_path:str, output_path:str):
    try:
        # transcribe the video
        transcript = deepgram_transcribe(video_path)
        print("Transcription completed.")
        print("Transcription result: ", transcript)

        with open("transcript.json", "w") as f:
            f.write(transcript)
        print("Transcription saved to transcript.json")
        transcript = llm_json_parser(transcript)
        
        print("transcript: ", transcript)
        # sentence analysis
        formatted_sent = format_deepgram_transcript_sent(transcript)
        print("Formatted transcript: ", formatted_sent)
        res = llm_call_analyse_sent(formatted_sent)
        print("LLM response: ", res)
        res = llm_json_parser(res)
        print("sent: ",res)

        # invalids
        invalids = [InvalidModel.from_dict(item) for item in res['data']]
        invalids.sort(key=lambda x: x.start_time)
        print(f"Invalid entries: {invalids}")

        # word analysis
        word_inv = format_deepgram_transcript_word(transcript, invalids)
        resp_word = llm_call_analyse_word(word_inv)
        resp_word = llm_json_parser(resp_word)
        print(resp_word)

        # invalids
        invalids_word = [InvalidModel.from_dict(item) for item in resp_word['data']]
        invalids_word.sort(key=lambda x: x.start_time)
        print(f"Invalid entries: {invalids_word}")

        # merge the invalids
        # remove invalids from isEntire = false as the are further analyzed
        invalids = [item for item in invalids if item.is_entire]
        invalids.extend(invalids_word)
        print(f"Invalid entries: {invalids}")

        # finally trim the video
        # Here you would add the code to trim the video using the invalids list
        print("trimming the video...")
        video_trimmer(video_path, invalids, output_path)
        print("Video trimmed successfully.")
        print("saved to: ", output_path)
        return output_path

    except Exception as e:
        print(f"Error processing video: {e}")
        return None


def main():
    # Example usage
    VIDEO_PATH = "/Users/suraj/vscode/aiml/genai/ai_video_editor/artifacts/samples/11-vs-bonus.mp4"
    OUTPUT_PATH = os.path.splitext(VIDEO_PATH)[0] + "_trimmed_main.mp4"
    
    trimmed_video_path = trim_video(VIDEO_PATH, OUTPUT_PATH)
    
    if trimmed_video_path:
        print(f"Trimmed video saved to: {trimmed_video_path}")
    else:
        print("Failed to trim video.")
    

if __name__ == "__main__":
    main()