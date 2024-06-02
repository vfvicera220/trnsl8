import tkinter as tk
from tkinter import StringVar, ttk
from tkinter import messagebox 
import numpy as np
from paddleocr import PaddleOCR
from deep_translator import GoogleTranslator
from deep_translator import DeeplTranslator
from windowcapture import WindowCapture
from pynput import keyboard
import configparser
import threading
import win32gui
import requests
import sv_ttk
import winreg
import time
# from datetime import datetime
import json
import os

class Trnsl8App:
    def __init__(self):
        self.curpath = os.path.dirname(os.path.realpath(__file__))
        self.cfgpath = os.path.join(self.curpath, "config.ini")
        self.icopath = os.path.join(self.curpath, "icon.ico")
        self.load_config()
        self.cachepath = os.path.join(self.curpath, "data_files", "cache", self.cfg_src_language + "_" + self.cfg_to_language, "translation_cache.json")
        
        self.licensing_url = "http://kx-labs.com:3000/verify_license"
        self.api_key = "2024_verify_trnsl8"

        self.src_lang = self.cfg_src_language
        self.trg_lang = self.cfg_to_language
        self.app_height = "280"
        self.window_list = []
        self.selected_hwnd = None
        self.is_licensed = False
        self.overlay_window = None
        self.settings_window = None
        self.canvas = None
        self.thread = None

        self.key_list = [
            ("`", "`"),
            ("F1", "f1"),
            ("F2", "f2"),
            ("F3", "f3"),
            ("F4", "f4"),
            ("F5", "f5"),
            ("F6", "f6"),
            ("F7", "f7"),
            ("F8", "f8"),
            ("F9", "f9"),
            ("F10", "f10"),
            ("F11", "f11"),
            ("F12", "f12"),
        ]

        self.language_list_from = [
            ("English", "en"),
            ("Chinese (Simplified)", "ch"),
            ("Chinese (Traditional)", "chinese_cht"),
            ("Japanese", "japan"),
            ("Korean", "korean")
        ]

        self.language_list_to = [
            ("English", "en"),
            ("Chinese (Simplified)", "zh-CN"),
            ("Chinese (Traditional)", "zh-TW"),
            ("Japanese", "ja"),
            ("Korean", "ko")
        ]

        win32gui.EnumWindows(self.winEnumHandler, None)

        self.setup_ocr()
        self.get_license_info()
        self.init_cache()
        self.setup_window()

        if self.is_licensed:
            self.setup_keyboard_listener()

    def init_cache(self):
        self.translation_cache = {}
        try:
            # Try to open the file in exclusive creation mode
            with open(self.cachepath, "x", encoding="utf-8") as f:
                # If the file doesn't exist, this block will execute
                # You can do additional setup here if needed
                json.dump({'dummy': 'dummy'}, f, ensure_ascii=False)
                print("Cache file created successfully.")
        except FileExistsError:
            # If the file already exists, this block will execute
            # You can handle the situation as per your requirements
            print("File already exists.")
            # Load cache from file if it exists
            if os.path.exists(self.cachepath):
                with open(self.cachepath, "r", encoding="utf-8") as f:
                    self.translation_cache = json.load(f)
        except FileNotFoundError:
            # If any of the directories leading up to the file don't exist, this block will execute
            # You might want to create the directories before creating the file
            os.makedirs(os.path.dirname(self.cachepath), exist_ok=True)
            print("Directories created. Cache file created successfully.")
            with open(self.cachepath, "x", encoding="utf-8") as f:
                # You can do additional setup here if needed
                json.dump({'dummy': 'dummy'}, f, ensure_ascii=False)
                print("Cache file created successfully.")

    def winEnumHandler(self, hwnd, ctx):
        if win32gui.IsWindowVisible(hwnd):
            window_title = win32gui.GetWindowText(hwnd)
            self.window_list.append((hwnd, window_title))

    def on_select(self, event):
        # Retrieve the selected window title from the Combobox
        selected_title = self.window_dropdown.get()
        # Find the corresponding hwnd
        for hwnd, title in self.window_list:
            if title == selected_title:
                self.selected_hwnd = hwnd
                self.wincap = WindowCapture(hwnd)

    def on_select_from_language(self, event):
        selected_lang = self.from_lng_dropdown.get()
        for longform, key in self.language_list_from:
            if longform == selected_lang:
                self.src_lang = key
                self.config['Detection']['src_language'] = key
                with open(self.cfgpath, 'w') as configfile:    # save
                    self.config.write(configfile)
                self.setup_ocr()
                self.cachepath = os.path.join(self.curpath, "data_files", "cache", key + "_" + self.cfg_to_language, "translation_cache.json")
                self.init_cache()

    def on_select_to_language(self, event):
        selected_lang = self.to_lng_dropdown.get()
        for longform, key in self.language_list_to:
            if longform == selected_lang:
                self.trg_lang = key
                self.config['Detection']['to_language'] = key
                with open(self.cfgpath, 'w') as configfile:    # save
                    self.config.write(configfile)
                self.cachepath = os.path.join(self.curpath, "data_files", "cache",  self.cfg_src_language + "_" + key, "translation_cache.json")
                self.init_cache()

    def on_select_translate_key(self, event):
        if not self.is_licensed:
            messagebox.showinfo("Unlicensed", "This feature is for PRO users only.")
        else:
            translate_key = self.translate_key_dropdown.get()
            for display_text, key in self.key_list:
                if display_text == translate_key:
                    self.cfg_trigger_translate_key = key
                    self.config['Shortcuts']['trigger_translate'] = key
                    with open(self.cfgpath, 'w') as configfile:    # save
                        self.config.write(configfile)
    
    def on_select_clear_key(self, event):
        if not self.is_licensed:
            messagebox.showinfo("Unlicensed", "This feature is for PRO users only.")
        else:
            clear_key = self.clear_key_dropdown.get()
            for display_text, key in self.key_list:
                if display_text == clear_key:
                    self.cfg_trigger_clear_key = key
                    self.config['Shortcuts']['clear_translate'] = key
                    with open(self.cfgpath, 'w') as configfile:    # save
                        self.config.write(configfile)

    def get_lang_from_key_index(self):
        index = None
        for i, (_, code) in enumerate(self.language_list_from):
            if code == self.src_lang:
                index = i
                break
        return index
    
    def get_lang_to_key_index(self):
        index = None
        for i, (_, code) in enumerate(self.language_list_to):
            if code == self.trg_lang:
                index = i
                break
        return index
    
    def get_translate_key_index(self):
        index = None
        for i, (_, code) in enumerate(self.key_list):
            if code == self.cfg_trigger_translate_key:
                index = i
                break
        return index
    
    def get_clear_key_index(self):
        index = None
        for i, (_, code) in enumerate(self.key_list):
            if code == self.cfg_trigger_clear_key:
                index = i
                break
        return index
    
    def load_config(self):
        self.config = configparser.ConfigParser()
        self.config.read(self.cfgpath)
        self.cfg_trigger_translate_key = self.config.get('Shortcuts', 'trigger_translate')
        self.cfg_trigger_clear_key = self.config.get('Shortcuts', 'clear_translate')
        self.cfg_license_key = self.config.get('Licensing', 'license_key')
        self.cfg_src_language = self.config.get('Detection', 'src_language')
        self.cfg_to_language = self.config.get('Detection', 'to_language')

    def get_machine_guid(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, "MachineGuid")
            return value
        except Exception as e:
            messagebox.showerror("Error", "Cannot get unique machine identifier.")
            return None
        
    def get_license_info(self):
        if self.cfg_license_key:
            machine_guid = self.get_machine_guid()
            headers = {
                "api_key": self.api_key,
                "Content-Type": "application/json"  # Assuming JSON content, adjust as needed
            }
            payload = {
                "license_key": self.cfg_license_key,
                "machine_identifier": machine_guid
            }
            response = requests.post(self.licensing_url, json=payload, headers=headers)
            self.is_licensed = response.json()['status'] == 'valid'
            if self.is_licensed:
                self.valid_until = response.json()['valid_until']
                self.app_height = "280"

    def setup_window(self):
        self.root = tk.Tk()
        self.root.title("Trnsl8 v1.0.0")
        self.root.geometry("250x" + self.app_height + "+50+50")
        self.root.resizable(False, False)
        self.root.iconbitmap(self.icopath)

        self.sel_window_label = ttk.Label(self.root, text="App: ", font=("Helvetica", 10))
        self.sel_window_label.place(x=12, y=21)
        self.window_dropdown = ttk.Combobox(self.root, width=17, state="readonly")
        self.window_dropdown['values'] = [title for hwnd, title in self.window_list]
        self.window_dropdown.place(x=53, y=15)
        self.window_dropdown.bind("<<ComboboxSelected>>", self.on_select)

        self.button_refresh_list = ttk.Button(self.root, text="Refresh", command=self.refresh_window_list)
        self.button_refresh_list.place(x=164, y=58)

        self.button_settings = ttk.Button(self.root, text="Settings", command=self.create_settings_window)
        self.button_settings.place(x=11, y=58)

        padding = 40
        self.from_lang_label = ttk.Label(self.root, text="From Lang:", font=("Helvetica", 10))
        self.from_lang_label.place(x=12, y=67 + padding)
        self.from_lng_dropdown = ttk.Combobox(self.root, width=12, state="readonly")
        self.from_lng_dropdown['values'] = [item[0] for item in self.language_list_from]
        self.from_lng_dropdown.place(x=93, y=61 + padding)
        self.from_lng_dropdown.current(self.get_lang_from_key_index())
        self.from_lng_dropdown.bind("<<ComboboxSelected>>", self.on_select_from_language)
        
        self.to_lang_label = ttk.Label(self.root, text="To Lang:", font=("Helvetica", 10))
        self.to_lang_label.place(x=12, y=112 + padding)
        self.to_lng_dropdown = ttk.Combobox(self.root, width=12, state="readonly")
        self.to_lng_dropdown['values'] = [item[0] for item in self.language_list_to]
        self.to_lng_dropdown.place(x=93, y=105 + padding)
        self.to_lng_dropdown.current(self.get_lang_to_key_index())
        self.to_lng_dropdown.bind("<<ComboboxSelected>>", self.on_select_to_language)

        self.progress_bar = ttk.Progressbar(self.root, orient="horizontal", length=300, mode="indeterminate",style="custom.Horizontal.TProgressbar")
        self.progress_bar.pack(side="bottom")

        self.button_translate = ttk.Button(self.root, text="Translate", command=self.start_thread, style='Accent.TButton')
        self.button_translate.place(x=123, y=155 + padding)

        self.button_clear = ttk.Button(self.root, text="Clear", command=self.close_overlay)
        self.button_clear.place(x=55, y=155 + padding)

        self.license_label_string = StringVar()
        if self.is_licensed:
            self.license_label_string.set("Licensed. Expiry: " + self.valid_until)
        else:
            self.license_label_string.set("Unlicensed.")
        self.license_label = ttk.Label(self.root, textvariable=self.license_label_string, font=("Helvetica", 8))
        self.license_label.pack(side="bottom")
        self.copyright_label = ttk.Label(self.root, text="© 2024 kx-labs.com", font=("Helvetica", 8))
        self.copyright_label.pack(side="bottom")
        
        sv_ttk.set_theme("dark")

    def setup_keyboard_listener(self):
        self.listener = keyboard.Listener(on_press=self.on_key_event)
        self.listener.start()

    def setup_ocr(self):
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang=self.src_lang,
            use_gpu=False,
            cls_model_dir="data_files\\cls\\" + self.src_lang,
            det_model_dir="data_files\\det\\" + self.src_lang,
            rec_model_dir="data_files\\rec\\" + self.src_lang
        )
            
    def on_key_event(self, key):
        try:
            key_char = key.char
        except AttributeError:
            key_char = key.name

        if self.cfg_trigger_translate_key == key_char:
            self.start_thread()

        if self.cfg_trigger_clear_key == key_char and self.thread is None or not self.thread.is_alive():
            self.close_overlay()

    def on_button_click(self):
        self.create_overlay()

    def refresh_window_list(self):
        self.window_list = []
        win32gui.EnumWindows(self.winEnumHandler, None)
        self.window_dropdown['values'] = [title for hwnd, title in self.window_list]

    def start_thread(self):
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self.create_overlay, daemon=True)
            self.thread.start()

    def capture_and_display_image(self, width, height):
        if not self.is_licensed:
            time.sleep(20)

        screenshot = self.wincap.get_screenshot()
        image_np = np.array(screenshot)
        result = self.ocr.ocr(image_np, cls=True)
        # print(str(datetime.now()) + " Text detection done! Translating...")
        self.canvas = tk.Canvas(self.overlay_window, width=width, height=height)
        self.canvas.configure(bg='white', highlightthickness=0)
        self.canvas.config(bg="black")

        # translate texts in batch
        texts = [line[1][0] for res in result for line in res]

        # Filter out texts that are already translated
        untranslated_texts = [text for text in texts if text not in self.translation_cache]
        # print("Untranslated texts: ")
        # print(untranslated_texts)

        # Translate only the untranslated texts and store them in the cache
        if untranslated_texts:
            translated_texts = GoogleTranslator(target=self.trg_lang).translate_batch(untranslated_texts)
            for original_text, translated_text in zip(untranslated_texts, translated_texts):
                if original_text not in self.translation_cache:
                    self.translation_cache[original_text] = translated_text

        # Write the updated cache to file
        with open(self.cachepath, "w", encoding="utf-8") as f:
            json.dump(self.translation_cache, f, ensure_ascii=False)
        # print(str(datetime.now()) + " Translation done!")
        for idx in range(len(result)):
            res = result[idx]
            for index, line in enumerate(res):
                bbox = line[0]

                # Retrieve translated text from cache
                original_text = texts[index]
                translated_text = self.translation_cache.get(original_text, "")

                self.canvas.create_rectangle(bbox[0][0], bbox[0][1], bbox[2][0], bbox[2][1], fill="#1C1C1C")
                # debug code for bounding box
                # self.canvas.create_rectangle(bbox[0][0], bbox[0][1], bbox[2][0], bbox[2][1], outline="#008000")
                center_x = (bbox[0][0] + bbox[2][0]) / 2
                center_y = (bbox[0][1] + bbox[2][1]) / 2
                self.canvas.create_text(center_x, center_y, text=translated_text, fill="white")
        self.canvas.pack()
        self.progress_bar.stop()

    def save_api_key(self):
        self.cfg_license_key = self.sv.get()
        self.config['Licensing']['license_key'] = self.cfg_license_key
        with open(self.cfgpath, 'w') as configfile:    # save
            self.config.write(configfile)
        self.get_license_info()
        if self.is_licensed:
            self.license_label_string.set("Licensed. Expiry: " + self.valid_until)
            self.setup_keyboard_listener()
        else:
            self.license_label_string.set("Unlicensed.")
        
    def close_settings_handler(self):
        self.save_api_key()
        self.close_settings()

    def create_settings_window(self):
        state = "disabled"
        if self.is_licensed:
            state = "readonly"

        self.close_settings()
        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("Settings")
        self.settings_window.protocol("WM_DELETE_WINDOW", self.close_settings_handler)
        self.settings_window.iconbitmap(self.icopath)
        x, y = (s for s in self.root.geometry().split("+")[1:])
        self.settings_window.geometry(f"300x150+{x}+{y}")

        padding = 7
        self.translate_key_label = ttk.Label(self.settings_window, text="Translate Action Key:", font=("Helvetica", 10),)
        self.translate_key_label.place(x=21, y=15 + padding)
        self.translate_key_dropdown = ttk.Combobox(self.settings_window, width=12, state=state)
        self.translate_key_dropdown['values'] = [item[0] for item in self.key_list]
        self.translate_key_dropdown.place(x=163, y=9 + padding)
        self.translate_key_dropdown.current(self.get_translate_key_index())
        self.translate_key_dropdown.bind("<<ComboboxSelected>>", self.on_select_translate_key)

        self.clear_key_label = ttk.Label(self.settings_window, text="Clear Action Key:", font=("Helvetica", 10))
        self.clear_key_label.place(x=21, y=55 + padding)
        self.clear_key_dropdown = ttk.Combobox(self.settings_window, width=12, state=state)
        self.clear_key_dropdown['values'] = [item[0] for item in self.key_list]
        self.clear_key_dropdown.place(x=163, y=50 + padding)
        self.clear_key_dropdown.current(self.get_clear_key_index())
        self.clear_key_dropdown.bind("<<ComboboxSelected>>", self.on_select_clear_key)

        self.license_label = ttk.Label(self.settings_window, text="License Key:", font=("Helvetica", 10),)
        self.license_label.place(x=21, y=105 + padding)
        self.sv = StringVar()
        self.license_input_field = ttk.Entry(self.settings_window, textvariable=self.sv, width=25, justify = 'center', validate="focusout", validatecommand=self.save_api_key)
        self.license_input_field.place(x=115, y=100 + padding)
        self.license_input_field.insert(0, self.cfg_license_key) 

    def create_overlay(self):
        if self.selected_hwnd == None:
            messagebox.showinfo("Info", "No application selected.")
        else:
            self.progress_bar.start()
            self.close_overlay()

            self.overlay_window = tk.Toplevel(self.root)
            self.overlay_window.title("Trnsl8 v1.0.0")
            self.overlay_window.iconbitmap(self.icopath)

            window_info = self.wincap.get_window_info()
            if window_info:
                left, top, width, height = window_info
                self.overlay_window.geometry(f"{width}x{height}+{left}+{top}")
                self.overlay_window.configure(background="black")
                self.overlay_window.wm_attributes("-transparentcolor", "black")
                self.overlay_window.config(bg="black")
                self.capture_and_display_image(width, height)
                # commenting code below as it causes the window to spawn
                # in wrong position
                # self.overlay_window.attributes("-topmost", False)
            else:
                messagebox.showinfo("Info", "Window not found.")

    def close_overlay(self):
        if self.overlay_window is not None and self.overlay_window.winfo_exists():
            self.overlay_window.destroy()
            if self.canvas is not None and self.canvas.winfo_exists():
                self.canvas.destroy()

    def close_settings(self):
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.destroy()
            if self.canvas is not None and self.canvas.winfo_exists():
                self.canvas.destroy()

if __name__ == "__main__":
    app = Trnsl8App()
    app.root.mainloop()