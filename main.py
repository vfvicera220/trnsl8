import tkinter as tk
from tkinter import ttk
import numpy as np
from paddleocr import PaddleOCR
from deep_translator import GoogleTranslator
from windowcapture import WindowCapture
import configparser
from pynput import keyboard
import threading

# Global variable to track the overlay window
overlay_window = None
canvas = None
thread = None  # Global variable to hold the thread object

def on_key_event(key):
    global overlay_window, thread
    
    try:
        key_char = key.char  # Get the character value of the key
    except AttributeError:
        key_char = key.name  # If it's a special key (like 'esc'), get its name

    if trigger_translate_key == key_char:
        start_thread()

def on_button_click():
    create_overlay()

def start_thread():
    # Check if a thread is already running
    global thread
    if thread is None or not thread.is_alive():
        # Create and start a new thread
        thread = threading.Thread(target=create_overlay)
        thread.start()

def capture_and_display_image(width, height):
    global canvas
    # get an updated image of the game
    screenshot = wincap.get_screenshot()
    # Convert PIL image to numpy array
    image_np = np.array(screenshot)
    # Perform OCR on the image
    result = ocr.ocr(image_np, cls=True)

    # Create a canvas widget to display the image
    canvas = tk.Canvas(overlay_window, width=width, height=height)
    canvas.configure(bg='white', highlightthickness=0)
    canvas.config(bg="black")  # Set the background color to black to allow transparency
    canvas.pack()

    for idx in range(len(result)):
        res = result[idx]
        for line in res:
            bbox = line[0]
            text = line[1][0]

            translated_text = GoogleTranslator(target='en').translate(text)

            # Draw rectangle
            canvas.create_rectangle(bbox[0][0], bbox[0][1], bbox[2][0], bbox[2][1], fill="#4caf50")
            # Calculate center of the rectangle
            center_x = (bbox[0][0] + bbox[2][0]) / 2
            center_y = (bbox[0][1] + bbox[2][1]) / 2
            # Draw text inside the rectangle
            canvas.create_text(center_x, center_y, text=translated_text, fill="white")

def create_overlay():
    global overlay_window
    
    # Close existing overlay window, if any
    close_overlay()
    
    overlay_window = tk.Toplevel(root)
    overlay_window.title("trnsl8 v1.0.0")

    # Set window dimensions
    window_info = wincap.get_window_info()
    if window_info:
        left, top, width, height = window_info
        overlay_window.geometry(f"{width}x{height}+{left}+{top}")
        print(window_info)
        # Set the window to be on top
        overlay_window.attributes("-topmost", True)  

        overlay_window.configure(background="black")  # Set a fallback background color
        overlay_window.wm_attributes("-transparentcolor", "black")  # Set transparent color
        overlay_window.config(bg="black")  # Set the background color to black to allow transparency

        capture_and_display_image(width, height)
    else:
        print("Window not found.")

def close_overlay():
    global overlay_window, canvas
    
    if overlay_window is not None and overlay_window.winfo_exists():
        overlay_window.destroy()
        # Destroy the canvas widget if it exists
        if canvas is not None and canvas.winfo_exists():
            canvas.destroy()

config = configparser.ConfigParser()
config.read('config.ini')
trigger_translate_key = config.get('Shortcuts', 'trigger_translate')

# Create the main application window
root = tk.Tk()
root.title("trnsl8 v1.0.0")
root.geometry("250x170+50+50")
root.resizable(False, False)  # Prevent resizing
root.iconbitmap("icon.ico")  # Add icon

# Create a listener for keyboard events
listener = keyboard.Listener(on_press=on_key_event)
listener.start()

# Create buttons for translate and clear
style = ttk.Style()
style.theme_use('clam')  # Use the 'clam' theme for a flatter appearance
style.configure('TButton', foreground='white', background='#4caf50', font=('Roboto', 12))  # Roboto is a Material Design font

button_translate = ttk.Button(root, text="Translate", command=on_button_click)
button_translate.pack(pady=10)
button_clear = ttk.Button(root, text="Clear", command=close_overlay)
button_clear.pack(pady=10)

wincap = WindowCapture('ODIN')

# Initialize paddleocr reader
ocr = PaddleOCR(use_angle_cls=True, lang='ch')

# Add copyright label at the bottom
attribution_label = tk.Label(root, text="Icon by iconsax\nwww.flaticon.com/free-icons/translation ", fg="gray")
attribution_label.pack(side="bottom")
copyright_label = tk.Label(root, text="© 2024 trnsl8. All rights reserved.", fg="gray")
copyright_label.pack(side="bottom")

root.mainloop()
