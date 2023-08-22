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

        self.selected_mode = tk.StringVar()
        self.selected_mode.set("Rectangles")  # Ustawienie trybu na początku

        # Tworzenie menu rozwijanego
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
        self.settings_window.title("Settings")

        # def update_email(_):
        #     email = email_entry.get()
        #     if validate_email(email):
        #         self.cam_controller.email_recipient = email
        #         self.cam_controller.update_parameters()
        #         self.__logger.info("updated recipient email to: " + email)
        #     else:
        #         self.__logger.warning("recipient email not updated - wrong email: " + email)

        def validate_email(email):
            pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
            return re.match(pattern, email) is not None

        def update_system_notification(value):
            if value == "Yes":
                self.send_system_notifications = self.cam_controller.send_system_notifications = True

            elif value == "No":
                self.send_system_notifications = self.cam_controller.send_system_notifications = False
            self.cam_controller.update_parameters()

        def update_email_notification(value):
            if value == "Yes":
                self.send_email_notifications = self.cam_controller.send_email_notifications = True
            elif value == "No":
                self.send_email_notifications = self.cam_controller.send_email_notifications = False
            self.cam_controller.update_parameters()

        def update_local_saving(value):
            if value == "Yes":
                self.save_recordings_locally = self.cam_controller.save_recordings_locally = True
            elif value == "No":
                self.save_recordings_locally = self.cam_controller.save_recordings_locally = False
            self.cam_controller.update_parameters()

        def update_gdrive_saving(value):
            if value == "Yes":
                self.upload_to_gdrive = self.cam_controller.upload_to_gdrive = True
            elif value == "No":
                self.upload_to_gdrive = self.cam_controller.upload_to_gdrive = False
            self.cam_controller.update_parameters()

        '''scale settings'''

        recording_fps_scale_setting = (
            ScaleSetting(settings_window=self.settings_window, initial_value=self.cam_controller.fps, min_value=1,
                         max_value=60, scale_length=200, row=0, column=0, padding=5, label_text="Recording fps:"))

        emergency_recording_length_scale_setting = (
            ScaleSetting(settings_window=self.settings_window,
                         initial_value=self.cam_controller.emergency_recording_length, min_value=1, max_value=30,
                         scale_length=200, row=1, column=0, padding=5, label_text="Length of emergency recording:"))

        standard_recording_length_scale_setting = (
            ScaleSetting(settings_window=self.settings_window,
                         initial_value=self.cam_controller.standard_recording_length, min_value=1, max_value=300,
                         scale_length=200, row=2, column=0, padding=5, label_text="Length of standard recording:"))

        emergency_buff_length_scale_setting = (
            ScaleSetting(settings_window=self.settings_window, initial_value=self.cam_controller.emergency_buff_length,
                         min_value=1, max_value=60, scale_length=200, row=3, column=0, padding=5,
                         label_text="Length of emergency buffer:"))

        detection_sensitivity_scale_setting = (
            ScaleSetting(settings_window=self.settings_window, initial_value=self.cam_controller.detection_sensitivity,
                         min_value=1, max_value=self.cam_controller.max_detection_sensitivity, scale_length=200, row=4,
                         column=0, padding=5, label_text="Detection sensitivity:"))

        min_motion_area_var_scale_setting = (
            ScaleSetting(settings_window=self.settings_window,
                         initial_value=self.cam_controller.min_motion_rectangle_area, min_value=10, max_value=5000,
                         scale_length=200, row=5, column=0, padding=5, label_text="Minimal motion area:"))

        delay_between_system_notifications_scale_setting = (
            ScaleSetting(settings_window=self.settings_window,
                         initial_value=self.cam_controller.min_delay_between_system_notifications, min_value=5,
                         max_value=600, scale_length=200, row=6, column=0, padding=5,
                         label_text="Delay between system notifications:"))

        delay_between_email_notifications_scale_setting = (
            ScaleSetting(settings_window=self.settings_window,
                         initial_value=self.cam_controller.min_delay_between_email_notifications,
                         min_value=5, max_value=600, scale_length=200, row=7, column=0, padding=5,
                         label_text="Delay between email notifications:"))


        # # system notifications approval
        # notification_label = tk.Label(self.settings_window, text="Do you want to recieve system notifications:")
        # notification_label.grid(row=8, column=0, padx=5, pady=5)
        # notification_var = tk.StringVar(value="Yes" if self.cam_controller.send_system_notifications else "No")
        # notification_menu = tk.OptionMenu(self.settings_window, notification_var, "Yes", "No",
        #                                   command=update_system_notification)
        # notification_menu.grid(row=8, column=1, padx=5, pady=5)
        #
        # # email notifications approval
        # notification_label2 = tk.Label(self.settings_window, text="Do you want to recieve mail notifications:")
        # notification_label2.grid(row=2, column=0, padx=5, pady=5)
        # notification_var2 = tk.StringVar(value="Yes" if self.cam_controller.send_email_notifications else "No")
        # notification_menu2 = tk.OptionMenu(self.settings_window, notification_var2, "Yes", "No",
        #                                    command=update_email_notification)
        # notification_menu2.grid(row=2, column=1, padx=5, pady=5)
        #
        # # email
        # email_label = tk.Label(self.settings_window, text="Notifications mail:")
        # email_label.grid(row=0, column=0, padx=5, pady=5)
        #
        # email_entry = tk.Entry(self.settings_window)
        #
        # email_entry.grid(row=0, column=1, padx=5, pady=5)
        # email_entry.bind("<KeyRelease>", update_email)
        #
        # # local recordings
        # local_recordings = tk.Label(self.settings_window, text="Do you want to save recordings locally:")
        # local_recordings.grid(row=3, column=0, padx=5, pady=5)
        # save_locally = tk.StringVar(value="Yes" if self.cam_controller.save_recordings_locally else "No")
        # local_save = tk.OptionMenu(self.settings_window, save_locally, "Yes", "No",
        #                            command=update_local_saving)
        # local_save.grid(row=3, column=1, padx=5, pady=5)
        #
        # # upload to cloud
        # gdrive_savings = tk.Label(self.settings_window, text="Do you want to save recordings on Google Drive:")
        # gdrive_savings.grid(row=4, column=0, padx=5, pady=5)
        # save_gdrive = tk.StringVar(value="Yes" if self.cam_controller.upload_to_gdrive else "No")
        # gdrive_save = tk.OptionMenu(self.settings_window, save_gdrive, "Yes", "No",
        #                             command=update_gdrive_saving)
        # gdrive_save.grid(row=4, column=1, padx=5, pady=5)

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

        self.label = tk.ttk.Label(settings_window, text=label_text)

        self.scale = tk.ttk.Scale(settings_window, from_=min_value, to=max_value, variable=self.var,
                                  length=scale_length, orient=tk.HORIZONTAL,
                                  command=lambda value: self.value_label.configure(text=round(float(value), 0)))

        self.value_label = tk.ttk.Label(settings_window, text=self.var.get())

        self.arrange(row, column, padding)

    def arrange(self, row, column, padding):
        self.label.grid(row=row, column=column, padx=padding, pady=padding)
        self.scale.grid(row=row, column=column + 1, padx=padding, pady=padding, sticky="W")
        self.value_label.grid(row=row, column=column + 2, padx=padding, pady=padding)
