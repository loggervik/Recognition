import tkinter as tk
from tkinter import ttk, messagebox   # 导入ttk模块，用于创建只读文本框
import threading
import time
import pytesseract
import re
import sys
import os
from PIL import ImageGrab
import ctypes
from openpyxl import Workbook  # 导入Workbook


# 获取系统DPI设置
def get_scaling_factor():
    # Set process DPI awareness
    ctypes.windll.shcore.SetProcessDpiAwareness(1)

    # Get desktop handle
    hDesktop = ctypes.windll.user32.GetDesktopWindow()

    # Get DPI for primary monitor
    dpi = ctypes.windll.user32.GetDpiForWindow(hDesktop)
    scaling_factor = dpi / 96.0  # Windows默认DPI为96
    return scaling_factor


# 调整bbox坐标
def adjust_bbox_for_scaling(bbox, scaling_factor):
    return tuple([int(coord * scaling_factor) for coord in bbox])


if hasattr(sys, '_MEIPASS'):

    # 如果程序被PyInstaller打包，则使用打包后的临时路径
    base_path = sys._MEIPASS
else:
    # 如果程序没有被打包，则使用正常的__file__路径
    base_path = os.path.dirname(os.path.abspath(__file__))

pytesseract.pytesseract.tesseract_cmd = os.path.join(base_path, 'ocr', 'tesseract.exe')

# 设置 Tesseract OCR 的路径
regions = [[], [], [], [], [], [], [], [], [], []]
scaling_factor = get_scaling_factor()


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
        self.start_x = 0  # 添加初始化
        self.start_y = 0  # 添加初始化
        self.end_x = 0
        self.end_y = 0
        self.region = []

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

    def on_release(self, _):
        self.region = [
            min(self.start_x, self.end_x),
            min(self.start_y, self.end_y),
            abs(self.end_x - self.start_x),
            abs(self.end_y - self.start_y)
        ]
        self.region_selected = True
        self.canvas.delete("rectangle")  # 清除绘制的矩形
        self.root.destroy()  # 关闭区域选择窗口


def check_value_within_range(value, range_entry):
    range_text = range_entry.get()
    try:
        lower, upper = map(float, range_text.split(','))
        if lower <= value <= upper:
            return True
    except ValueError:
        pass
    return False


class ScreenshotApp:
    def __init__(self, root):
        self.root = root
        root.title("校验")
        root.geometry("520x630")
        self.display_textboxes = []
        self.range_entries = []  # 保存范围文本框的列表
        self.labels = []
        self.select_buttons = []
        labels = ['水温', '进气压力', '进气温度', '中冷后压力', '中冷后温度', '排气背压', '机油温度', 'a', 'b', 'c']
        for i in range(10):
            label = tk.Label(root, text=f"{labels[i]}:")
            display_textbox = ttk.Entry(root, state="readonly")  # 创建只读文本框用于显示识别内容
            range_entry = tk.Entry(root, width=10)  # 范围输入文本框
            select_button = tk.Button(root, text="选择截图区域", command=lambda index=i: self.select_area(index))
            label.grid(row=i, column=0, padx=(10, 0), pady=10, sticky="e")
            display_textbox.grid(row=i, column=1, padx=(0, 10), pady=10, sticky="w")
            range_entry.grid(row=i, column=2, padx=(0, 10), pady=10, sticky="w")
            select_button.grid(row=i, column=3, pady=10)
            self.labels.append(label)
            self.display_textboxes.append(display_textbox)
            self.range_entries.append(range_entry)
            self.select_buttons.append(select_button)
        # 模式选择的下拉菜单
        self.selected_mode = tk.StringVar()  # 下拉菜单选择的值
        self.mode_options = ["模式1", "模式2", "模式3", "模式4"]
        self.mode_dropdown = ttk.Combobox(root, textvariable=self.selected_mode, values=self.mode_options,
                                          state="readonly")
        self.mode_dropdown.grid(row=11, column=1, padx=(0, 10), pady=10, sticky="w")
        self.mode_dropdown.bind("<<ComboboxSelected>>", self.on_mode_change)

        # 定义各模式对应的范围数组
        self.options = {
            "模式1": [[0, 100], [0, 200], [0, 300], [0, 400], [0, 500], [0, 600], [0, 700], [], [], []],
            "模式2": [[0, 10], [0, 20], [0, 30], [0, 40], [0, 50], [0, 60], [0, 70], [], [], []],
            "模式3": [[0, 1], [0, 2], [0, 3], [0, 4], [0, 5], [0, 6], [0, 7], [], [], []],
            "模式4": [[0, 1000], [0, 2000], [0, 3000], [0, 4000], [0, 5000], [0, 6000], [0, 7000], [], [], []]
            # 为模式3和模式4同样定义范围数组
        }
        # 在“关闭”按钮旁边添加一个“导出数据”按钮
        self.export_button = tk.Button(root, text="导出数据", command=self.export_data)
        self.export_button.grid(row=11, column=2, pady=10)  # 确保按钮的位置正确
        self.close_button = tk.Button(root, text="关闭", command=self.on_close)
        self.close_button.grid(row=11, column=3, columnspan=4, pady=10)
        self.load_regions_from_file()
        threading.Thread(target=self.text_recognition_loop, daemon=True).start()

    def on_mode_change(self, event):
        """处理模式变更事件，更新范围文本框的值。"""
        mode = self.selected_mode.get()  # 获取当前选中的模式
        ranges = self.options[mode]  # 根据模式获取对应的范围数组

        # 遍历范围文本框列表，更新它们的内容
        for i, range_entry in enumerate(self.range_entries):
            if ranges[i]:  # 如果当前模式为该项定义了范围
                range_entry.delete(0, tk.END)  # 清除现有内容
                range_entry.insert(0, f"{ranges[i][0]},{ranges[i][1]}")  # 填入新的范围
            else:
                range_entry.delete(0, tk.END)  # 清除内容

    def on_close(self):
        self.save_regions_to_file()
        self.root.destroy()

    @staticmethod
    def save_regions_to_file():
        if regions:  # 检查regions列表是否不为空
            with open('regions.txt', 'w') as file:
                for region in regions:
                    if len(region) == 4:  # 确保每个区域都有4个坐标值
                        file.write(f"{region[0]},{region[1]},{region[2]},{region[3]}\n")
                    else:
                        print("发现不完整的区域数据，跳过写入。")
        else:
            print("没有要保存的区域坐标。")

    @staticmethod
    def load_regions_from_file():
        if os.path.exists('regions.txt'):
            with open('regions.txt', 'r') as file:
                lines = file.readlines()
                for i, line in enumerate(lines):
                    x, y, width, height = map(int, line.strip().split(','))
                    regions[i] = [x, y, width, height]

    # 定义导出数据的功能
    def export_data(self):
        workbook = Workbook()  # 创建一个新的工作簿
        sheet = workbook.active  # 获取当前活动的工作表
        # 添加标题行
        sheet.append(["标签", "识别内容", "范围"])
        # 遍历labels, display_textboxes和range_entries，将数据写入工作表
        for i in range(len(self.labels)):
            label = self.labels[i]['text']  # 获取标签文本
            content = self.display_textboxes[i].get()  # 获取显示文本框的内容
            range_text = self.range_entries[i].get()  # 获取范围文本框的内容
            sheet.append([label, content, range_text])  # 将数据添加到下一行
        # 保存工作簿到文件
        workbook.save("PUMA测试数据.xlsx")  # 将文件保存到当前目
        self.show_export_success_popup()

    @staticmethod
    def show_export_success_popup():
        # 使用tkinter的messagebox显示成功信息
        messagebox.showinfo("导出成功", "已完成导出")

    def select_area(self, index):
        self.root.after(0, lambda: self.trigger_select(index))

    def trigger_select(self, index):
        tool = TransparentScreenCaptureTool(tk.Toplevel(self.root))
        self.root.wait_window(tool.root)  # 等待用户完成区域选择
        if tool.region_selected:
            regions[index] = tool.region
            # 使用 ImageGrab.grab() 替换 pyautogui.screenshot()
            bbox = (tool.region[0], tool.region[1], tool.region[0] + tool.region[2], tool.region[1] + tool.region[3])
            adjusted_bbox = adjust_bbox_for_scaling(bbox, scaling_factor)
            screenshot = ImageGrab.grab(bbox=bbox)
            recognized_text = pytesseract.image_to_string(screenshot)
            filtered_text = filter_math_content(recognized_text)  # 过滤文本，仅保留数学内容
            self.set_display_textbox_content(index, filtered_text)
            # 释放截图对象占用的内存不再是必要的操作

    def set_display_textbox_content(self, index, content):
        self.display_textboxes[index].configure(state="normal")
        self.display_textboxes[index].delete(0, tk.END)
        self.display_textboxes[index].insert(0, content)
        self.display_textboxes[index].configure(state="readonly")

        # 检查数值是否在范围内
        try:
            value = float(content)
            if not check_value_within_range(value, self.range_entries[index]):
                self.flash_entry(self.range_entries[index])
            else:
                self.range_entries[index].configure(bg="white")
        except ValueError:
            pass

    def flash_entry(self, entry, times=5):
        current_color = entry.cget("bg")
        new_color = "red" if current_color == "white" else "white"
        entry.configure(bg=new_color)
        times -= 1
        if times > 0:
            self.root.after(500, lambda: self.flash_entry(entry, times))

    def text_recognition_loop(self):
        while True:
            time.sleep(1)  # 每1秒检查一次
            for i, region in enumerate(regions):
                if region:
                    bbox = (region[0], region[1], region[0] + region[2], region[1] + region[3])
                    adjusted_bbox = adjust_bbox_for_scaling(bbox, scaling_factor)
                    screenshot = ImageGrab.grab(bbox=bbox)
                    recognized_text = pytesseract.image_to_string(screenshot, config='--psm 6')
                    self.root.after(0, lambda index=i, text=recognized_text: self.set_display_textbox_content(index,
                                                                                                              filter_math_content(
                                                                                                                  text)))
                    # 释放截图对象占用的内存不再是必要的操作


def filter_math_content(text):
    # pattern = r"[-+]?[0-9]*\.?[0-9]+"
    # pattern = r"[-+]?\d*\.?\d+"
    pattern = r"[-−]?\d*\.?\d+"
    matches = re.findall(pattern, text)
    return ' '.join(matches)


def main():
    root = tk.Tk()
    ScreenshotApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
