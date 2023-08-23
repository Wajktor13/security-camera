import tkinter as tk
import logging
import re
import subprocess
import os
import platform
from tkinter import ttk
from controller import Controller
from threading import Thread
from PIL import Image, ImageTk


class SecurityCameraApp(tk.Tk):

    def __init__(self):
        super().__init__()

        # logging
        self.__logger = logging.getLogger("security_camera_logger")

        # cam and surveillance
        self.cam_controller = Controller()
        self.surveillance_thread = None

        ''' gui '''
        # basic
        self.__app_height = int(self.winfo_screenheight()) - 70
        self.__app_width = int(self.winfo_screenwidth())
        self.__gui_refresh_time = 1
        self.displayed_frame = None
        self.geometry("{}x{}+-7+0".format(self.__app_width, self.__app_height))
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.title('Security Camera')
        self.option_add("*tearOff", False)

        # theme
        self.style = ttk.Style()
        self.tk.call("source", "../tkinter_theme/forest-dark.tcl")
        self.style.theme_use("forest-dark")
        self.main_font = "Arial 14"
        self.option_add("*Font", self.main_font)
        self.style.configure("TButton", font=self.main_font)
        self.style.configure("Custom.TMenubutton", font=self.main_font)

        # canvas
        canvas_frame = ttk.Frame(self)
        canvas_frame.grid(row=0, column=3, rowspan=7)

        self.canvas = tk.Canvas(canvas_frame, width=self.__app_width, height=self.__app_height)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # image mode dropdown
        self.image_mode_var = self.create_image_mode_dropdown()

        # settings window
        self.settings_window = None

        # buttons
        self.create_buttons()

        # cyclic window update
        self.update_window()

    def create_image_mode_dropdown(self):
        image_mode_var = tk.StringVar()
        image_mode_var.set("Rectangles")
        image_mode_label = ttk.Label(self, text="Camera mode:")
        image_mode_label.grid(row=1, column=0, padx=5, pady=5)
        image_mode_options = ["Standard", "Standard              ", "Rectangles", "Contours", "High contrast",
                              "Mexican hat", "Gray", "Sharpened"]
        image_mode_menu = ttk.OptionMenu(self, image_mode_var, *image_mode_options, style="Custom.TMenubutton")
        image_mode_menu.config(width=15)
        image_mode_menu.grid(row=1, column=1, padx=5, pady=5)

        return image_mode_var

    def create_buttons(self):
        button_width = 30
        button_padding = 6

        # buttons frame
        buttons_frame = ttk.Frame(self)

        # start button
        start_button = ttk.Button(buttons_frame, text="Start surveillance", style='Accent.TButton',
                                  command=self.run_surveillance_thread, width=button_width)
        start_button.grid(row=0, column=0, pady=button_padding, padx=button_padding)
        # stop button
        stop_button = ttk.Button(buttons_frame, text="Stop surveillance", style='Accent.TButton',
                                 command=self.kill_surveillance_thread, width=button_width)
        stop_button.grid(row=1, column=0, pady=button_padding, padx=button_padding)

        # settings button
        settings_button = ttk.Button(buttons_frame, text="Settings", style='Accent.TButton',
                                     command=self.open_settings_window, width=button_width)
        settings_button.grid(row=2, column=0, pady=button_padding, padx=button_padding)

        # go to recordings button
        go_to_recordings_buttons = ttk.Button(buttons_frame, text="Open recordings directory", style='Accent.TButton',
                                              command=self.open_recordings_folder, width=button_width)
        go_to_recordings_buttons.grid(row=4, column=0, pady=button_padding, padx=button_padding)

        # place frame
        buttons_frame.grid(row=0, column=0, pady=10, padx=10, columnspan=2)

    def open_settings_window(self):
        if self.settings_window is not None:
            return

        self.settings_window = tk.Toplevel(self)
        self.settings_window.title("Security Camera Settings")
        self.settings_window.resizable(False, False)

        # scale settings
        settings_padding = 10
        scale_length = 280

        recording_fps_scale_setting = (
            ScaleSetting(settings_window=self.settings_window, initial_value=self.cam_controller.fps, min_value=1,
                         max_value=60, scale_length=scale_length, row=0, column=0, padding=settings_padding,
                         label_text="Recording fps:"))

        emergency_recording_length_scale_setting = (
            ScaleSetting(settings_window=self.settings_window,
                         initial_value=self.cam_controller.emergency_recording_length, min_value=1, max_value=30,
                         scale_length=scale_length, row=1, column=0, padding=settings_padding,
                         label_text="Length of emergency recording:"))

        standard_recording_length_scale_setting = (
            ScaleSetting(settings_window=self.settings_window,
                         initial_value=self.cam_controller.standard_recording_length, min_value=1, max_value=300,
                         scale_length=scale_length, row=2, column=0, padding=settings_padding,
                         label_text="Length of standard recording:"))

        emergency_buff_length_scale_setting = (
            ScaleSetting(settings_window=self.settings_window, initial_value=self.cam_controller.emergency_buff_length,
                         min_value=1, max_value=60, scale_length=scale_length, row=3, column=0,
                         padding=settings_padding, label_text="Length of emergency buffer:"))

        detection_sensitivity_scale_setting = (
            ScaleSetting(settings_window=self.settings_window, initial_value=self.cam_controller.detection_sensitivity,
                         min_value=1, max_value=self.cam_controller.max_detection_sensitivity,
                         scale_length=scale_length, row=4, column=0, padding=settings_padding,
                         label_text="Detection sensitivity:"))

        min_motion_area_var_scale_setting = (
            ScaleSetting(settings_window=self.settings_window,
                         initial_value=self.cam_controller.min_motion_rectangle_area, min_value=10, max_value=5000,
                         scale_length=scale_length, row=5, column=0, padding=settings_padding,
                         label_text="Minimal motion area:"))

        delay_between_system_notifications_scale_setting = (
            ScaleSetting(settings_window=self.settings_window,
                         initial_value=self.cam_controller.min_delay_between_system_notifications, min_value=5,
                         max_value=600, scale_length=scale_length, row=6, column=0, padding=settings_padding,
                         label_text="Delay between system notifications:"))

        delay_between_email_notifications_scale_setting = (
            ScaleSetting(settings_window=self.settings_window,
                         initial_value=self.cam_controller.min_delay_between_email_notifications,
                         min_value=5, max_value=600, scale_length=scale_length, row=7, column=0,
                         padding=settings_padding, label_text="Delay between email notifications:"))

        # yes / no settings
        system_notifications_yesno_setting = (
            CheckbuttonSetting(settings_window=self.settings_window,
                               initial_value=self.cam_controller.send_system_notifications,
                               label_text="Send system notifications:", row=9, column=0, padding=settings_padding))

        email_notifications_yesno_setting = (
            CheckbuttonSetting(settings_window=self.settings_window,
                               initial_value=self.cam_controller.send_email_notifications,
                               label_text="Send email notifications:", row=10, column=0, padding=settings_padding))

        local_recordings_yesno_setting = (
            CheckbuttonSetting(settings_window=self.settings_window,
                               initial_value=self.cam_controller.save_recordings_locally,
                               label_text="Save recordings locally:", row=11, column=0, padding=settings_padding))

        upload_to_gdrive_yesno_setting = (
            CheckbuttonSetting(settings_window=self.settings_window,
                               initial_value=self.cam_controller.upload_to_gdrive,
                               label_text="Upload recordings to google drive:", row=12, column=0,
                               padding=settings_padding))

        # email entry
        email_entry_var = tk.StringVar(value=self.cam_controller.email_recipient)

        email_label = ttk.Label(self.settings_window, text="Email notifications recipient:")
        email_label.grid(row=8, column=0, padx=settings_padding, pady=settings_padding)

        email_entry = tk.Entry(self.settings_window, width=28, textvariable=email_entry_var, font=self.main_font)
        email_entry.grid(row=8, column=1, columnspan=1, padx=(0, 10), pady=settings_padding)

        # apply settings button
        def update_email(entry):
            email = entry.get()
            if validate_email(email):
                self.cam_controller.email_recipient = email
                self.__logger.info("updated recipient email to: " + email)
            else:
                self.__logger.warning("recipient email not updated - wrong email: " + email)

        def validate_email(email):
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return re.match(pattern, email)

        def apply_settings():
            # scale settings
            self.cam_controller.fps = recording_fps_scale_setting.get_value()
            self.cam_controller.emergency_recording_length = emergency_recording_length_scale_setting.get_value()
            self.cam_controller.standard_recording_length = standard_recording_length_scale_setting.get_value()
            self.cam_controller.emergency_buff_length = emergency_buff_length_scale_setting.get_value()
            self.cam_controller.detection_sensitivity = detection_sensitivity_scale_setting.get_value()
            self.cam_controller.min_motion_rectangle_area = min_motion_area_var_scale_setting.get_value()
            self.cam_controller.min_delay_between_system_notifications = (
                delay_between_system_notifications_scale_setting.get_value())
            self.cam_controller.min_delay_between_email_notifications = (
                delay_between_email_notifications_scale_setting.get_value())

            # yes / no settings
            self.cam_controller.send_system_notifications = system_notifications_yesno_setting.get_value()
            self.cam_controller.send_email_notifications = email_notifications_yesno_setting.get_value()
            self.cam_controller.save_recordings_locally = local_recordings_yesno_setting.get_value()
            self.cam_controller.upload_to_gdrive = upload_to_gdrive_yesno_setting.get_value()

            # email entry
            update_email(email_entry)

            # updating parameters
            self.cam_controller.update_parameters()

            # saving parameters to JSON
            self.cam_controller.controller_settings_manager.save_settings(self.cam_controller)

        apply_settings_button = ttk.Button(self.settings_window, text="Apply", style='Accent.TButton',
                                           command=apply_settings, width=30)
        apply_settings_button.grid(row=13, column=0, columnspan=3, padx=200, pady=30, sticky="ew")

        # disabling settings window
        self.settings_window = None

    def run_surveillance_thread(self):
        self.surveillance_thread = Thread(target=self.cam_controller.start_surveillance)
        self.__logger.info("surveillance thread started")
        self.surveillance_thread.start()

    def kill_surveillance_thread(self):
        if self.cam_controller.cam is not None:
            self.cam_controller.surveillance_running = False
            self.cam_controller.cam.destroy()
        self.cam_controller.controller_settings_manager.save_settings(self.cam_controller)
        self.__logger.info("surveillance thread stopped")

    def on_closing(self):
        self.kill_surveillance_thread()
        self.destroy()

    def update_window(self):
        if self.cam_controller.surveillance_running and self.cam_controller.cam is not None:
            cam = self.cam_controller.cam
            modes = {"Rectangles": cam.get_frame_with_rectangles,
                     "Contours": cam.get_frame_with_contours,
                     "High contrast": cam.get_high_contrast_frame,
                     "Mexican hat": cam.get_mexican_hat_effect_frame,
                     "Sharpened": cam.get_sharpened_frame,
                     "Gray": cam.get_gray_frame,
                     "Standard": cam.get_standard_frame}

            try:
                frame = modes[self.image_mode_var.get()]()
            except KeyError:
                frame = cam.get_standard_frame()

            if frame is not None:
                self.displayed_frame = ImageTk.PhotoImage(image=Image.fromarray(frame))
                self.canvas.create_image(0, 0, image=self.displayed_frame, anchor=tk.NW)

        self.after(self.__gui_refresh_time, self.update_window)

    @staticmethod
    def open_recordings_folder():
        path = os.path.realpath("../recordings")

        if platform.system() == 'Windows':
            subprocess.Popen(["explorer", path])
        else:
            subprocess.Popen(["xdg-open", path])


class ScaleSetting:
    def __init__(self, settings_window, initial_value, min_value, max_value, scale_length, row, column, padding,
                 label_text):
        self.var = tk.DoubleVar(value=initial_value)

        self.label = tk.ttk.Label(master=settings_window, text=label_text)

        self.scale = tk.ttk.Scale(master=settings_window, from_=min_value, to=max_value, variable=self.var,
                                  length=scale_length, orient=tk.HORIZONTAL,
                                  command=lambda value: self.value_label.configure(text=round(float(value), 0)))

        self.value_label = tk.ttk.Label(master=settings_window, text=self.var.get())

        self.arrange(row, column, padding)

    def arrange(self, row, column, padding):
        self.label.grid(row=row, column=column, padx=padding, pady=padding)
        self.scale.grid(row=row, column=column + 1, padx=padding, pady=padding, sticky="W")
        self.value_label.grid(row=row, column=column + 2, padx=padding, pady=padding)

    def get_value(self):
        return round(float(self.var.get()), 0)


class CheckbuttonSetting:
    def __init__(self, settings_window, initial_value, label_text, row, column, padding):
        self.var = tk.BooleanVar(value=initial_value)

        self.label = tk.ttk.Label(master=settings_window, text=label_text)

        self.menu = ttk.Checkbutton(master=settings_window, variable=self.var)

        self.arrange(row, column, padding)

    def arrange(self, row, column, padding):
        self.label.grid(row=row, column=column, padx=padding, pady=padding)
        self.menu.grid(row=row, column=column + 1, padx=padding, pady=padding)

    def get_value(self):
        return self.var.get()
