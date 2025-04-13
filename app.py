import os
import streamlit as st
from src.llm.llm import llm_call_analyse_sent, llm_call_analyse_word
from src.models.invalid_model import InvalidModel
from src.transcribe.deepgram_transcriber import deepgram_transcribe
from src.utils.json_parser import llm_json_parser
from src.utils.transcript_format import format_deepgram_transcript_sent, format_deepgram_transcript_word
from src.utils.video_trimmer import trim_video as video_trimmer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def trim_video(video_path, output_path, verbose=False, progress_bar=None):
    try:
        # Update progress
        if progress_bar:
            progress_bar.progress(0.1)
            st.write("Transcribing the video...")
            
        # Transcribe the video
        transcript = deepgram_transcribe(video_path)
        if verbose:
            st.write("Transcription completed.")
            st.write("Transcription result: ", transcript)

        # Update progress
        if progress_bar:
            progress_bar.progress(0.3)
            
        with open("transcript.json", "w") as f:
            f.write(transcript)
        if verbose:
            st.write("Transcription saved to transcript.json")
        transcript = llm_json_parser(transcript)
        
        if verbose:
            st.write("Parsed transcript: ", transcript)
            
        # Update progress
        if progress_bar:
            progress_bar.progress(0.4)
            st.write("Analyzing sentences...")
            
        # Sentence analysis
        formatted_sent = format_deepgram_transcript_sent(transcript)
        if verbose:
            st.write("Formatted transcript: ", formatted_sent)
        res = llm_call_analyse_sent(formatted_sent)
        if verbose:
            st.write("LLM response: ", res)
        res = llm_json_parser(res)
        if verbose:
            st.write("Sentence analysis result:", res)

        # Update progress
        if progress_bar:
            progress_bar.progress(0.6)
            st.write("Processing invalid segments...")
            
        # Invalids
        invalids = [InvalidModel.from_dict(item) for item in res['data']]
        invalids.sort(key=lambda x: x.start_time)
        if verbose:
            st.write(f"Invalid entries from sentence analysis: {invalids}")

        # Word analysis
        if progress_bar:
            st.write("Analyzing words...")
            
        word_inv = format_deepgram_transcript_word(transcript, invalids)
        resp_word = llm_call_analyse_word(word_inv)
        resp_word = llm_json_parser(resp_word)
        if verbose:
            st.write("Word analysis result:", resp_word)

        # Update progress
        if progress_bar:
            progress_bar.progress(0.8)
            
        # Process word-level invalids
        invalids_word = [InvalidModel.from_dict(item) for item in resp_word['data']]
        invalids_word.sort(key=lambda x: x.start_time)
        if verbose:
            st.write(f"Invalid entries from word analysis: {invalids_word}")

        # Merge the invalids
        # Remove invalids from isEntire = false as they are further analyzed
        invalids = [item for item in invalids if item.is_entire]
        invalids.extend(invalids_word)
        if verbose:
            st.write(f"Combined invalid entries: {invalids}")

        # Update progress
        if progress_bar:
            progress_bar.progress(0.9)
            st.write("Trimming the video...")
            
        # Finally trim the video
        video_trimmer(video_path, invalids, output_path)
        
        # Update progress
        if progress_bar:
            progress_bar.progress(1.0)
            
        st.success("Video trimmed successfully.")
        return output_path

    except Exception as e:
        st.error(f"Error processing video: {e}")
        return None

def main():
    st.set_page_config(page_title="AI Video Editor", page_icon="🎬", layout="wide")
    
    st.title("AI Video Editor")
    st.subheader("Automatically trim videos based on content analysis")
    
    # File upload
    uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "mov", "avi"])
    
    # Settings
    with st.expander("Advanced Settings"):
        verbose = st.checkbox("Enable verbose output")
        output_name = st.text_input("Custom output filename (optional)")
    
    if uploaded_file is not None:
        # Save the uploaded file temporarily
        temp_path = os.path.join("temp", uploaded_file.name)
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.video(temp_path)
        
        # Set output path
        if output_name:
            # Always ensure output is .mp4 format
            output_name = os.path.splitext(output_name)[0]  # Remove any existing extension
            output_path = os.path.join("output", f"{output_name}.mp4")
        else:
            filename, ext = os.path.splitext(uploaded_file.name)
            output_path = os.path.join("output", f"{filename}_trimmed{ext}")
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Process button
        if st.button("Process Video"):
            st.write(f"Processing video: {uploaded_file.name}")
            
            progress_bar = st.progress(0)
            trimmed_video_path = trim_video(temp_path, output_path, verbose, progress_bar)
            
            if trimmed_video_path:
                st.write(f"Trimmed video saved to: {trimmed_video_path}")
                st.video(trimmed_video_path)
                
                # Download button
                with open(trimmed_video_path, "rb") as file:
                    btn = st.download_button(
                        label="Download trimmed video",
                        data=file,
                        file_name=os.path.basename(trimmed_video_path),
                        mime="video/mp4"
                    )
            else:
                st.error("Failed to trim video.")

if __name__ == "__main__":
    main()