import numpy as np
import win32gui, win32ui, win32con
from ctypes import windll

class WindowCapture:

    # properties
    w = 0
    h = 0
    hwnd = None
    cropped_x = 0
    cropped_y = 0
    offset_x = 0
    offset_y = 0

    # constructor
    def __init__(self, hwnd):
        self.hwnd = hwnd
        # find the handle for the window we want to capture
        if not self.hwnd:
            raise Exception('No window selected.')
        
        # get the window size
        window_rect = win32gui.GetWindowRect(self.hwnd)
        self.w = window_rect[2] - window_rect[0]
        self.h = window_rect[3] - window_rect[1]

        # account for the window border and titlebar and cut them off
        border_pixels = 8
        titlebar_pixels = 30
        self.w = self.w - (border_pixels * 2)
        self.h = self.h - titlebar_pixels - border_pixels
        self.cropped_x = border_pixels
        self.cropped_y = titlebar_pixels

        # set the cropped coordinates offset so we can translate screenshot
        # images into actual screen positions
        self.offset_x = window_rect[0] + self.cropped_x
        self.offset_y = window_rect[1] + self.cropped_y

    def get_screenshot(self):
        hwnd = self.hwnd
        hwnd_dc = win32gui.GetWindowDC(hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()
        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(mfc_dc, self.w, self.h)
        save_dc.SelectObject(bitmap)
        save_dc.BitBlt((0, 0), (self.w, self.h), mfc_dc, (self.cropped_x, self.cropped_y), win32con.SRCCOPY)

        # If Special K is running, this number is 3. If not, 1
        result = windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 3)

        bmpstr = bitmap.GetBitmapBits(True)

        img = np.fromstring(bmpstr, dtype='uint8')
        img.shape = (self.h, self.w, 4)
        img = img[...,:3]
        img = np.ascontiguousarray(img)

        if not result:  # result should be 1
            win32gui.DeleteObject(bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwnd_dc)
            raise RuntimeError(f"Unable to acquire screenshot! Result: {result}")

        return img
    
    # to be merged with __init__
    def get_window_info(self):
        # Find the window handle by title
        hwnd = self.hwnd
        if hwnd == 0:
            return None

        # Get window position and dimensions
        window_rect = win32gui.GetWindowRect(hwnd)
        width = window_rect[2] - window_rect[0]
        height = window_rect[3] - window_rect[1]

        # account for the window border and titlebar and cut them off
        border_pixels = 8
        titlebar_pixels = 30
        width = width - (border_pixels * 2)
        height = height - titlebar_pixels - border_pixels

        return window_rect[0], window_rect[1], width, height
