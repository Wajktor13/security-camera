import tkinter as tk
import logging
import re
import time
import datetime
import subprocess
import os
import platform
from tkinter import ttk
from controller import Controller
from threading import Thread
from PIL import Image, ImageTk


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # logging
        self.__logger = logging.getLogger("security_camera_logger")

        self.cam_controller = Controller(refresh_time=10, emergency_recording_length=10, standard_recording_length=180,
                                         emergency_buff_length=4, detection_sensitivity=12,
                                         max_detection_sensitivity=15, min_motion_rectangle_area=100, fps=24,
                                         camera_number=0, send_system_notifications=True,
                                         min_delay_between_system_notifications=30, send_email_notifications=False,
                                         min_delay_between_email_notifications=240,
                                         email_recipient="wajktor007@gmail.com", upload_to_gdrive=False)
        self.surveillance_thread = None
        self.title('Camera window')
        self.app_height = int(self.winfo_screenheight()) - 70
        self.app_width = int(self.winfo_screenwidth())
        self.__gui_refresh_time = 1

        self.geometry("{}x{}+-7+0".format(self.app_width, self.app_height))
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        ## utworzenie widgetów do zmiany parametrów

        self.settings_window = None

        self.selected_mode = tk.StringVar()
        self.selected_mode.set("Rectangles")  # Ustawienie trybu na początku

        # Tworzenie menu rozwijanego
        self.mode_label = tk.Label(self, text="Change camera mode:")
        self.mode_label.grid(row=1, column=0, padx=5, pady=5)
        self.mode_options = ["Standard", "Rectangles", "Contours", "High contrast", "Mexican hat", "Szarość",
                             "Sharpened"]
        self.mode_menu = tk.OptionMenu(self, self.selected_mode, *self.mode_options)
        self.mode_menu.grid(row=1, column=1, padx=5, pady=5)

        self.email_label = tk.Label(self, text="Notifications mail:")
        self.email_label.grid(row=2, column=0, padx=5, pady=5)

        self.email_entry = tk.Entry(self)

        self.email_entry.grid(row=2, column=1, padx=5, pady=5)
        self.email_entry.bind("<Return>", self.update_email)

        self.notification_label = tk.Label(self, text="Do you want to recieve system notifications:")
        self.notification_label.grid(row=3, column=0, padx=5, pady=5)
        self.notification_var = tk.StringVar(value="Yes" if self.cam_controller.send_system_notifications else "No")
        self.notification_menu = tk.OptionMenu(self, self.notification_var, "Yes", "No",
                                               command=self.update_system_notification)
        self.notification_menu.grid(row=3, column=1, padx=5, pady=5)

        self.notification_label2 = tk.Label(self, text="Do you want to recieve mail notifications:")
        self.notification_label2.grid(row=4, column=0, padx=5, pady=5)
        self.notification_var2 = tk.StringVar(value="Yes" if self.cam_controller.send_email_notifications else "No")
        self.notification_menu2 = tk.OptionMenu(self, self.notification_var2, "Yes", "No",
                                                command=self.update_email_notification)
        self.notification_menu2.grid(row=4, column=1, padx=5, pady=5)

        ## przyciski
        buttons_frame = tk.Frame(self)
        self.start_button = tk.Button(buttons_frame, text="Start", command=self.run_surveillance_thread, width=30, height=2)
        self.stop_button = tk.Button(buttons_frame, text="Stop", command=self.kill_surveillance_thread, width=30, height=2)
        self.start_button.grid(row=0, column=0, pady=5, padx=5)
        self.stop_button.grid(row=1, column=0, pady=5, padx=5)

        self.settings_button = tk.Button(buttons_frame, text="Camera settings", command=self.open_settings_window, width=30, height=2)
        self.settings_button.grid(row=2, column=0, pady=5, padx=5)

        self.go_to_recordings_buttons = tk.Button(buttons_frame, text="Open recordings",
                                                  command=self.open_recordings_folder, width=30, height=2)
        self.go_to_recordings_buttons.grid(row=3, column=0, pady=5, padx=5)

        buttons_frame.grid(row=0, column=0, pady=10, padx=10, columnspan=2)


        ## okno aplikacji
        canvas_frame = tk.Frame(self)
        canvas_frame.grid(row=0, column=2, rowspan=7)

        self.canvas = tk.Canvas(canvas_frame, width=self.app_width, height=self.app_height)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.start_time_label = tk.Label(self, text="Start hour (HH:MM):")
        self.start_time_label.grid(row=5, column=0, padx=5, pady=5)

        self.start_time_entry = tk.Entry(self)
        self.start_time_entry.grid(row=5, column=1, padx=5, pady=5)

        self.end_time_label = tk.Label(self, text="End hour (HH:MM):")
        self.end_time_label.grid(row=6, column=0, padx=5, pady=5)

        self.end_time_entry = tk.Entry(self)
        self.end_time_entry.grid(row=6, column=1, padx=5, pady=5)
        # self.check_schedule()

        self.photo = None

        self.update_window()


    def open_settings_window(self):
        if self.settings_window is not None:
            return

        self.settings_window = tk.Toplevel(self)
        self.settings_window.title("Settings")

            ## funckja do uzyskiwania aktualnej wartości suwaka
        def show_scale_value_emergency( value):
            rounded_value = round(float(value), 0)
            scale_value_emergency_label.configure(text=rounded_value)
            self.cam_controller.emergency_recording_length = int(emergency_recording_length_scale.get())
            self.cam_controller.update_parameters()

        def show_scale_value_refresh( value):
            rounded_value = round(float(value), 0)
            scale_value_refresh_label.configure(text=rounded_value)
            self.cam_controller.fps = int(refresh_time_scale.get())
            self.cam_controller.update_parameters()

        def show_scale_value_buffer( value):
            rounded_value = round(float(value), 0)
            scale_value_buffer_label.configure(text=rounded_value)
            self.cam_controller.emergency_buff_length = int(emergency_buff_size_scale.get())
            self.cam_controller.update_parameters()

        def show_scale_value_rect( value):
            rounded_value = round(float(value), 0)
            scale_value_rect_label.configure(text=rounded_value)
            self.cam_controller.min_motion_rectangle_area = int(min_motion_rectangle_area_scale.get())
            self.cam_controller.update_parameters()

        def show_scale_value_sens( value):
            rounded_value = round(float(value), 0)
            scale_value_sens_label.configure(text=rounded_value)
            self.cam_controller.detection_sensitivity = int(detection_sensitivity_scale.get())
            self.cam_controller.update_parameters()

        def show_scale_value_standard( value):
            rounded_value = round(float(value), 0)
            scale_value_standard_label.configure(text=rounded_value)
            self.cam_controller.standard_recording_length = int(standard_recording_length_scale.get())
            self.cam_controller.update_parameters()

        def show_min_delay( value):
            rounded_value = round(float(value), 0)
            scale_delay_value_label.configure(text=rounded_value)
            self.cam_controller.min_delay_between_system_notifications = \
                int(min_delay_between_system_notifications_scale.get())
            self.cam_controller.update_parameters()

        def show_min_delay_mail( value):
            rounded_value = round(float(value), 0)
            scale_delay_mail_value_label.configure(text=rounded_value)
            self.cam_controller.min_delay_between_email_notifications =\
                int(min_delay_between_email_notifications_scale.get())
            self.cam_controller.update_parameters()

        # Tworzenie widgetów suwaków w oknie ustawień
        ## zmiana częstotliwości odświeżania
        refresh_time_var = tk.DoubleVar(value=self.cam_controller.fps)
        
        refresh_time_scale = ttk.Scale(self.settings_window, from_=1, to=60,
                                            variable=refresh_time_var,
                                            length=200, orient=tk.HORIZONTAL, command=show_scale_value_refresh)
        refresh_time_scale.grid(row=0, column=1, padx=5, pady=5)
        refresh_time_label = ttk.Label(self.settings_window, text="Refresh rate:")
        refresh_time_label.grid(row=0, column=0, padx=5, pady=5)
        scale_value_refresh_label = ttk.Label(self.settings_window, text=refresh_time_var.get())
        scale_value_refresh_label.grid(row=0, column=2, padx=5, pady=5)

        ## zmiana długości nagrywania awaryjnego
        emergency_recording_length_var = tk.DoubleVar(value=self.cam_controller.emergency_recording_length)
        emergency_recording_length_scale = ttk.Scale(self.settings_window, from_=1, to=30,
                                                          variable=emergency_recording_length_var,
                                                          length=200, orient=tk.HORIZONTAL,
                                                          command=show_scale_value_emergency)
        emergency_recording_length_scale.grid(row=1, column=1, padx=5, pady=5)
        emergency_recording_length_label = ttk.Label(self.settings_window, text="Lenght of emergency recording:")
        emergency_recording_length_label.grid(row=1, column=0, padx=5, pady=5)
        scale_value_emergency_label = ttk.Label(self.settings_window, text=emergency_recording_length_var.get())
        scale_value_emergency_label.grid(row=1, column=2, padx=5, pady=5)

        ## zmiana długości nagrania standardowego
        standard_recording_length_var = tk.DoubleVar(value=self.cam_controller.standard_recording_length)

        standard_recording_length_scale = ttk.Scale(self.settings_window, from_=1, to=250,
                                                         variable=standard_recording_length_var,
                                                         length=200, orient=tk.HORIZONTAL,
                                                         command=show_scale_value_standard)
        standard_recording_length_scale.grid(row=2, column=1, padx=5, pady=5)
        standard_recording_length_label = ttk.Label(self.settings_window, text="Lenght of standard recording:")
        standard_recording_length_label.grid(row=2, column=0, padx=5, pady=5)

        scale_value_standard_label = ttk.Label(self.settings_window, text=standard_recording_length_var.get())
        scale_value_standard_label.grid(row=2, column=2, padx=5, pady=5)

        ## zmiana wielkości bufora do nagrania awaryjnego
        emergency_buff_size_var = tk.DoubleVar(value=self.cam_controller.emergency_buff_length)

        emergency_buff_size_scale = ttk.Scale(self.settings_window, from_=1, to=60,
                                                   variable=emergency_buff_size_var,
                                                   length=200, orient=tk.HORIZONTAL,
                                                   command=show_scale_value_buffer)
        emergency_buff_size_scale.grid(row=3, column=1, padx=5, pady=5)
        emergency_buff_size_label = ttk.Label(self.settings_window, text="Size of emergency buffer:")
        emergency_buff_size_label.grid(row=3, column=0, padx=5, pady=5)

        scale_value_buffer_label = ttk.Label(self.settings_window, text=emergency_buff_size_var.get())
        scale_value_buffer_label.grid(row=3, column=2, padx=5, pady=5)

        ## zmiana czułości detekcji
        detection_sensitivity_var = tk.DoubleVar(value=self.cam_controller.detection_sensitivity)

        detection_sensitivity_scale = ttk.Scale(self.settings_window, from_=1, to=self.cam_controller.max_detection_sensitivity,
                                                     variable=detection_sensitivity_var,
                                                     length=200, orient=tk.HORIZONTAL,
                                                     command=show_scale_value_sens)
        detection_sensitivity_scale.grid(row=4, column=1, padx=5, pady=5)
        detection_sensitivity_label = ttk.Label(self.settings_window, text="Detection sensivity:")
        detection_sensitivity_label.grid(row=4, column=0, padx=5, pady=5)

        scale_value_sens_label = ttk.Label(self.settings_window, text=detection_sensitivity_var.get())
        scale_value_sens_label.grid(row=4, column=2, padx=5, pady=5)

        # zmiana minimalnego obszaru ruchu
        min_motion_rectangle_area_var = tk.DoubleVar(value=self.cam_controller.min_motion_rectangle_area)

        min_motion_rectangle_area_scale = ttk.Scale(self.settings_window, from_=10, to=5000,
                                                         variable=min_motion_rectangle_area_var,
                                                         length=200, orient=tk.HORIZONTAL,
                                                         command=show_scale_value_rect)
        min_motion_rectangle_area_scale.grid(row=5, column=1, padx=5, pady=5)
        min_motion_rectangle_area_label = ttk.Label(self.settings_window, text="Minimal movement range:")
        min_motion_rectangle_area_label.grid(row=5, column=0, padx=5, pady=5, sticky="W")

        scale_value_rect_label = ttk.Label(self.settings_window, text=min_motion_rectangle_area_var.get())
        scale_value_rect_label.grid(row=5, column=2, padx=5, pady=5)

        # zmiana odstępu między powiadomieniami systemowymi
        min_delay_between_system_notifications_var = tk.DoubleVar(
            value=self.cam_controller.min_delay_between_system_notifications)

        min_delay_between_system_notifications_scale = ttk.Scale(self.settings_window, from_=5, to=600,
                                                                      variable=min_delay_between_system_notifications_var,
                                                                      length=200, orient=tk.HORIZONTAL,
                                                                      command=show_min_delay)
        min_delay_between_system_notifications_scale.grid(row=6, column=1, padx=5, pady=5)
        min_delay_between_system_notifications_label = ttk.Label(self.settings_window,
                                                                      text="Delay between system notifications:")
        min_delay_between_system_notifications_label.grid(row=6, column=0, padx=5, pady=5, sticky="W")

        scale_delay_value_label = ttk.Label(self.settings_window, text = min_delay_between_system_notifications_var.get())
        scale_delay_value_label.grid(row=6, column=2, padx=5, pady=5)

        min_delay_between_email_notifications_var = tk.DoubleVar(
            value=self.cam_controller.min_delay_between_email_notifications)

        min_delay_between_email_notifications_scale = ttk.Scale(self.settings_window, from_=90, to=3600,
                                                                     variable=min_delay_between_email_notifications_var,
                                                                     length=200, orient=tk.HORIZONTAL,
                                                                     command=show_min_delay_mail)
        min_delay_between_email_notifications_scale.grid(row=7, column=1, padx=5, pady=5)
        min_delay_between_email_notifications_label = ttk.Label(self.settings_window,
                                                                     text="Delay between mail notifications:")
        min_delay_between_email_notifications_label.grid(row=7, column=0, padx=5, pady=5, sticky="W")

        scale_delay_mail_value_label = ttk.Label(self.settings_window, text=min_delay_between_email_notifications_var.get())
        scale_delay_mail_value_label.grid(row=7, column=2, padx=5, pady=5)

        self.settings_window=None

        # Przycisk zapisu ustawień
        # save_button = tk.Button(self.settings_window, text="Save")
        # save_button.grid(row=8, column=0, columnspan=2, pady=10)

        # self.settings_window.protocol("WM_DELETE_WINDOW", self.close_settings_window)



    def update_mode(self, mode):
        # Wywołanie zmiany trybu obrazu po wybraniu nowej opcji z menu rozwijanego
        self.update_window()

    def update_email(self, event):
        email = self.email_entry.get()
        if self.validate_email(email):
            self.email_recipient = email
            self.cam_controller.update_parameters()
            print("Aktualizacja adresu e-mail:", self.email_recipient)
        else:
            print("Nieprawidłowy adres e-mail!")
        print(self.email_recipient)

    def validate_email(self, email):
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return re.match(pattern, email) is not None

    def update_system_notification(self, value):
        if value == "Yes":
            self.send_system_notifications = self.cam_controller.send_system_notifications = True
            
        elif value == "No":
            self.send_system_notifications = self.cam_controller.send_system_notifications = False
        self.cam_controller.update_parameters()

    def update_email_notification(self, value):
        if value == "Yes":
            self.send_email_notifications = self.cam_controller.send_email_notifications = True
        elif value == "No":
            self.send_email_notifications = self.cam_controller.send_email_notifications = False
        self.cam_controller.update_parameters()

    def run_surveillance_thread(self):
        self.surveillance_thread = Thread(target=self.cam_controller.start_surveillance)
        self.__logger.info("surveillance thread started")
        self.surveillance_thread.start()

    def kill_surveillance_thread(self):
        if self.cam_controller.cam is not None:
            self.cam_controller.surveillance_running = False
            self.cam_controller.cam.destroy()
        self.__logger.info("surveillance thread stopped")

    def on_closing(self):
        if self.cam_controller.cam is not None:
            self.cam_controller.surveillance_running = False
            self.cam_controller.cam.destroy()
        self.__logger.info("surveillance thread stopped")
        self.destroy()

    def check_schedule(self):
        current_time = datetime.datetime.now().time()
        start_time_str = self.start_time_entry.get()
        end_time_str = self.end_time_entry.get()

        try:
            start_time = datetime.datetime.strptime(start_time_str, "%H:%M").time()
            end_time = datetime.datetime.strptime(end_time_str, "%H:%M").time()

            if start_time <= current_time <= end_time:
                self.run_surveillance_thread()
                self.title("Camera window - Active")
            else:
                self.kill_surveillance_thread()
                self.title("Camera window - Inactive")

        except ValueError:
            self.kill_surveillance_thread()
            self.title("Camera window - Inactive")

        self.after(60000, self.check_schedule)  # Sprawdzanie co minutę


    
    def update_window(self):
        if self.cam_controller.surveillance_running and self.cam_controller.cam is not None:
            selected_mode = self.selected_mode.get()
            if selected_mode == "Rectangles":
                frame = self.cam_controller.cam.get_frame_with_rectangles()
            elif selected_mode == "Contours":
                frame = self.cam_controller.cam.get_frame_with_contours()
            elif selected_mode == "High contrast":
                frame = self.cam_controller.cam.get_high_contrast_frame()
            elif selected_mode == "Mexican hat":
                frame = self.cam_controller.cam.get_mexican_hat_effect_frame()
            elif selected_mode == "Standard":
                frame = self.cam_controller.cam.get_standard_frame()
            elif selected_mode == "Sharpened":
                frame = self.cam_controller.cam.get_sharpened_frame()
            else:
                frame = self.cam_controller.cam.get_gray_frame()

            if frame is not None:
                self.photo = ImageTk.PhotoImage(image=Image.fromarray(frame))
                self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

        self.after(self.__gui_refresh_time, self.update_window)

    @staticmethod
    def open_recordings_folder():
        path = os.path.realpath("../recordings")

        if platform.system() == 'Windows':
            subprocess.Popen(["explorer", path])
        else:
            subprocess.Popen(["xdg-open", path])