import cv2
import subprocess
import os

def download_youtube_video(url, output_path, resolution="360p"):
    # Download the video and convert it to mp4.
    ydl_opts = {
        'format': f'bestvideo[height<={resolution[:-1]}]+bestaudio/best[height<={resolution[:-1]}]',
        'outtmpl': output_path + '.webm',
        'merge_output_format': 'mp4',  # Ensure output is in mp4 format
        'quiet': False
    }
    
    # Using yt-dlp command line as subprocess call.
    cmd = [
        'yt-dlp', url,
        '-f', ydl_opts['format'],
        '-o', ydl_opts['outtmpl'],
        '--merge-output-format', ydl_opts['merge_output_format']
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Error downloading video: {e}")

    # After merging the video and audio, the file will be named 'video.webm.mp4'.
    # Rename the file to 'video.mp4' for consistent processing.
    try:
        os.rename(output_path + '.webm.mp4', output_path + '.mp4')
    except FileNotFoundError:
        raise ValueError("Merged video file not found after download!")


def frame_to_ascii(frame, width=100):
    # Resize frame maintaining the aspect ratio.
    height, original_width = frame.shape[:2]
    aspect_ratio = original_width / height
    new_height = int(width / aspect_ratio)
    
    resized_frame = cv2.resize(frame, (width, new_height))
    
    # Convert frame to grayscale.
    gray_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)
    
    # ASCII characters from dark to light.
    ascii_chars = "@%#*+=-:. "
    
    # Normalize the grayscale values to map to ASCII characters.
    ascii_art = ""
    for pixel_value in gray_frame.flatten():
        # Ensure index is within bounds of ascii_chars.
        index = min(len(ascii_chars) - 1, pixel_value // (256 // len(ascii_chars)))
        ascii_art += ascii_chars[index]
        
    return ascii_art


def video_to_ascii(video_path, output_file, width=100, frame_step=10):
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        raise ValueError("Could not open video file!")
    
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    with open(output_file, 'w') as f:
        for i in range(frame_count):
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process every nth frame (defined by frame_step).
            if i % frame_step == 0:
                try:
                    ascii_art = frame_to_ascii(frame, width)
                    
                    # Split the ascii_art into lines according to width.
                    ascii_art_lines = [ascii_art[index:index+width] for index in range(0, len(ascii_art), width)]
                    
                    # Write to file with a frame separator.
                    f.write("\n".join(ascii_art_lines) + "\n")
                    f.write("\n" + "=" * width + "\n")  # Separator between frames.
                except Exception as e:
                    print(f"Error processing frame {i}: {e}")
                
    cap.release()


if __name__ == '__main__':
    url = 'https://www.youtube.com/watch?v=FtutLA63Cp8'
    output_path = 'video'

    try:
        download_youtube_video(url, output_path)
        video_to_ascii(output_path + '.mp4', 'video_ascii.txt', width=80, frame_step=1)

        print("ASCII art video written to video_ascii.txt")

        os.remove(output_path + '.mp4')  # Clean up by removing the downloaded video.
    except Exception as e:
        print(f"An error occurred: {e}")

