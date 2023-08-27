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
from camera import Camera


class SecurityCameraApp(tk.Tk):

    def __init__(self):
        super().__init__(className="Security Camera")

        # logging
        self.__logger = logging.getLogger("security_camera_logger")

        # cam and surveillance
        self.cam_controller = Controller()
        self.surveillance_thread = None
        self.__no_cameras = Camera.get_number_of_camera_devices()

        ''' gui '''
        # basic
        self.__app_width = 1700
        self.__app_height = 720
        self.__img_width = 1280
        self.__img_height = 720
        self.__gui_refresh_time = 10
        self.__displayed_img = None
        self.__antispam_length = 5
        self.resizable(False, False)
        self.geometry("{}x{}+-7+0".format(self.__app_width, self.__app_height))
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.title('Security Camera')
        self.option_add("*tearOff", False)
        self.grid_columnconfigure(0, minsize=420)
        self.iconphoto(False, tk.PhotoImage(file="../assets/eye_icon.png"))

        # theme
        self.__style = ttk.Style()
        self.__main_font = "TkDefaultFont 14"
        self.tk.call("source", "../assets/tkinter_theme/forest-dark.tcl")
        self.__style.theme_use("forest-dark")
        self.option_add("*Font", self.__main_font)
        self.__style.configure("TButton", font=self.__main_font)
        self.__style.configure("Custom.TMenubutton", font=self.__main_font)

        # canvas
        canvas_frame = ttk.Frame(self)
        canvas_frame.grid(row=0, column=3, rowspan=7)

        self.__canvas = tk.Canvas(canvas_frame, width=self.__app_width, height=self.__app_height)
        self.__canvas.pack(fill=tk.BOTH, expand=True)

        # sidebar
        self.__image_mode_dropdown = None
        self.__toggle_surveillance_button = None
        self.create_sidebar()

        # settings window
        self.__settings_window = None

        # cyclic window update
        self.update_window()

    def create_sidebar(self):
        button_width = 30
        button_padding = 6

        # buttons frame
        sidebar_frame = ttk.Frame(self)

        # toggle surveillance button
        self.__toggle_surveillance_button = ttk.Button(sidebar_frame, text="Start surveillance", style='Accent.TButton',
                                                       command=self.toggle_surveillance, width=button_width)
        self.__toggle_surveillance_button.grid(row=0, column=0, columnspan=2, pady=button_padding, padx=button_padding)

        # settings button
        settings_button = ttk.Button(sidebar_frame, text="Settings", style='Accent.TButton',
                                     command=self.open_settings_window, width=button_width)
        settings_button.grid(row=2, column=0, columnspan=2, pady=button_padding, padx=button_padding)

        # go to recordings button
        go_to_recordings_buttons = ttk.Button(sidebar_frame, text="Open recordings directory", style='Accent.TButton',
                                              command=self.open_recordings_folder, width=button_width)
        go_to_recordings_buttons.grid(row=4, columnspan=2, column=0, pady=button_padding, padx=button_padding)

        # dropdown
        self.__image_mode_dropdown = DropdownSetting(root=sidebar_frame, initial_value="Rectangles",
                                                     label_text="Camera mode:",
                                                     dropdown_options=["Standard", "Standard              ",
                                                                       "Rectangles",
                                                                       "Contours", "High contrast", "Mexican hat",
                                                                       "Gray",
                                                                       "Sharpened"],
                                                     width=15, row=5, column=0, padding_x=5, padding_y=5)

        # place frame
        sidebar_frame.grid(row=0, column=0, pady=(200, 10), padx=10, columnspan=2)

    def open_settings_window(self):
        if self.__settings_window is not None:
            return

        def on_settings_closing():
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")
            self.__settings_window.destroy()
            self.__settings_window = None

        self.__settings_window = tk.Toplevel(self)
        self.__settings_window.title("Security Camera Settings")
        self.__settings_window.resizable(False, False)
        self.__settings_window.iconphoto(False, tk.PhotoImage(file="../assets/settings.png"))
        self.__settings_window.protocol("WM_DELETE_WINDOW", on_settings_closing)

        # frame, canvas and scrollbar
        def on_canvas_configure(_):
            settings_frame.update_idletasks()
            canvas.config(scrollregion=canvas.bbox("all"))

        def scroll_canvas(value):
            canvas.yview_scroll(value, "units")

        canvas = tk.Canvas(self.__settings_window, width=980, height=700)
        scrollbar = tk.Scrollbar(self.__settings_window, orient="vertical", command=canvas.yview)
        canvas.config(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        settings_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=settings_frame, anchor="nw")

        canvas.bind_all("<MouseWheel>", lambda event: scroll_canvas(int(-1 * (event.delta / 120))))
        canvas.bind_all("<Button-4>", lambda _: scroll_canvas(-1))
        canvas.bind_all("<Button-5>", lambda _: scroll_canvas(1))
        canvas.bind("<Configure>", on_canvas_configure)

        # scale settings
        settings_padding_x = 15
        settings_padding_y = 30
        scale_length = 450

        recording_fps_scale_setting = (
            ScaleSetting(root=settings_frame, initial_value=self.cam_controller.fps, min_value=1,
                         max_value=60, scale_length=scale_length, row=0, column=0, padding_x=settings_padding_x,
                         padding_y=settings_padding_y, label_text="Recording fps (FPS):"))

        emergency_recording_length_scale_setting = (
            ScaleSetting(root=settings_frame,
                         initial_value=self.cam_controller.emergency_recording_length, min_value=1, max_value=30,
                         scale_length=scale_length, row=1, column=0, padding_x=settings_padding_x,
                         padding_y=settings_padding_y, label_text="Length of emergency recording (s):"))

        standard_recording_length_scale_setting = (
            ScaleSetting(root=settings_frame,
                         initial_value=self.cam_controller.standard_recording_length, min_value=1, max_value=300,
                         scale_length=scale_length, row=2, column=0, padding_x=settings_padding_x,
                         padding_y=settings_padding_y, label_text="Length of standard recording (s):"))

        emergency_buff_length_scale_setting = (
            ScaleSetting(root=settings_frame,
                         initial_value=self.cam_controller.emergency_buff_length, min_value=1, max_value=60,
                         scale_length=scale_length, row=3, column=0, padding_x=settings_padding_x,
                         padding_y=settings_padding_y, label_text="Length of emergency buffer (s):"))

        detection_sensitivity_scale_setting = (
            ScaleSetting(root=settings_frame,
                         initial_value=self.cam_controller.detection_sensitivity, min_value=1,
                         max_value=self.cam_controller.max_detection_sensitivity, scale_length=scale_length, row=4,
                         column=0, padding_x=settings_padding_x, padding_y=settings_padding_y,
                         label_text="Detection sensitivity (unitless):"))

        min_motion_area_var_scale_setting = (
            ScaleSetting(root=settings_frame,
                         initial_value=self.cam_controller.min_motion_rectangle_area, min_value=10, max_value=5000,
                         scale_length=scale_length, row=5, column=0, padding_x=settings_padding_x,
                         padding_y=settings_padding_y, label_text="Minimal motion area (pixels):"))

        delay_between_system_notifications_scale_setting = (
            ScaleSetting(root=settings_frame,
                         initial_value=self.cam_controller.min_delay_between_system_notifications, min_value=5,
                         max_value=600, scale_length=scale_length, row=6, column=0, padding_x=settings_padding_x,
                         padding_y=settings_padding_y, label_text="Delay between system notifications (s):"))

        delay_between_email_notifications_scale_setting = (
            ScaleSetting(root=settings_frame,
                         initial_value=self.cam_controller.min_delay_between_email_notifications,
                         min_value=5, max_value=600, scale_length=scale_length, row=7, column=0,
                         padding_x=settings_padding_x, padding_y=settings_padding_y,
                         label_text="Delay between email notifications (s):"))

        # checkbutton settings
        system_notifications_checkbutton_setting = (
            CheckbuttonSetting(root=settings_frame,
                               initial_value=self.cam_controller.send_system_notifications,
                               label_text="Send system notifications:", row=11, column=0, padding_x=settings_padding_x,
                               padding_y=settings_padding_y))

        email_notifications_checkbutton_setting = (
            CheckbuttonSetting(root=settings_frame,
                               initial_value=self.cam_controller.send_email_notifications,
                               label_text="Send email notifications:", row=12, column=0, padding_x=settings_padding_x,
                               padding_y=settings_padding_y))

        local_recordings_checkbutton_setting = (
            CheckbuttonSetting(root=settings_frame,
                               initial_value=self.cam_controller.save_recordings_locally,
                               label_text="Save recordings locally:", row=13, column=0, padding_x=settings_padding_x,
                               padding_y=settings_padding_y))

        upload_to_gdrive_checkbutton_setting = (
            CheckbuttonSetting(root=settings_frame,
                               initial_value=self.cam_controller.upload_to_gdrive,
                               label_text="Upload recordings to Google Drive:", row=14, column=0,
                               padding_x=settings_padding_x, padding_y=settings_padding_y))

        # entry settings
        entry_length = 38

        email_entry_setting = (
            EntrySetting(root=settings_frame, initial_value=self.cam_controller.email_recipient,
                         label_text="Email notifications recipient:", row=9, column=0, width=entry_length,
                         padding_x=settings_padding_x, padding_y=settings_padding_y, font=self.__main_font))

        gdrive_folder_id_entry_setting = (
            EntrySetting(root=settings_frame, initial_value=self.cam_controller.gdrive_folder_id,
                         label_text="Google Drive folder ID:", row=10, column=0, width=entry_length,
                         padding_x=settings_padding_x, padding_y=settings_padding_y, font=self.__main_font))

        # camera number dropdown
        camera_number_var = tk.IntVar()
        camera_number_var.set(0)
        camera_number_label = ttk.Label(settings_frame, text="Camera number:")
        camera_number_label.grid(row=8, column=0, padx=settings_padding_x, pady=settings_padding_y, sticky="W")
        camera_number_options = [self.cam_controller.camera_number] + [i for i in range(self.__no_cameras)]
        camera_number_menu = ttk.OptionMenu(settings_frame, camera_number_var, *camera_number_options,
                                            style="Custom.TMenubutton")
        camera_number_menu.config(width=2)
        camera_number_menu.grid(row=8, column=1, padx=5, pady=5)

        # settings applied label
        settings_applied_label = ttk.Label(settings_frame, text="", padding=(5, 5))
        settings_applied_label.configure(foreground="#217346")
        settings_applied_label.grid(row=16, column=0, columnspan=3, padx=200)

        # apply settings button
        def update_email(new_email):
            if validate_email(new_email):
                self.cam_controller.email_recipient = new_email
                self.__logger.info("updated recipient email to: " + new_email)
            else:
                self.__logger.warning("recipient email not updated - wrong email: " + new_email)

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

            # checkbutton settings
            self.cam_controller.send_system_notifications = system_notifications_checkbutton_setting.get_value()
            self.cam_controller.send_email_notifications = email_notifications_checkbutton_setting.get_value()
            self.cam_controller.save_recordings_locally = local_recordings_checkbutton_setting.get_value()
            self.cam_controller.upload_to_gdrive = upload_to_gdrive_checkbutton_setting.get_value()

            # email entry
            update_email(email_entry_setting.get_value())

            # google drive folder id entry
            self.cam_controller.gdrive_folder_id = gdrive_folder_id_entry_setting.get_value()

            # camera number dropdown
            prev_camera_number = self.cam_controller.camera_number
            self.cam_controller.camera_number = camera_number_var.get()
            self.__logger.info("changed camera")
            if (prev_camera_number != camera_number_var.get() and
                    self.cam_controller.surveillance_running):
                # restarting surveillance in order to change camera
                self.kill_surveillance_thread()
                self.run_surveillance_thread()
                self.__logger.info("restarted surveillance after camera change")

            # updating parameters
            self.cam_controller.update_parameters()

            # saving parameters to JSON
            self.cam_controller.controller_settings_manager.save_settings(self.cam_controller)

            # show settings applied label
            settings_applied_label.config(text="✔ settings have been applied")

        apply_settings_button = ttk.Button(settings_frame, text="Apply", style='Accent.TButton',
                                           command=apply_settings, width=5)
        apply_settings_button.grid(row=15, column=0, columnspan=3, padx=390, pady=(30, 5), sticky="ew")

    def toggle_surveillance(self):
        self.__toggle_surveillance_button.state(["disabled"])

        if not self.cam_controller.surveillance_running:
            self.run_surveillance_thread()
            self.toggle_surveillance_button_antispam(self.__antispam_length)
        else:
            self.kill_surveillance_thread()
            self.toggle_surveillance_button_antispam(self.__antispam_length)

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
                frame = modes[self.__image_mode_dropdown.get_value()]()
            except KeyError:
                frame = cam.get_standard_frame()

            if frame is not None:
                img = Image.fromarray(frame).resize(size=(self.__img_width, self.__img_height))
                self.__displayed_img = ImageTk.PhotoImage(image=img)
                self.__canvas.create_image(0, 0, image=self.__displayed_img, anchor=tk.NW)

        self.after(self.__gui_refresh_time, self.update_window)

    def toggle_surveillance_button_antispam(self, iteration):
        if iteration > 0:
            new_text = "Stop surveillance" if self.cam_controller.surveillance_running else "Start surveillance"
            self.__toggle_surveillance_button.config(text=f"{new_text} ({iteration})")
            self.after(1000, self.toggle_surveillance_button_antispam, iteration - 1)
        else:
            current_text = self.__toggle_surveillance_button.cget("text")
            self.__toggle_surveillance_button.config(text=current_text[:-3])
            self.__toggle_surveillance_button.state(["!disabled"])

    @staticmethod
    def open_recordings_folder():
        path = os.path.realpath("../recordings")

        if platform.system() == 'Windows':
            subprocess.Popen(["explorer", path])
        else:
            subprocess.Popen(["xdg-open", path])


class ScaleSetting:
    def __init__(self, root, initial_value, min_value, max_value, scale_length, row, column, padding_x,
                 padding_y, label_text):
        self.__var = tk.DoubleVar(value=initial_value)

        self.__label = tk.ttk.Label(master=root, text=label_text)

        self.__scale = tk.ttk.Scale(master=root, from_=min_value, to=max_value, variable=self.__var,
                                    length=scale_length, orient=tk.HORIZONTAL,
                                    command=lambda value: self.value_label.configure(text=round(float(value), 0)))

        self.value_label = tk.ttk.Label(master=root, text=self.__var.get())

        self.arrange(row, column, padding_x, padding_y)

    def arrange(self, row, column, padding_x, padding_y):
        self.__label.grid(row=row, column=column, padx=padding_x, pady=padding_y, sticky="W")
        self.__scale.grid(row=row, column=column + 1, padx=padding_x, pady=padding_y)
        self.value_label.grid(row=row, column=column + 2, padx=padding_x, pady=padding_y)

    def get_value(self):
        return round(float(self.__var.get()), 0)


class CheckbuttonSetting:
    def __init__(self, root, initial_value, label_text, row, column, padding_x, padding_y):
        self.__var = tk.BooleanVar(value=initial_value)

        self.__label = tk.ttk.Label(master=root, text=label_text)

        self.__menu = ttk.Checkbutton(master=root, variable=self.__var)

        self.arrange(row, column, padding_x, padding_y)

    def arrange(self, row, column, padding_x, padding_y):
        self.__label.grid(row=row, column=column, padx=padding_x, pady=padding_y, sticky="W")
        self.__menu.grid(row=row, column=column + 1, padx=padding_x, pady=padding_y)

    def get_value(self):
        return self.__var.get()


class EntrySetting:
    def __init__(self, root, initial_value, label_text, row, column, width, padding_x, padding_y, font):
        self.__var = tk.StringVar(value=initial_value)

        self.__label = tk.ttk.Label(master=root, text=label_text)

        self.__entry = tk.Entry(master=root, width=width, textvariable=self.__var, font=font)

        self.arrange(row, column, padding_x, padding_y)

    def arrange(self, row, column, padding_x, padding_y):
        self.__label.grid(row=row, column=column, padx=padding_x, pady=padding_y, sticky="W")
        self.__entry.grid(row=row, column=column + 1, padx=padding_x, pady=padding_y)

    def get_value(self):
        return self.__var.get()


class DropdownSetting:
    def __init__(self, root, initial_value, label_text, dropdown_options, width, row, column, padding_x, padding_y):
        self.__var = tk.StringVar(value=initial_value)

        self.__label = ttk.Label(master=root, text=label_text)

        self.__menu = ttk.OptionMenu(root, self.__var, *dropdown_options, style="Custom.TMenubutton")

        self.__menu.config(width=width)
        self.arrange(row, column, padding_x, padding_y)

    def arrange(self, row, column, padding_x, padding_y):
        self.__label.grid(row=row, column=column, padx=padding_x, pady=padding_y, sticky="W")
        self.__menu.grid(row=row, column=column + 1, padx=padding_x, pady=padding_y)

    def get_value(self):
        return self.__var.get()
