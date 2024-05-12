import tkinter as tk
import numpy as np
from paddleocr import PaddleOCR
from deep_translator import GoogleTranslator
from deep_translator import DeeplTranslator
from windowcapture import WindowCapture
import configparser
from pynput import keyboard
import threading
import requests
import winreg
import time
import os

curpath = os.path.dirname(os.path.realpath(__file__))
cfgpath = os.path.join(curpath, "config.ini")
icopath = os.path.join(curpath, "icon.ico")

# Global variable to track the overlay window
overlay_window = None
canvas = None
thread = None  # Global variable to hold the thread object
is_licensed = False

def get_machine_guid():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", 0, winreg.KEY_READ)
        value, _ = winreg.QueryValueEx(key, "MachineGuid")
        return value
    except Exception as e:
        print("Error:", e)
        return None
    
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
    global is_licensed
    if is_licensed == False:
        time.sleep(10)
    
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

    # Display the image on the canvas
    # canvas.create_image(0, 0, anchor=tk.NW, image=screenshot)

    for idx in range(len(result)):
            res = result[idx]
            for line in res:
                bbox = line[0]
                text = line[1][0]

                translated_text = GoogleTranslator(target='en').translate(text)
                # # translated_text = DeeplTranslator(api_key='ede3a8cd-d467-4ad9-808d-87e317dbf74d:fx', source='zh', target='en').translate(text)

                # Draw rectangle
                canvas.create_rectangle(bbox[0][0], bbox[0][1], bbox[2][0], bbox[2][1], fill="#1C1C1C")
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
    overlay_window.title("Trnsl8 v1.0.0")

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
config.read(cfgpath)
trigger_translate_key = config.get('Shortcuts', 'trigger_translate')
license_key = config.get('Licensing', 'license_key')
src_language = config.get('Detection', 'src_language')

url = "http://kx-labs.com:3000/verify_license"
api_key = "2024_verify_trnsl8"
headers = {
    "api_key": api_key,
    "Content-Type": "application/json"  # Assuming JSON content, adjust as needed
}
machine_guid = get_machine_guid()
payload = {
    "license_key": license_key,
    "machine_identifier": machine_guid
}
response = requests.post(url, json=payload, headers=headers)
is_licensed = response.json()['status'] == 'valid'
app_height = 150
src_lang = "ch"
if is_licensed:
    valid_until = response.json()['valid_until']
    app_height = 190
    src_lang = src_language


# Create the main application window
root = tk.Tk()
root.title("Trnsl8 v1.0.0")
root.geometry(f"250x{app_height}+50+50")
root.resizable(False, False)  # Prevent resizing
root.iconbitmap(icopath)  # Add icon

# Create a listener for keyboard events
listener = keyboard.Listener(on_press=on_key_event)
if is_licensed:
    listener.start()

# Create buttons for translate and clear
button_translate = tk.Button(root, text="Translate", command=on_button_click, bg="#3498db", fg="white", font=("Arial", 12), bd=0, borderwidth=0, highlightthickness=0, width=10, relief=tk.FLAT)
button_translate.pack(pady=10)
button_clear = tk.Button(root, text="Clear", command=close_overlay, bg="#e74c3c", fg="white", font=("Arial", 12), bd=0, borderwidth=0, highlightthickness=0, width=10, relief=tk.FLAT)
button_clear.pack(pady=10)

wincap = WindowCapture('ODIN')

# Initialize paddleocr reader
ocr = PaddleOCR(use_angle_cls=True, lang=src_lang)

if is_licensed:
    license_label = tk.Label(root, text="Licensed. Expiry: " + valid_until, fg="gray")
    license_label.pack(side="bottom")
else:
    license_label = tk.Label(root, text="Unlicensed.", fg="gray")
    license_label.pack(side="bottom")
attribution_label = tk.Label(root, text="Icon by iconsax@www.flaticon.com ", fg="gray")
attribution_label.pack(side="bottom")
copyright_label = tk.Label(root, text="© 2024 kx-labs.com", fg="gray")
copyright_label.pack(side="bottom")

root.mainloop()
