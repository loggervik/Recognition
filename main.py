import time
import pytesseract
import os
import shutil
import pygetwindow as gw
import pyautogui
import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedStyle

# 设置Tesseract OCR的路径
pytesseract.pytesseract.tesseract_cmd = r'D:\Program Files\Tesseract-OCR\tesseract.exe'


# 初始化文件夹和结果文件的函数
def initialize_files():
    if os.path.exists("screenshots"):
        shutil.rmtree("screenshots")  # 删除并重新创建“screenshots”文件夹
    os.makedirs("screenshots")

    with open("result.txt", "w", encoding="utf-8") as file:
        file.write("")


# 截图及文本识别功能
def start_detection():
    initialize_files()

    root.iconify()  # 最小化主窗口
    screenshot_counter = 1

    while True:
        # 获取指定标题的窗口
        target_window = gw.getWindowsWithTitle("Radmin LAN")

        # 检查目标窗口是否存在
        if target_window:
            window = target_window[0]

            # 激活并获取窗口的位置与尺寸
            window.activate()
            x, y, width, height = window.left, window.top, window.width, window.height

            # 截取窗口区域的屏幕快照
            screenshot = pyautogui.screenshot(region=(x, y, width, height))

            # 保存屏幕快照
            screenshot_path = os.path.join("screenshots", f"screen_{screenshot_counter}.png")
            screenshot.save(screenshot_path)

            # 对屏幕快照进行文字识别
            text = pytesseract.image_to_string(screenshot)

            # 将识别出的文字写入结果文件
            with open("result.txt", "a", encoding="utf-8") as file:
                file.write(f"屏幕{str(screenshot_counter)}:\n{text}\n\n")

            screenshot_counter += 1
        else:
            print("未找到标题为 'Radmin LAN' 的窗口")

        time.sleep(10)  # 每隔10秒执行一次截图和识别


# 关闭程序的函数
def close_program():
    root.destroy()


# 创建主窗口
root = tk.Tk()
root.title("校验工具")
root.geometry("300x100")
style = ThemedStyle(root)
style.set_theme("arc")
# 创建并配置按钮
start_button = ttk.Button(root, text="启动检测", command=start_detection, style="Accent.TButton")
start_button.pack(side="left", padx=10)

close_button = ttk.Button(root, text="关闭", command=close_program, style="Warning.TButton")
close_button.pack(side="right", padx=10)

# 运行Tkinter事件循环
root.mainloop()
