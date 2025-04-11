import os
import json
import ffmpeg
import subprocess
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

VIDEO_PATH = "../artifacts/samples/11-vs-bonus.mp4"
TRANSCRIPT_PATH = "../artifacts/transcripts/11-vs-bonus.json"

def get_video_duration(video_path: str) -> float:
    """Get video duration using ffprobe"""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        video_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        data = json.loads(result.stdout)
        return float(data['format']['duration'])
    except (KeyError, json.JSONDecodeError, ValueError):
        raise RuntimeError("Failed to retrieve video duration using ffprobe.")

def trim_video(video_path: str, invalid_timestamps: List[Dict[str, float]], output_path: str):
    """
    Trim the video based on the invalid timestamps using ffmpeg.
    """
    invalid_timestamps.sort(key=lambda x: x['start_time'])
    duration = get_video_duration(video_path)

    valid_segments = []

    if invalid_timestamps and invalid_timestamps[0]['start_time'] > 0:
        valid_segments.append((0, invalid_timestamps[0]['start_time']))

    for i in range(len(invalid_timestamps) - 1):
        current_end = invalid_timestamps[i]['end_time']
        next_start = invalid_timestamps[i + 1]['start_time']
        if next_start > current_end:
            valid_segments.append((current_end, next_start))

    if invalid_timestamps and invalid_timestamps[-1]['end_time'] < duration:
        valid_segments.append((invalid_timestamps[-1]['end_time'], duration))

    if not valid_segments and not invalid_timestamps:
        valid_segments.append((0, duration))

    if not valid_segments:
        logging.warning("No valid segments found after trimming.")
        return

    temp_file_list = "temp_file_list.txt"
    temp_files = []

    try:
        for i, (start, end) in enumerate(valid_segments):
            temp_file = f"temp_segment_{i}.mp4"
            temp_files.append(temp_file)

            (
                ffmpeg
                .input(video_path, ss=start, to=end)
                .output(temp_file, c="copy")
                .run(quiet=True, overwrite_output=True)
            )

        with open(temp_file_list, "w") as f:
            for temp_file in temp_files:
                f.write(f"file '{temp_file}'\n")

        (
            ffmpeg
            .input(temp_file_list, format="concat", safe=0)
            .output(output_path, c="copy")
            .run(quiet=True, overwrite_output=True)
        )
        logging.info(f"Trimmed video saved to {output_path}")

    except Exception as e:
        logging.warning("Concat demuxer failed. Trying filter_complex...")

        try:
            filter_parts = []
            concat_parts = []

            for i, (start, end) in enumerate(valid_segments):
                filter_parts.append(
                    f"[0:v]trim=start={start:.6f}:end={end:.6f},setpts=PTS-STARTPTS[v{i}];"
                    f"[0:a]atrim=start={start:.6f}:end={end:.6f},asetpts=PTS-STARTPTS[a{i}];"
                )
                concat_parts.append(f"[v{i}][a{i}]")

            filter_script = ''.join(filter_parts) + ''.join(concat_parts) + f"concat=n={len(valid_segments)}:v=1:a=1[outv][outa]"

            (
                ffmpeg
                .input(video_path)
                .filter_complex(filter_script)
                .output(output_path, map="[outv]", map_audio="[outa]")
                .run(quiet=True, overwrite_output=True)
            )
            logging.info(f"Trimmed video saved to {output_path} (using filter_complex)")

        except Exception as e:
            logging.warning("filter_complex failed. Trying raw subprocess...")

            try:
                filter_parts = []
                concat_parts = []

                for i, (start, end) in enumerate(valid_segments):
                    filter_parts.append(
                        f"[0:v]trim=start={start:.6f}:end={end:.6f},setpts=PTS-STARTPTS[v{i}];"
                        f"[0:a]atrim=start={start:.6f}:end={end:.6f},asetpts=PTS-STARTPTS[a{i}];"
                    )
                    concat_parts.append(f"[v{i}][a{i}]")

                filter_script = ''.join(filter_parts) + ''.join(concat_parts) + f"concat=n={len(valid_segments)}:v=1:a=1[outv][outa]"

                cmd = [
                    "ffmpeg", "-i", video_path,
                    "-filter_complex", filter_script,
                    "-map", "[outv]", "-map", "[outa]",
                    "-c:v", "libx264", "-c:a", "aac",
                    "-y", output_path
                ]
                subprocess.run(cmd, check=True)
                logging.info(f"Trimmed video saved to {output_path} (using subprocess)")

            except subprocess.CalledProcessError as e:
                logging.error(f"Error during video trimming: {e}")

    finally:
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        if os.path.exists(temp_file_list):
            os.remove(temp_file_list)

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
