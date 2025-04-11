import os
from moviepy import VideoFileClip, concatenate_videoclips  # todo: later use ffmpeg-python instead of moviepy

VIDEO_PATH = "../artifacts/samples/11-vs-bonus.mp4"
TRANSCRIPT_PATH = "../artifacts/transcripts/11-vs-bonus.json"

def trim_video(video_path: str, invalid_timestamps: list, output_path: str):
    """
    Trim the video based on the invalid timestamps
    """
    # Load the video clip
    clip = VideoFileClip(video_path)
    
    # Create a list to store valid segments
    valid_segments = []
    
    # Sort timestamps by start_time to ensure proper order
    invalid_timestamps.sort(key=lambda x: x['start_time'])
    
    # Add the segment from 0 to the first invalid timestamp
    if len(invalid_timestamps) > 0 and invalid_timestamps[0]['start_time'] > 0:
        valid_segments.append(clip.subclipped(0, invalid_timestamps[0]['start_time']))
    
    # Add segments between invalid timestamps
    for i in range(len(invalid_timestamps) - 1):
        current_end = invalid_timestamps[i]['end_time']
        next_start = invalid_timestamps[i + 1]['start_time']
        
        if next_start > current_end:
            valid_segments.append(clip.subclipped(current_end, next_start))
    
    # Add the segment from the last invalid timestamp to the end
    if len(invalid_timestamps) > 0 and invalid_timestamps[-1]['end_time'] < clip.duration:
        valid_segments.append(clip.subclipped(invalid_timestamps[-1]['end_time'], clip.duration))
    
    # If no valid segments were found or no invalid timestamps provided, keep the entire clip
    if len(valid_segments) == 0 and len(invalid_timestamps) == 0:
        valid_segments.append(clip)
    
    # Concatenate all valid segments if there are any
    if valid_segments:
        final_clip = concatenate_videoclips(valid_segments)
        final_clip.write_videofile(output_path, codec='libx264')
        final_clip.close()
    else:
        print("No valid segments found after trimming.")
    
    # Close the original clip
    clip.close()

if __name__ == "__main__":
    # Sample invalid timestamps
    invalid_timestamps = [
        {'start_time': 0.48, 'end_time': 7.12},
        {'start_time': 10.72, 'end_time': 15.60},
        {'start_time': 16.66, 'end_time': 24.27}
    ]
    import time
    start = time.time()
    # Generate output path
    output_path = os.path.splitext(VIDEO_PATH)[0] + "_trimmed.mp4"
    
    # Trim the video
    trim_video(VIDEO_PATH, invalid_timestamps, output_path)
    end = time.time()
    print(f"Video trimmed in {end - start:.2f} seconds.")