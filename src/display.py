import time
import curses

def read_ascii_frames(file_path):
    """Read ASCII art frames from a text file."""
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Split the content into frames by the separator line
    frames = content.split("\n" + "=" * 80 + "\n")
    
    return frames

def display_ascii_animation(stdscr, frames, delay=0.1):
    """Display ASCII art frames in the terminal using curses."""
    curses.curs_set(0)  # Hide cursor
    terminal_height, terminal_width = stdscr.getmaxyx()
    
    while True:
        for frame in frames:
            stdscr.clear()
            
            # Resize and display frame within the terminal size
            lines = frame.split('\n')
            for y, line in enumerate(lines[:terminal_height]):
                if y < terminal_height:
                    stdscr.addstr(y, 0, line[:terminal_width])
            
            stdscr.refresh()
            time.sleep(delay)

if __name__ == "__main__":
    ascii_file_path = 'video_ascii.txt'
    delay = 1 / 24 # 24 FPS.
    
    try:
        frames = read_ascii_frames(ascii_file_path)
        curses.wrapper(display_ascii_animation, frames, delay)
    except FileNotFoundError:
        print(f"File {ascii_file_path} not found!")
    except Exception as e:
        print(f"An error occurred: {e}")

