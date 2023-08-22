import tkinter as tk
from tkinter import ttk
import logging
import re
import subprocess
import os
import platform
from controller import Controller
from threading import Thread
from PIL import Image, ImageTk


class SecurityCameraApp(tk.Tk):

    def __init__(self):
        super().__init__()

        # logging
        self.__logger = logging.getLogger("security_camera_logger")

        # basic app config
        self.__app_height = int(self.winfo_screenheight()) - 70
        self.__app_width = int(self.winfo_screenwidth())
        self.__gui_refresh_time = 1
        self.geometry("{}x{}+-7+0".format(self.__app_width, self.__app_height))
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.title('Security Camera')

        # cam
        self.cam_controller = Controller()
        self.surveillance_thread = None

        # utworzenie widgetów do zmiany parametrów

        self.settings_window = None

        # Tworzenie menu rozwijanego
        self.selected_mode = tk.StringVar()
        self.selected_mode.set("Rectangles")  # Ustawienie trybu na początku
        self.mode_label = tk.Label(self, text="Change camera mode:")
        self.mode_label.grid(row=1, column=0, padx=5, pady=5)
        self.mode_options = ["Standard", "Rectangles", "Contours", "High contrast", "Mexican hat", "Gray", "Sharpened"]
        self.mode_menu = tk.OptionMenu(self, self.selected_mode, *self.mode_options)
        self.mode_menu.grid(row=1, column=1, padx=5, pady=5)

        # przyciski
        buttons_frame = tk.Frame(self)
        self.start_button = tk.Button(buttons_frame, text="Start", command=self.run_surveillance_thread, width=30,
                                      height=2)
        self.stop_button = tk.Button(buttons_frame, text="Stop", command=self.kill_surveillance_thread, width=30,
                                     height=2)
        self.start_button.grid(row=0, column=0, pady=5, padx=5)
        self.stop_button.grid(row=1, column=0, pady=5, padx=5)

        self.settings_button = tk.Button(buttons_frame, text="Settings", command=self.open_settings_window,
                                         width=30, height=2)
        self.settings_button.grid(row=2, column=0, pady=5, padx=5)

        self.go_to_recordings_buttons = tk.Button(buttons_frame, text="Open recordings",
                                                  command=self.open_recordings_folder, width=30, height=2)
        self.go_to_recordings_buttons.grid(row=4, column=0, pady=5, padx=5)

        buttons_frame.grid(row=0, column=0, pady=10, padx=10, columnspan=2)

        # okno aplikacji
        canvas_frame = tk.Frame(self)
        canvas_frame.grid(row=0, column=3, rowspan=7)

        self.canvas = tk.Canvas(canvas_frame, width=self.__app_width, height=self.__app_height)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.start_time_label = tk.Label(self, text="Start hour (HH:MM):")
        self.start_time_label.grid(row=2, column=0, padx=5, pady=5)

        self.start_hour_picker = tk.ttk.Combobox(self, values=self.get_hour_range())
        self.start_hour_picker.grid(row=2, column=1, padx=5, pady=5)

        self.start_minute_picker = tk.ttk.Combobox(self, values=self.get_minute_range())
        self.start_minute_picker.grid(row=2, column=2, padx=5, pady=5)

        self.end_time_label = tk.Label(self, text="End hour (HH:MM):")
        self.end_time_label.grid(row=3, column=0, padx=5, pady=5)

        self.end_hour_picker = tk.ttk.Combobox(self, values=self.get_hour_range())
        self.end_hour_picker.grid(row=3, column=1, padx=5, pady=5)

        self.end_minute_picker = tk.ttk.Combobox(self, values=self.get_minute_range())
        self.end_minute_picker.grid(row=3, column=2, padx=5, pady=5)

        self.displayed_frame = None

        self.update_window()

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
            YesNoSetting(settings_window=self.settings_window,
                         initial_value="Yes" if self.cam_controller.send_system_notifications else "No",
                         label_text="Send system notifications:", row=9, column=0, padding=settings_padding))

        email_notifications_yesno_setting = (
            YesNoSetting(settings_window=self.settings_window,
                         initial_value="Yes" if self.cam_controller.send_email_notifications else "No",
                         label_text="Send email notifications:", row=10, column=0, padding=settings_padding))

        local_recordings_yesno_setting = (
            YesNoSetting(settings_window=self.settings_window,
                         initial_value="Yes" if self.cam_controller.save_recordings_locally else "No",
                         label_text="Save recordings locally:", row=11, column=0, padding=settings_padding))

        upload_to_gdrive_yesno_setting = (
            YesNoSetting(settings_window=self.settings_window,
                         initial_value="Yes" if self.cam_controller.upload_to_gdrive else "No",
                         label_text="Save recordings locally:", row=12, column=0, padding=settings_padding))

        # email entry
        email_label = tk.Label(self.settings_window, text="Email notifications recipient:")
        email_label.grid(row=8, column=0, padx=settings_padding, pady=settings_padding)

        email_entry = tk.Entry(self.settings_window, width=40)
        email_entry.grid(row=8, column=1, columnspan=2, padx=settings_padding, pady=settings_padding)

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
            self.cam_controller.min_delay_between_email_notifications = delay_between_email_notifications_scale_setting.get_value()

            # yes / no settings
            self.cam_controller.send_system_notifications = system_notifications_yesno_setting.get_value()
            self.cam_controller.send_email_notifications = email_notifications_yesno_setting.get_value()
            self.cam_controller.save_recordings_locally = local_recordings_yesno_setting.get_value()
            self.cam_controller.upload_to_gdrive = upload_to_gdrive_yesno_setting.get_value()

            # email entry
            update_email(email_entry)

            # updating parameters
            self.cam_controller.update_parameters()

        apply_settings_button = tk.Button(self.settings_window, text="Apply", command=apply_settings,
                                          width=30, height=1)
        apply_settings_button.grid(row=13, column=0, columnspan=3, padx=200, pady=30, sticky="ew")

        # disabling settings window
        self.settings_window = None

    def update_mode(self):
        # Wywołanie zmiany trybu obrazu po wybraniu nowej opcji z menu rozwijanego
        self.update_window()

    @staticmethod
    def get_hour_range():
        return [f"{hour:02d}" for hour in range(24)]

    @staticmethod
    def get_minute_range():
        return [f"{minute:02d}" for minute in range(60)]

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

    # def check_schedule(self):
    #     current_time = datetime.datetime.now().time()
    #     start_time_str = self.start_time_entry.get()
    #     end_time_str = self.end_time_entry.get()
    #
    #     try:
    #         start_time = datetime.datetime.strptime(start_time_str, "%H:%M").time()
    #         end_time = datetime.datetime.strptime(end_time_str, "%H:%M").time()
    #
    #         if start_time <= current_time <= end_time:
    #             self.run_surveillance_thread()
    #             self.title("Camera window - Active")
    #         else:
    #             self.kill_surveillance_thread()
    #             self.title("Camera window - Inactive")
    #
    #     except ValueError:
    #         self.kill_surveillance_thread()
    #         self.title("Camera window - Inactive")
    #
    #     self.after(60000, self.check_schedule)  # Sprawdzanie co minutę

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

            frame = modes[self.selected_mode.get()]()

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


class YesNoSetting:
    def __init__(self, settings_window, initial_value, label_text, row, column, padding):
        self.var = tk.StringVar(value=initial_value)

        self.label = tk.ttk.Label(master=settings_window, text=label_text)

        self.menu = tk.OptionMenu(settings_window, self.var, *("Yes", "No"))

        self.arrange(row, column, padding)

    def arrange(self, row, column, padding):
        self.label.grid(row=row, column=column, padx=padding, pady=padding)
        self.menu.grid(row=row, column=column + 1, padx=padding, pady=padding)

    def get_value(self):
        return self.var.get() == "Yes"
