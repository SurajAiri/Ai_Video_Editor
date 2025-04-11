import os
import pathlib
import whisper
import json

VIDEO_PATH = pathlib.Path("/Users/suraj/vscode/aiml/genai/ai_video_editor/artifacts/samples/sample2.mp3")

if not VIDEO_PATH.exists():
    print(f"Path {VIDEO_PATH} does not exist. Please set the correct path.")
    exit(1)


# transcribe the video using whisper
def transcribe_video(video_path: str):
    """
    Transcribe the video using Whisper
    """
    model = whisper.load_model("turbo")
    print("Model loaded.")
    result = model.transcribe(video_path, task="transcribe", language="en",  condition_on_previous_text=False, word_timestamps=True)
    print("Transcription completed.")
    print(result["text"])
    return result

def save_transcription(transcription: str, output_path: str = "transcription.json"):
    """
    Save the transcription to a file
    """
    with open(output_path, 'w') as f:
        json.dump(transcription, f)
    print(f"Transcription saved to {output_path}")


def filler_words_check(transcription: str):
    """
    Check for filler words in the transcription
    """
    print("Checking for filler words...")
    filler_words = ["um", "uh", "like", "you know", "well", "so"]
    for word in filler_words:
        if word in transcription.lower():
            print(f"Filler word found: {word}")
            return True
    return False

# check for long pauses
def long_pauses_check(transcription: str):
    """
    Check for long pauses in the transcription
    """
    print("Checking for long pauses...")
    if '   ' in transcription:
        print("Long pause found.")
        return True
    return False

# check for repeated sentences
def repeated_sentences_check(transcription: str):
    """
    Check for repeated sentences in the transcription
    """
    print("Checking for repeated sentences...")
    sentences = transcription.split('.')
    for i, sentence in enumerate(sentences):
        if sentence.strip() in sentences[i+1:]:
            print(f"Repeated sentence found: {sentence.strip()}")
            return True
    return False

# analyse the transcription
def analyse_transcription(transcription: str):
    """
    Analyse the transcription to separate valid and invalid segments
    """
    # this will consider filler words as invalid segments
    # this will also consider long pauses as invalid segments
    # this will consider repeated sentences as invalid segments and latest sentence as valid
    # also have the type of invalid types

    print("Analysing transcription...")

    filler_words = ["um", "uh", "like", "you know", "well", "so"]
    segments = []

    # Split transcription into segments based on punctuation
    sentences = transcription.split('.')
    for sentence in sentences:
        if not sentence.strip():
            continue
            
        segment = {
            'text': sentence.strip(),
            'valid': True,
            'invalid_type': None
        }

        # Check for filler words
        for filler in filler_words:
            if filler in sentence.lower():
                segment['valid'] = False
                segment['invalid_type'] = 'filler_words'

        # Check for long pauses (3+ spaces between words)
        if '   ' in sentence:
            segment['valid'] = False
            segment['invalid_type'] = 'long_pause'

        # Check for repeated content
        for existing_segment in segments:
            if segment['text'].lower() == existing_segment['text'].lower():
                existing_segment['valid'] = False
                existing_segment['invalid_type'] = 'repetition'
                break

        segments.append(segment)

    return segments

    

# separate valid and invalid segments

# remove invalid segments

# generate the video

