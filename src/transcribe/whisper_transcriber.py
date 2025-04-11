import whisper

# transcribe the video using whisper
def transcribe_video(video_path: str):
    """
    Transcribe the video using Whisper
    """

    # Load the Whisper model
    model = whisper.load_model("turbo")
    print("Model loaded.")
    
    # Transcribe the video
    result = model.transcribe(video_path, task="transcribe", language="en",  condition_on_previous_text=False, word_timestamps=True)
    print("Transcription completed.")

    # Print the transcription
    # print(result["text"])
    return result