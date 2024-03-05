import tkinter as tk
from tkinter import ttk  # 导入ttk模块，用于创建只读文本框
import pyautogui
import threading
import time
import pytesseract
import re

# 设置 Tesseract OCR 的路径
pytesseract.pytesseract.tesseract_cmd = r'D:\Program Files\Tesseract-OCR\tesseract.exe'
regions = [[], [], [], [], [], [], [], [], [], []]


class TransparentScreenCaptureTool:
    def __init__(self, root):
        self.root = root
        root.title("透明屏幕截图工具")
        root.attributes('-fullscreen', True)
        root.attributes('-alpha', 0.3)  # 调整透明度以提高性能
        self.canvas = tk.Canvas(root, bg="white", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.region_selected = False

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.region_selected = False

    def on_drag(self, event):
        self.end_x = event.x
        self.end_y = event.y
        self.canvas.delete("rectangle")
        self.canvas.create_rectangle(self.start_x, self.start_y, self.end_x, self.end_y, outline="red",
                                     tags="rectangle")

    def on_release(self, event):
        self.region = [self.start_x, self.start_y, self.end_x - self.start_x, self.end_y - self.start_y]
        self.region_selected = True
        self.canvas.delete("rectangle")  # 清除绘制的矩形
        self.root.destroy()  # 关闭区域选择窗口


class ScreenshotApp:
    def __init__(self, root):
        self.root = root
        root.title("校验")
        root.geometry("600x500")
        self.display_textboxes = []
        self.range_entries = []  # 保存范围文本框的列表
        self.labels = []
        self.select_buttons = []
        labels = ['水温', '进气压力', '进气温度', '中冷后压力', '中冷后温度', '排气背压', '机油温度', 'a', 'b', 'c']
        for i in range(10):
            label = tk.Label(root, text=f"{labels[i]}:")
            display_textbox = ttk.Entry(root, state="readonly")  # 创建只读文本框用于显示识别内容
            range_entry = tk.Entry(root, width=20)  # 范围输入文本框
            select_button = tk.Button(root, text="选择截图区域", command=lambda i=i: self.select_area(i))
            label.grid(row=i, column=0, padx=(10, 0), pady=10, sticky="e")
            display_textbox.grid(row=i, column=1, padx=(0, 10), pady=10, sticky="w")
            range_entry.grid(row=i, column=2, padx=(0, 10), pady=10, sticky="w")
            select_button.grid(row=i, column=3, pady=10)
            self.labels.append(label)
            self.display_textboxes.append(display_textbox)
            self.range_entries.append(range_entry)
            self.select_buttons.append(select_button)
        self.close_button = tk.Button(root, text="关闭", command=root.destroy)
        self.close_button.grid(row=11, column=0, columnspan=4, pady=10)
        threading.Thread(target=self.text_recognition_loop, daemon=True).start()

    def select_area(self, index):
        self.root.after(0, lambda: self.trigger_select(index))

    def trigger_select(self, index):
        tool = TransparentScreenCaptureTool(tk.Toplevel(self.root))
        self.root.wait_window(tool.root)  # 等待用户完成区域选择
        if tool.region_selected:
            regions[index] = tool.region
            screenshot = pyautogui.screenshot(region=tool.region)
            recognized_text = pytesseract.image_to_string(screenshot)
            filtered_text = self.filter_math_content(recognized_text)  # 过滤文本，仅保留数学内容
            self.set_display_textbox_content(index, filtered_text)
            del screenshot  # 释放截图对象占用的内存

    def set_display_textbox_content(self, index, content):
        self.display_textboxes[index].configure(state="normal")
        self.display_textboxes[index].delete(0, tk.END)
        self.display_textboxes[index].insert(0, content)
        self.display_textboxes[index].configure(state="readonly")

        # 检查数值是否在范围内
        try:
            value = float(content)
            if not self.check_value_within_range(value, self.range_entries[index]):
                self.flash_entry(self.range_entries[index])
        except ValueError:
            pass

    def check_value_within_range(self, value, range_entry):
        range_text = range_entry.get()
        try:
            lower, upper = map(float, range_text.split(','))
            if lower <= value <= upper:
                return True
        except ValueError:
            pass
        return False

    def flash_entry(self, entry):
        current_color = entry.cget("bg")
        new_color = "red" if current_color == "white" else "white"
        entry.configure(bg=new_color)
        self.root.after(500, lambda: self.flash_entry(entry))

    def filter_math_content(self, text):
        pattern = r"[-+]?[0-9]*\.?[0-9]+"
        matches = re.findall(pattern, text)
        return ' '.join(matches)

    def text_recognition_loop(self):
        while True:
            time.sleep(5)  # 每5秒检查一次
            for i, region in enumerate(regions):
                if region:
                    screenshot = pyautogui.screenshot(region=region)
                    recognized_text = pytesseract.image_to_string(screenshot)
                    self.root.after(0, lambda i=i, text=recognized_text: self.set_display_textbox_content(i,
                                                                                                          self.filter_math_content(
                                                                                                              text)))
                    del screenshot  # 释放截图对象占用的内存


def main():
    root = tk.Tk()
    app = ScreenshotApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
