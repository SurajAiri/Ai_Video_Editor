import os
import json
import subprocess
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

VIDEO_PATH = "../artifacts/samples/11-vs-bonus.mp4"
TRANSCRIPT_PATH = "../artifacts/transcripts/11-vs-bonus.json"

def get_video_duration(video_path: str) -> float:
    """Get video duration using ffprobe - optimized for speed"""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",  # Only analyze video stream
        "-show_entries", "format=duration",
        "-of", "json",
        video_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    try:
        data = json.loads(result.stdout)
        return float(data['format']['duration'])
    except (KeyError, json.JSONDecodeError, ValueError):
        raise RuntimeError("Failed to retrieve video duration using ffprobe.")

def trim_video(video_path: str, invalid_timestamps: List[Dict[str, float]], output_path: str):
    """
    Trim the video based on the invalid timestamps using a single ffmpeg command
    with complex filtergraph, avoiding any temporary file creation.
    """
    try:
        # Sort and validate timestamps
        invalid_timestamps.sort(key=lambda x: x['start_time'])
        duration = get_video_duration(video_path)

        # Identify valid segments
        valid_segments = []
        if not invalid_timestamps:
            valid_segments.append((0, duration))
        else:
            if invalid_timestamps[0]['start_time'] > 0:
                valid_segments.append((0, invalid_timestamps[0]['start_time']))

            for i in range(len(invalid_timestamps) - 1):
                current_end = invalid_timestamps[i]['end_time']
                next_start = invalid_timestamps[i + 1]['start_time']
                if next_start > current_end:
                    valid_segments.append((current_end, next_start))

            if invalid_timestamps[-1]['end_time'] < duration:
                valid_segments.append((invalid_timestamps[-1]['end_time'], duration))

        if not valid_segments:
            logging.warning("No valid segments found after trimming.")
            return

        # Build a single-pass complex filter
        filter_parts = []
        concat_parts = []

        for i, (start, end) in enumerate(valid_segments):
            filter_parts.append(
                f"[0:v]trim=start={start:.6f}:end={end:.6f},setpts=PTS-STARTPTS[v{i}];"
                f"[0:a]atrim=start={start:.6f}:end={end:.6f},asetpts=PTS-STARTPTS[a{i}];"
            )
            concat_parts.append(f"[v{i}][a{i}]")

        filter_script = ''.join(filter_parts) + ''.join(concat_parts) + f"concat=n={len(valid_segments)}:v=1:a=1[outv][outa]"

        # Direct single-command execution
        cmd = [
            "ffmpeg", "-nostdin", "-y",
            "-i", video_path,
            "-filter_complex", filter_script,
            "-map", "[outv]", "-map", "[outa]",
            "-c:v", "libx264", "-c:a", "aac", 
            "-preset", "ultrafast",  # Fastest encoding preset
            "-crf", "23",            # Balance quality vs speed
            "-threads", "0",         # Use all available CPU threads
            output_path
        ]
        
        # For smaller segments or simple edits, avoid re-encoding if possible
        if len(valid_segments) == 1 or sum((end - start) for start, end in valid_segments) < 0.9 * duration:
            # Try to use segment extraction without re-encoding
            if len(valid_segments) == 1:
                start, end = valid_segments[0]
                cmd = [
                    "ffmpeg", "-nostdin", "-y",
                    "-i", video_path,
                    "-ss", f"{start:.6f}",
                    "-to", f"{end:.6f}",
                    "-c", "copy",  # Copy without re-encoding
                    output_path
                ]
        
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        logging.info(f"Trimmed video saved to {output_path}")

    except subprocess.CalledProcessError as e:
        logging.error(f"Error during video trimming: {e}")
        logging.error(f"ffmpeg stderr: {e.stderr.decode() if hasattr(e, 'stderr') else 'unknown'}")
        
        # Fallback to simpler method if complex filter fails
        try:
            # For simple cases, just try stream copying the entire video
            if len(valid_segments) == 1:
                start, end = valid_segments[0]
                cmd = [
                    "ffmpeg", "-nostdin", "-y",
                    "-i", video_path,
                    "-ss", f"{start:.6f}",
                    "-to", f"{end:.6f}",
                    "-c", "copy",
                    output_path
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                logging.info(f"Trimmed video saved to {output_path} (fallback simple method)")
            else:
                # For complex cases, try with simpler encoding parameters
                filter_script = ''.join(filter_parts) + ''.join(concat_parts) + f"concat=n={len(valid_segments)}:v=1:a=1[outv][outa]"
                cmd = [
                    "ffmpeg", "-nostdin", "-y",
                    "-i", video_path,
                    "-filter_complex", filter_script,
                    "-map", "[outv]", "-map", "[outa]",
                    "-c:v", "libx264", "-preset", "veryfast",
                    "-c:a", "aac",
                    output_path
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                logging.info(f"Trimmed video saved to {output_path} (fallback encoding method)")
        except Exception as fallback_error:
            logging.error(f"Fallback also failed: {fallback_error}")

if __name__ == "__main__":
    invalid_timestamps = [
        {'start_time': 0.48, 'end_time': 7.12},
        {'start_time': 10.72, 'end_time': 15.60},
        {'start_time': 16.66, 'end_time': 24.27}
    ]
    import time

    start = time.time()
    output_path = os.path.splitext(VIDEO_PATH)[0] + "_trimmed.mp4"
    
    trim_video(VIDEO_PATH, invalid_timestamps, output_path)
    
    end = time.time()
    print(f"Time taken: {end - start:.2f} seconds")