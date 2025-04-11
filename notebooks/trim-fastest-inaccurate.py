# fastest one
import os
import json
import subprocess
import tempfile
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

VIDEO_PATH = "../artifacts/samples/11-vs-bonus.mp4"

def get_video_duration(video_path: str) -> float:
    """Fastest video duration retrieval."""
    result = subprocess.run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ], stdout=subprocess.PIPE, text=True)
    
    return float(result.stdout.strip())

def trim_fast_segments(video_path: str, valid_segments: List[tuple], output_path: str):
    """Trim valid segments using stream copy, then concatenate."""
    with tempfile.TemporaryDirectory() as tmpdir:
        segment_files = []

        # Extract valid segments without re-encoding
        for idx, (start, end) in enumerate(valid_segments):
            seg_path = os.path.join(tmpdir, f"part_{idx}.ts")
            segment_files.append(seg_path)
            
            cmd = [
                "ffmpeg", "-nostdin", "-y",
                "-ss", f"{start:.3f}",
                "-to", f"{end:.3f}",
                "-i", video_path,
                "-c", "copy", "-avoid_negative_ts", "make_zero",
                "-f", "mpegts", seg_path
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Create a list file for concatenation
        list_path = os.path.join(tmpdir, "segments.txt")
        with open(list_path, "w") as f:
            for seg in segment_files:
                f.write(f"file '{seg}'\n")

        # Concatenate all segments into final output
        concat_cmd = [
            "ffmpeg", "-nostdin", "-y",
            "-f", "concat", "-safe", "0",
            "-i", list_path,
            "-c", "copy", output_path
        ]
        subprocess.run(concat_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

def process_video(video_path: str, invalid_timestamps: List[Dict[str, float]], output_path: str):
    invalid_timestamps.sort(key=lambda x: x['start_time'])
    duration = get_video_duration(video_path)

    # Compute valid segments
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
        logging.warning("No valid segments to keep.")
        return

    try:
        trim_fast_segments(video_path, valid_segments, output_path)
        logging.info(f"Fast trimmed video saved to: {output_path}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Fast trim failed: {e.stderr.decode()}")
        logging.error("Try reducing number of segments or fallback to re-encoding method.")

if __name__ == "__main__":
    invalid_timestamps = [
        {'start_time': 0.48, 'end_time': 1.36},
        {'start_time': 2.399, 'end_time': 2.72},
    ]

    import time
    start = time.time()

    output_path = os.path.splitext(VIDEO_PATH)[0] + "_fast_trimmed3.mp4"
    process_video(VIDEO_PATH, invalid_timestamps, output_path)

    end = time.time()
    print(f"Time taken: {end - start:.2f} seconds")
