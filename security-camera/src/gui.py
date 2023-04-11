import tkinter as tk
from controller import Controller
from threading import *
from PIL import Image, ImageTk


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.cam_controller = Controller()
        self.monitoring_thread = None
        
        self.title('title')
        self.app_height=600
        self.app_width=1200
        self.screen_height=self.winfo_screenheight()
        self.screen_width=self.winfo_screenwidth()
        self.x_cordinate=int((self.screen_width/2)-(self.app_width/2))
        self.y_cordinate=int((self.screen_height/2)-(self.app_height/2))
        self.refresh_time = 100

        self.geometry("{}x{}+{}+{}".format(self.app_width, self.app_height, self.x_cordinate, self.y_cordinate))

        self.start_button=tk.Button(self, text="Start", command=self.run_monitoring_thread)
        self.stop_button=tk.Button(self,text="Stop", command=self.kill_monitoring_thread)

        self.start_button.pack()
        self.stop_button.pack()

        self.update_window()

    def run_monitoring_thread(self):
        self.monitoring_thread = Thread(target=self.cam_controller.start_monitoring)
        self.monitoring_thread.start()

    def kill_monitoring_thread(self):
        self.cam_controller.monitoring = False
        self.cam_controller.cam.destroy()
        # ???

    def update_window(self):
        self.after(self.refresh_time, self.update_window)