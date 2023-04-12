import tkinter as tk
from controller import Controller
from threading import *
from PIL import Image, ImageTk


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.cam_controller = Controller(refresh_time=10, emergency_recording_length=5, standard_recording_length=15,
                                         emergency_buff_size=70, detection_sensitivity=12, max_detection_sensitivity=15,
                                         min_motion_rectangle_area=1000)
        self.surveillance_thread = None

        self.title('title')
        self.app_height = 1000
        self.app_width = 1400
        self.screen_height = self.winfo_screenheight()
        self.screen_width = self.winfo_screenwidth()
        self.x_coordinate = int((self.screen_width / 2) - (self.app_width / 2))
        self.y_coordinate = int((self.screen_height / 2) - (self.app_height / 2))
        self.refresh_time = 30

        self.geometry("{}x{}+{}+{}".format(self.app_width, self.app_height, self.x_coordinate, self.y_coordinate))

        self.start_button = tk.Button(self, text="Start", command=self.run_surveillance_thread, width=80, height=5)
        self.stop_button = tk.Button(self, text="Stop", command=self.kill_surveillance_thread, width=80, height=5)

        self.start_button.pack()
        self.stop_button.pack()

        self.canvas = tk.Canvas(self, width=1000,
                                height=1000)
        self.canvas.pack()

        self.photo = None

        self.update_window()

    def run_surveillance_thread(self):
        self.surveillance_thread = Thread(target=self.cam_controller.start_surveillance)
        self.surveillance_thread.start()

    def kill_surveillance_thread(self):
        self.cam_controller.surveillance_running = False
        self.cam_controller.cam.destroy()
        # ???

    def update_window(self):
        if self.cam_controller.surveillance_running:
            frame = self.cam_controller.cam.get_standard_frame()
            if frame is not None:
                self.photo = ImageTk.PhotoImage(image=Image.fromarray(frame))
                self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

        self.after(self.refresh_time, self.update_window)
