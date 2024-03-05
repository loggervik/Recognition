import tkinter as tk


class TransparentScreenCaptureTool:
    def __init__(self, root):
        self.root = root
        root.title("透明屏幕截图工具")
        root.attributes('-fullscreen', True)  # 设置窗口全屏显示
        root.attributes('-alpha', 0.5)  # 设置窗口透明度
        # Variables to store the coordinates of the four points
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        # Create a transparent canvas for selection
        self.canvas = tk.Canvas(root, bg="white", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        # Bind mouse events for selection
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        # Initialize region variable
        self.region = None

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y

    def on_drag(self, event):
        self.end_x = event.x
        self.end_y = event.y
        # Update the selection rectangle
        self.canvas.delete("rectangle")
        self.canvas.create_rectangle(self.start_x, self.start_y, self.end_x, self.end_y, outline="red",
                                     tags="rectangle")

    def on_release(self, event):
        # Print the coordinates of the four points
        print("Start Point:", (self.start_x, self.start_y))
        print("Width:", self.end_x - self.start_x)
        print("Height:", self.end_y - self.start_y)
        # Calculate region
        self.region = [self.start_x, self.start_y, self.end_x - self.start_x, self.end_y - self.start_y]
        # Close the window after printing the information
        self.root.destroy()


def select():
    root = tk.Tk()
    app = TransparentScreenCaptureTool(root)
    root.mainloop()
    return app.region


if __name__ == '__main__':
    select()
