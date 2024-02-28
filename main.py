import tkinter as tk
import time
import pytesseract
import os
import shutil
import pygetwindow as gw
import pyautogui

# Specify the Tesseract installation path
pytesseract.pytesseract.tesseract_cmd = r'D:\Program Files\Tesseract-OCR\tesseract.exe'


def initialize_files():
    if os.path.exists("screenshots"):
        shutil.rmtree("screenshots")  # Remove the existing screenshots folder
    os.makedirs("screenshots")  # Create an empty screenshots folder

    with open("result.txt", "w", encoding="utf-8") as file:
        file.write("")  # Reset the content of result.txt


def start_detection():
    initialize_files()  # Clear old screenshots and reset result.txt

    root.iconify()  # Minimize the window
    counter = 1  # Initialize a counter for screenshot filenames
    while True:
        # Get the window by its title
        window = gw.getWindowsWithTitle("Radmin VPN")[0]

        # Activate the window
        window.activate()

        # Get the window's position and size
        x, y, width, height = window.left, window.top, window.width, window.height

        # Capture the window's screenshot using pyautogui
        screenshot = pyautogui.screenshot(region=(x, y, width, height))

        # Save the screenshot to the "screenshots" folder
        screenshot_path = os.path.join("screenshots", f"screen_{counter}.png")
        screenshot.save(screenshot_path)

        # Perform text recognition on the entire screenshot
        text = pytesseract.image_to_string(screenshot)

        # Write the entire recognized text to a text file
        with open("result.txt", "a", encoding="utf-8") as file:
            file.write(f"Screen {counter}:\n{text}\n\n")

        counter += 1
        time.sleep(10)  # Wait for 10 seconds between each capture


def close_program():
    root.destroy()  # Close the window


# Create the main window
root = tk.Tk()
root.title("Text Detection")
root.geometry("300x100")

# Create buttons
start_button = tk.Button(root, text="启动检测", command=start_detection)
start_button.pack(side="left", padx=10)
close_button = tk.Button(root, text="关闭", command=close_program)
close_button.pack(side="right", padx=10)

# Run the Tkinter event loop
root.mainloop()
