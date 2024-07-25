import cv2
import subprocess
import os
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from queue import Queue, Empty
from threading import Thread

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("video_processing.log"),
        logging.StreamHandler()
    ]
)

ASCII_CHARS = "@%#*+=-:. "

def download_youtube_video(url, output_path, resolution="360p"):
    """Download a YouTube video at the specified resolution."""
    logging.info(f"Starting download for {url} with resolution {resolution}.")
    ydl_opts = {
        'format': f'bestvideo[height<={resolution[:-1]}]+bestaudio/best[height<={resolution[:-1]}]',
        'outtmpl': output_path + '.webm',
        'merge_output_format': 'mp4',
    }

    cmd = [
        'yt-dlp', url,
        '-f', ydl_opts['format'],
        '-o', ydl_opts['outtmpl'],
        '--merge-output-format', ydl_opts['merge_output_format']
    ]

    try:
        subprocess.run(cmd, check=True)
        logging.info("Video download completed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error downloading video: {e}")
        raise RuntimeError("Error downloading video!")

    try:
        os.rename(output_path + '.webm.mp4', output_path + '.mp4')
        logging.info(f"Video renamed to {output_path + '.mp4'}.")
    except FileNotFoundError:
        logging.error("Merged video file not found after download!")
        raise FileNotFoundError("Merged video file not found after download!")

def frame_to_ascii(frame, width=100):
    """Convert a video frame to ASCII art."""
    if frame is None:
        return ""
    
    height, original_width = frame.shape[:2]
    aspect_ratio = original_width / height
    new_height = int(width / aspect_ratio)

    resized_frame = cv2.resize(frame, (width, new_height))
    gray_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)

    ascii_art = ''.join(
        ASCII_CHARS[min(len(ASCII_CHARS) - 1, pixel_value // (256 // len(ASCII_CHARS)))]
        for pixel_value in gray_frame.flatten()
    )

    return ascii_art

def process_frame(frame_idx, width, frame, total_frames):
    """Process a single video frame and convert it to ASCII."""
    try:
        ascii_art = frame_to_ascii(frame, width)
        ascii_art_lines = [ascii_art[i:i + width] for i in range(0, len(ascii_art), width)]
        
        percentage_complete = (frame_idx + 1) / total_frames * 100
        logging.info(f"Processed frame {frame_idx}/{total_frames}. (Progress: {percentage_complete:.2f}%)")

        return frame_idx, "\n".join(ascii_art_lines) + "\n" + "=" * width + "\n"
    except Exception as e:
        logging.error(f"Error processing frame {frame_idx}: {e}")
        return frame_idx, ""

def write_ascii_to_file(file_path, queue, total_frames, video_metadata):
    """Write ASCII art frames to a text file, preserving order."""
    with open(file_path, 'w') as f:
        # Write metadata at the beginning.
        f.write(f"Video Resolution: {video_metadata['resolution']}\n")
        f.write(f"Video FPS: {video_metadata['fps']}\n")
        f.write("\n" + "=" * 80 + "\n\n")

        frames = {}
        frames_written = 0
        while frames_written < total_frames:
            try:
                frame_idx, ascii_art = queue.get(timeout=1)
                if frame_idx is None:  # End of queue signal.
                    continue
                frames[frame_idx] = ascii_art
                while frames_written in frames:
                    f.write(frames.pop(frames_written))
                    frames_written += 1
                logging.debug(f"Written {frames_written} frames to file.")
            except Empty:
                continue

def video_to_ascii(video_path, output_file, width=100, frame_step=10, num_processes=4):
    """Convert a video to ASCII art and save it to a text file."""
    logging.info(f"Converting video {video_path} to ASCII art...")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logging.error("Could not open video file!")
        raise ValueError("Could not open video file!")

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
   
    video_metadata = {
        'resolution': f"{video_width}x{video_height}",
        'fps': fps
    }
    
    logging.info(f"Video FPS: {fps}, Width: {video_width}, Height: {video_height}")
    logging.info(f"Total frames in video: {frame_count}")
    
    if frame_step == 1:
        logging.info("Processing all frames...")
    else:
        # Determine the ordinal suffix for `frame_step`.
        def ordinal(n):
            """Return the ordinal string for an integer."""
            if 10 <= n % 100 <= 20:
                suffix = 'th'
            else:
                suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
            return f"{n}{suffix}"

        logging.info(f"Processing every {ordinal(frame_step)} frame...")

    frame_indices = list(range(0, frame_count, frame_step))
    total_frames = len(frame_indices)

    queue = Queue(maxsize=num_processes * 2)

    with ProcessPoolExecutor(max_workers=num_processes) as executor:
        futures = []
        logging.info("Starting frame processing...")
        for i in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if not ret:
                logging.warning(f"Frame {i} could not be read!")
                continue

            futures.append(executor.submit(process_frame, i, width, frame, total_frames))

        writer_thread = Thread(target=write_ascii_to_file, args=(output_file, queue, total_frames, video_metadata))
        writer_thread.start()

        for future in as_completed(futures):
            frame_idx, ascii_art = future.result()
            queue.put((frame_idx, ascii_art))
        
        queue.put((None, None))  # Signal the end of processing.
        writer_thread.join()

    cap.release()
    logging.info(f'Video conversion to ASCII art completed, output written to "{output_file}".')

if __name__ == '__main__':
    url = 'https://www.youtube.com/watch?v=FtutLA63Cp8'
    output_path = 'video'

    try:
        logging.info("Starting video download...")
        download_youtube_video(url, output_path)
        logging.info("Video download complete. Starting video to ASCII conversion...")
        video_to_ascii(output_path + '.mp4', 'video_ascii.txt', width=160, frame_step=1, num_processes=32)
        logging.info('ASCII art video written to "video_ascii.txt".')
        os.remove(output_path + '.mp4')  # Clean up by removing the downloaded video.
        logging.info("Downloaded video file removed.")
    except Exception as e:
        logging.critical(f"An error occurred: {e}")

