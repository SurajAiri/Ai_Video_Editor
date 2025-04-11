import os
import json
import subprocess
import tempfile
import logging
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

VIDEO_PATH = "../artifacts/samples/11-vs-bonus.mp4"

def get_video_duration(video_path: str) -> float:
    """Get video duration using ffprobe - optimized for speed"""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",  # Only analyze video stream
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    try:
        return float(result.stdout.strip())
    except ValueError:
        raise RuntimeError("Failed to retrieve video duration using ffprobe.")

def get_keyframe_positions(video_path: str) -> List[float]:
    """Get keyframe timestamps for more accurate cuts"""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-skip_frame", "nokey",
        "-select_streams", "v:0",
        "-show_entries", "frame=pts_time",
        "-of", "csv=p=0",
        video_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    try:
        keyframes = [float(line.strip()) for line in result.stdout.split('\n') if line.strip()]
        return keyframes
    except ValueError:
        logging.warning("Could not get keyframe information, using default cutting method")
        return []

def process_segment(video_path: str, start: float, end: float, output_path: str, use_keyframes: bool = False):
    """Process a single segment, optimized for accuracy and speed"""
    
    # For very short segments (under 2 seconds), use accurate method with re-encoding
    if end - start < 2.0:
        cmd = [
            "ffmpeg", "-nostdin", "-y",
            "-ss", f"{start:.6f}",
            "-to", f"{end:.6f}",
            "-i", video_path,
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
            "-c:a", "aac", "-strict", "experimental",
            "-avoid_negative_ts", "1",
            output_path
        ]
    # For longer segments, use faster stream copy when possible
    else:
        # Use a small input seek (not accurate but faster) for long seeks
        # And refined output seek for precision
        seek_before = max(0, start - 1.0) if use_keyframes else start
        
        cmd = [
            "ffmpeg", "-nostdin", "-y",
            "-ss", f"{seek_before:.6f}",
            "-i", video_path
        ]
        
        if use_keyframes:
            # Additional precise cut with re-encoding
            cmd.extend([
                "-ss", f"{start - seek_before:.6f}",
                "-to", f"{end - seek_before:.6f}"
            ])
        else:
            cmd.extend([
                "-to", f"{end - seek_before:.6f}"
            ])
            
        cmd.extend([
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
            "-c:a", "aac", "-strict", "experimental",
            "-avoid_negative_ts", "1",
            output_path
        ])
    
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return output_path

def create_concat_file(segment_files: List[str], concat_file: str):
    """Create a concat demuxer file for ffmpeg"""
    with open(concat_file, "w") as f:
        for file_path in segment_files:
            f.write(f"file '{file_path}'\n")

def concatenate_videos(concat_file: str, output_path: str):
    """Concatenate video segments using the concat demuxer"""
    cmd = [
        "ffmpeg", "-nostdin", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_file,
        "-c", "copy",  # Just copy streams, no re-encoding
        output_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

def trim_video(video_path: str, invalid_timestamps: List[Dict[str, float]], output_path: str):
    """
    Trim the video based on the invalid timestamps using a hybrid approach:
    - Process segments in parallel
    - Use precise cutting for short segments and faster methods for longer ones
    - Concatenate segments efficiently
    """
    try:
        # Sort and validate timestamps
        invalid_timestamps.sort(key=lambda x: x['start_time'])
        duration = get_video_duration(video_path)
        keyframes = get_keyframe_positions(video_path)
        use_keyframes = len(keyframes) > 0

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

        # Process segments in parallel 
        with tempfile.TemporaryDirectory() as tmpdir:
            segment_files = []
            
            # Process each segment in a thread pool
            with ThreadPoolExecutor(max_workers=min(os.cpu_count(), len(valid_segments))) as executor:
                futures = []
                
                for i, (start, end) in enumerate(valid_segments):
                    segment_path = os.path.join(tmpdir, f"segment_{i}.mp4")
                    segment_files.append(segment_path)
                    
                    futures.append(executor.submit(
                        process_segment, 
                        video_path, 
                        start, 
                        end, 
                        segment_path,
                        use_keyframes
                    ))
                
                # Wait for all segments to complete
                for future in futures:
                    future.result()
            
            # Create concat file
            concat_file = os.path.join(tmpdir, "concat_list.txt")
            create_concat_file(segment_files, concat_file)
            
            # Concatenate all segments
            concatenate_videos(concat_file, output_path)
            
            logging.info(f"Trimmed video saved to {output_path}")

    except subprocess.CalledProcessError as e:
        logging.error(f"Error during video trimming: {e}")
        logging.error(f"ffmpeg stderr: {e.stderr.decode() if hasattr(e, 'stderr') else 'unknown'}")
        
        # Fallback to simpler method if complex processing fails
        try:
            # Use single-pass ffmpeg for fallback (similar to your accurate method)
            if len(valid_segments) == 1:
                start, end = valid_segments[0]
                cmd = [
                    "ffmpeg", "-nostdin", "-y",
                    "-i", video_path,
                    "-ss", f"{start:.6f}",
                    "-to", f"{end:.6f}",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                    "-c:a", "aac",
                    output_path
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                logging.info(f"Trimmed video saved to {output_path} (fallback method)")
            else:
                # For multiple segments, create a complex filtergraph as fallback
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
                    "ffmpeg", "-nostdin", "-y",
                    "-i", video_path,
                    "-filter_complex", filter_script,
                    "-map", "[outv]", "-map", "[outa]",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                    "-c:a", "aac",
                    output_path
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                logging.info(f"Trimmed video saved to {output_path} (fallback complex filter method)")
        except Exception as fallback_error:
            logging.error(f"Fallback also failed: {fallback_error}")

if __name__ == "__main__":
    invalid_timestamps = [
        {'start_time': 0.48, 'end_time': 1.36},
        {'start_time': 2.399, 'end_time': 2.72},
    ]
    
    import time
    start = time.time()
    
    output_path = os.path.splitext(VIDEO_PATH)[0] + "_optimized_trimmed.mp4"
    trim_video(VIDEO_PATH, invalid_timestamps, output_path)
    
    end = time.time()
    print(f"Time taken: {end - start:.2f} seconds")