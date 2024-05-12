# trnsl8
 A simple overlay translator tool for Windows.

# Requirements
- Use Python 3.7 max for compatibility with paddleocr.
- Install dependencies via `pip install -r requirements.txt`

# Generate exe
- pyinstaller --noconfirm --onedir --windowed --icon "D:/repo/trnsl8/icon.ico" --add-data "D:/repo/trnsl8/libs/mklml.dll;." --add-data "D:/repo/trnsl8/config.ini;." --add-data "D:/repo/trnsl8/icon.ico;." --collect-all "paddleocr" --hidden-import "imghdr" --hidden-import "torch" --hidden-import "imgaug" --hidden-import "pyclipper" --collect-data "scipy"  "D:/repo/trnsl8/main.py"

# Credits
- Translation icons created by iconsax - Flaticon https://www.flaticon.com/free-icons/translation