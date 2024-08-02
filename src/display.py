import time
import curses

def read_ascii_frames(file_path):
    """Read ASCII art frames from a text file and extract metadata."""
    frames = []
    metadata = {}

    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()

        # Initialize metadata parsing state.
        parsing_metadata = True
        frame_lines = []

        for line in lines:
            line = line.rstrip()  # Strip only trailing whitespace.
            if not line:
                # Stop parsing metadata when encountering an empty line.
                parsing_metadata = False
                continue

            if parsing_metadata:
                if line.startswith("Video Resolution:"):
                    metadata['resolution'] = line.split(":", 1)[1].strip()
                elif line.startswith("Video FPS:"):
                    try:
                        metadata['fps'] = int(line.split(":", 1)[1].strip())
                    except ValueError:
                        raise ValueError(f"Invalid FPS value in metadata: {line.split(':', 1)[1].strip()}")
            else:
                # Collect frames after metadata has been parsed.
                if line.startswith("=" * 80):
                    if frame_lines:  # Avoid adding empty frames.
                        frames.append('\n'.join(frame_lines))
                        frame_lines = []  # Reset for next frame.
                else:
                    frame_lines.append(line)

        # Append the last frame if any.
        if frame_lines:
            frames.append('\n'.join(frame_lines))

    except FileNotFoundError:
        raise FileNotFoundError(f"File {file_path} not found!")
    except Exception as e:
        raise RuntimeError(f"An error occurred while reading frames: {e}")

    return frames, metadata

def display_ascii_animation(stdscr, frames, fps=24):
    """Display ASCII art frames in the terminal using curses."""
    curses.curs_set(0)  # Hide cursor.
    stdscr.nodelay(1)   # Make getch() non-blocking.
    
    terminal_height, terminal_width = stdscr.getmaxyx()
    frame_duration = 1 / fps
    start_time = time.time()

    frame_index = 0
    while frame_index < len(frames):
        frame_start_time = time.time()

        # Clear the screen.
        stdscr.clear()
        
        # Resize and display frame within the terminal size.
        frame_lines = frames[frame_index].split('\n')
        for y, line in enumerate(frame_lines[:terminal_height]):
            if y < terminal_height:
                stdscr.addstr(y, 0, line[:terminal_width])
        
        stdscr.refresh()

        render_time = time.time() - frame_start_time
        elapsed_time = time.time() - start_time
        expected_time = (frame_index + 1) * frame_duration
        time_to_sleep = expected_time - elapsed_time - render_time

        if time_to_sleep > 0:
            time.sleep(time_to_sleep)
            frame_index += 1
        else:
            # Calculate the next frame index based on the elapsed time
            frame_index = int(elapsed_time // frame_duration)

        # Check for user input to quit the animation.
        if stdscr.getch() != -1:
            return

if __name__ == "__main__":
    ascii_file_path = 'video_ascii.txt'

    try:
        frames, metadata = read_ascii_frames(ascii_file_path)
        fps = metadata.get('fps', 24)  # Default to 24 FPS if not found.
        
        curses.wrapper(display_ascii_animation, frames, fps)
    
    except FileNotFoundError as fnf_error:
        print(fnf_error)
    except RuntimeError as re:
        print(re)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

