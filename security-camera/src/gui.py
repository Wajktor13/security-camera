import tkinter as tk
import logging
import re
import time
import datetime
from tkinter import ttk
from controller import Controller
from threading import Thread
from PIL import Image, ImageTk


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # logging
        # logging.basicConfig(filename="security-camera/security-camera/logs/" + time.strftime("%d-%m-%Y", time.localtime(time.time())) + ".txt",
        #                     level=logging.DEBUG,
        #                     format="[%(asctime)s]:[%(levelname)s]:[%(module)s]:%(message)s")
        logging.basicConfig(filename="../logs/" + time.strftime("%d-%m-%Y", time.localtime(time.time())) + ".txt",
                            level=logging.DEBUG,
                            format="[%(asctime)s]:[%(levelname)s]:[%(module)s]:%(message)s")
        self.__logger = logging.getLogger("security_camera_logger")
        self.__logger.info("security camera started")

        self.cam_controller = Controller(refresh_time=10, emergency_recording_length=10, standard_recording_length=180,
                                         emergency_buff_length=4, detection_sensitivity=13,
                                         max_detection_sensitivity=15, min_motion_rectangle_area=100, fps=24,
                                         camera_number=0, send_system_notifications=True,
                                         min_delay_between_system_notifications=30,
                                         send_email_notifications=False,
                                         min_delay_between_email_notifications=240,
                                         email_recipient="wajktor007@gmail.com")
        self.surveillance_thread = None

        self.title('Camera window')
        self.app_height = int(self.winfo_screenheight())-70
        self.app_width = int(self.winfo_screenwidth())
        self.refresh_time = 1

        self.geometry("{}x{}+-7+0".format(self.app_width, self.app_height)) 
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        ## utworzenie widgetów do zmiany parametrów
        

        ## zmiana częstotliwości odświeżania
        self.refresh_time_var = tk.IntVar(value=self.cam_controller.refresh_time)

        self.refresh_time_scale = ttk.Scale(self, from_=1, to=60,
                                                     variable=self.refresh_time_var,
                                                     length=200, orient=tk.HORIZONTAL, command=self.show_scale_value_refresh)
        self.refresh_time_scale.grid(row=0, column=1, padx=5, pady=5)
        self.refresh_time_label = ttk.Label(self, text="Częstotliwość odświeżania:")
        self.refresh_time_label.grid(row=0, column=0, padx=5, pady=5)

        self.scale_value_refresh_label = ttk.Label(self, text=self.refresh_time_var.get())
        self.scale_value_refresh_label.grid(row=0, column=2, padx=5, pady=5)


        ## zmiana długości nagrywania awaryjnego 
        self.emergency_recording_length_var = tk.IntVar(value=self.cam_controller.no_emergency_recording_frames)
        self.emergency_recording_length_scale = ttk.Scale(self, from_=1, to=30,
                                                        variable=self.emergency_recording_length_var,
                                                        length=200, orient=tk.HORIZONTAL,
                                                        command=self.show_scale_value_emergency)
        self.emergency_recording_length_scale.grid(row=1, column=1, padx=5, pady=5)
        self.emergency_recording_length_label = ttk.Label(self, text="Długość nagrania awaryjnego:")
        self.emergency_recording_length_label.grid(row=1, column=0, padx=5, pady=5)

        self.scale_value_emergency_label = ttk.Label(self, text=self.emergency_recording_length_var.get())
        self.scale_value_emergency_label.grid(row=1, column=2, padx=5, pady=5)



        ## zmiana długości nagrania standardowego
        self.standard_recording_length_var = tk.IntVar(value=self.cam_controller.no_standard_recording_frames)

        self.standard_recording_length_scale = ttk.Scale(self, from_=1, to=250,
                                                     variable=self.standard_recording_length_var,
                                                     length=200, orient=tk.HORIZONTAL, command=self.show_scale_value_standard)
        self.standard_recording_length_scale.grid(row=2, column=1, padx=5, pady=5)
        self.standard_recording_length_label = ttk.Label(self, text="Długość nagrania standardowego:")
        self.standard_recording_length_label.grid(row=2, column=0, padx=5, pady=5)
        
        self.scale_value_standard_label = ttk.Label(self, text=self.standard_recording_length_var.get())
        self.scale_value_standard_label.grid(row=2, column=2, padx=5, pady=5)


        ## zmiana wielkości bufora do nagrania awaryjnego
        self.emergency_buff_size_var = tk.IntVar(value=self.cam_controller.no_emergency_buff_frames)

        self.emergency_buff_size_scale = ttk.Scale(self, from_=1, to=60,
                                                     variable=self.emergency_buff_size_var,
                                                     length=200, orient=tk.HORIZONTAL, command=self.show_scale_value_buffer)
        self.emergency_buff_size_scale.grid(row=3, column=1, padx=5, pady=5)
        self.emergency_buff_size_label = ttk.Label(self, text="Wielkość bufora awaryjnego:")
        self.emergency_buff_size_label.grid(row=3, column=0, padx=5, pady=5)

        self.scale_value_buffer_label = ttk.Label(self, text=self.emergency_buff_size_var.get())
        self.scale_value_buffer_label.grid(row=3, column=2, padx=5, pady=5)


        ## zmiana czułości detekcji
        self.detection_sensitivity_var = tk.IntVar(value=self.cam_controller.detection_sensitivity)
        
        self.detection_sensitivity_scale = ttk.Scale(self, from_=1, to=self.cam_controller.max_detection_sensitivity,
                                                     variable=self.detection_sensitivity_var,
                                                     length=200, orient=tk.HORIZONTAL, command=self.show_scale_value_sens)
        self.detection_sensitivity_scale.grid(row=4, column=1, padx=5, pady=5)
        self.detection_sensitivity_label = ttk.Label(self, text="Czułość detekcji:")
        self.detection_sensitivity_label.grid(row=4, column=0, padx=5, pady=5)

        self.scale_value_sens_label = ttk.Label(self, text=self.detection_sensitivity_var.get())
        self.scale_value_sens_label.grid(row=4, column=2, padx=5, pady=5)

        # zmiana minimalnego obszaru ruchu
        self.min_motion_rectangle_area_var = tk.IntVar(value=self.cam_controller.min_motion_rectangle_area)

        self.min_motion_rectangle_area_scale = ttk.Scale(self, from_=10, to=5000,
                                                         variable=self.min_motion_rectangle_area_var,
                                                         length=200, orient=tk.HORIZONTAL, command=self.show_scale_value_rect)
        self.min_motion_rectangle_area_scale.grid(row=5, column=1, padx=5, pady=5)
        self.min_motion_rectangle_area_label = ttk.Label(self, text="Minimalny obszar ruchu:")
        self.min_motion_rectangle_area_label.grid(row=5, column=0, padx=5, pady=5,sticky="W")
        
        self.scale_value_rect_label = ttk.Label(self, text=self.min_motion_rectangle_area_var.get())
        self.scale_value_rect_label.grid(row=5, column=2, padx=5, pady=5)


        # zmiana odstępu między powiadomieniami systemowymi
        self.min_delay_between_system_notifications_var = tk.IntVar(value=self.cam_controller.min_delay_between_system_notifications)

        self.min_delay_between_system_notifications_scale = ttk.Scale(self, from_=5, to=600,
                                                         variable=self.min_delay_between_system_notifications_var,
                                                         length=200, orient=tk.HORIZONTAL, command=self.show_min_delay)
        self.min_delay_between_system_notifications_scale.grid(row=6, column=1, padx=5, pady=5)
        self.min_delay_between_system_notifications_label = ttk.Label(self, text="Odstęp czasowy między powiadomieniami systemowymi:")
        self.min_delay_between_system_notifications_label.grid(row=6, column=0, padx=5, pady=5,sticky="W")
        
        self.scale_delay_value_label = ttk.Label(self, text=self.min_delay_between_system_notifications_var.get())
        self.scale_delay_value_label.grid(row=6, column=2, padx=5, pady=5)

        self.min_delay_between_email_notifications_var = tk.IntVar(value=self.cam_controller.min_delay_between_email_notifications)

        self.min_delay_between_email_notifications_scale = ttk.Scale(self, from_=90, to=3600,
                                                         variable=self.min_delay_between_email_notifications_var,
                                                         length=200, orient=tk.HORIZONTAL, command=self.show_min_delay_mail)
        self.min_delay_between_email_notifications_scale.grid(row=7, column=1, padx=5, pady=5)
        self.min_delay_between_email_notifications_label = ttk.Label(self, text="Odstęp czasowy między powiadomieniami mailowymi:")
        self.min_delay_between_email_notifications_label.grid(row=7, column=0, padx=5, pady=5,sticky="W")
        
        self.scale_delay_mail_value_label = ttk.Label(self, text=self.min_delay_between_email_notifications_var.get())
        self.scale_delay_mail_value_label.grid(row=7, column=2, padx=5, pady=5)
        
        self.selected_mode = tk.StringVar()
        self.selected_mode.set("Prostokąty")  # Ustawienie trybu na początku

        # Tworzenie menu rozwijanego
        self.mode_label = tk.Label(self, text="Zmiana trybu obrazu:")
        self.mode_label.grid(row=7, column=3, padx=5, pady=5)
        self.mode_options = ["Standardowy", "Prostokąty", "Kontury", "Wysoki kontrast", "Meksykańska czapka", "Szarość", "Wyostrzony"]
        self.mode_menu = tk.OptionMenu(self, self.selected_mode, *self.mode_options)
        self.mode_menu.grid(row=7,column=4,padx=5,pady=5)


        self.email_label = tk.Label(self, text="Email do powiadomień:")
        self.email_label.grid(row=8, column=3, padx=5, pady=5)

        self.email_entry = tk.Entry(self)
        
        self.email_entry.grid(row=8, column=4, padx=5, pady=5)
        self.email_entry.bind("<Return>", self.update_email)

        self.notification_label = tk.Label(self, text="Czy wysyłać powiadomienia systemowe:")
        self.notification_label.grid(row=9, column=3, padx=5, pady=5)
        self.notification_var = tk.StringVar(value="Tak")
        self.notification_menu = tk.OptionMenu(self, self.notification_var, "Tak", "Nie", command=self.update_system_notification)
        self.notification_menu.grid(row=9, column=4, padx=5, pady=5)

        self.notification_label2 = tk.Label(self, text="Czy wysyłać powiadomienia mailowe:")
        self.notification_label2.grid(row=10, column=3, padx=5, pady=5)
        self.notification_var2 = tk.StringVar(value="Nie")
        self.notification_menu2 = tk.OptionMenu(self, self.notification_var2, "Tak", "Nie", command=self.update_email_notification)
        self.notification_menu2.grid(row=10, column=4, padx=5, pady=5)

        ## przyciski
        buttons_frame = tk.Frame(self)
        self.start_button = tk.Button(buttons_frame, text="Start", command=self.run_surveillance_thread, width=30, height=2)
        self.stop_button = tk.Button(buttons_frame, text="Stop", command=self.kill_surveillance_thread, width=30, height=2)
        self.start_button.grid(row=0, column=0, pady=5)
        self.stop_button.grid(row=1, column=0, pady=5)
        buttons_frame.grid(row=6, column=3, pady=10, sticky="E")

        ## okno aplikacji
        canvas_frame = tk.Frame(self)
        self.canvas = tk.Canvas(canvas_frame, width=int(self.app_width*0.7), height=int(self.app_height*0.5))
        self.canvas.pack(padx=10, pady=10)
        canvas_frame.grid(row=0, column=3, pady=10, rowspan=5, columnspan=6,sticky="E")

        self.start_time_label = tk.Label(self, text="Godzina rozpoczęcia (HH:MM):")
        self.start_time_label.grid(row=7, column=5, padx=5, pady=5)

        self.start_time_entry = tk.Entry(self)
        self.start_time_entry.grid(row=7, column=6, padx=5, pady=5)

        self.end_time_label = tk.Label(self, text="Godzina zakończenia (HH:MM):")
        self.end_time_label.grid(row=8, column=5, padx=5, pady=5)

        self.end_time_entry = tk.Entry(self)
        self.end_time_entry.grid(row=8, column=6, padx=5, pady=5)
        self.check_schedule()        

        self.photo = None

        self.update_window()



    def update_mode(self, mode):
        # Wywołanie zmiany trybu obrazu po wybraniu nowej opcji z menu rozwijanego
        self.update_window()

    def update_email(self, event):
        email = self.email_entry.get()
        if self.validate_email(email):
            self.email_recipient = email
            print("Aktualizacja adresu e-mail:", self.email_recipient)
        else:
            print("Nieprawidłowy adres e-mail!")
        print(self.email_recipient)

    def validate_email(self, email):
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return re.match(pattern, email) is not None


    def update_system_notification(self, value):
        if value == "Tak":
            self.send_system_notifications = True
        elif value == "Nie":
            self.send_system_notifications = False
        

    def update_email_notification(self, value):
        if value == "Tak":
            self.send_email_notifications = True
        elif value == "Nie":
            self.send_email_notifications = False

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
                self.title("Kamera - WŁĄCZONA")
            else:
                self.title("Kamera - WYŁĄCZONA")

        except ValueError:
            self.title("Kamera - BŁĄD")

        self.after(60000, self.check_schedule)  # Sprawdzanie co minutę

    ## funckja do uzyskiwania aktualnej wartości suwaka
    def show_scale_value_emergency(self, value):
        self.scale_value_emergency_label.configure(text=value)
        self.cam_controller.no_emergency_recording_frames=self.emergency_recording_length_scale.get()
    
    def show_scale_value_refresh(self, value):
        self.scale_value_refresh_label.configure(text=value)
        self.cam_controller.refresh_time=int(self.refresh_time_scale.get())
    
    def show_scale_value_buffer(self, value):
        self.scale_value_buffer_label.configure(text=value)
        self.cam_controller.no_emergency_buff_frames=self.emergency_buff_size_scale.get()
    
    def show_scale_value_rect(self, value):
        self.scale_value_rect_label.configure(text=value)
        self.cam_controller.min_motion_rectangle_area = self.min_motion_rectangle_area_scale.get()  

    def show_scale_value_sens(self, value):
        self.scale_value_sens_label.configure(text=value)
        self.cam_controller.detection_sensitivity = self.detection_sensitivity_scale.get()
    
    def show_scale_value_standard(self, value):
        self.scale_value_standard_label.configure(text=value)
        self.cam_controller.no_standard_recording_frames=self.standard_recording_length_scale.get()
    
    def show_min_delay(self, value):
        self.scale_delay_value_label.configure(text=value)
        self.cam_controller.min_delay_between_system_notifications=self.min_delay_between_system_notifications_scale.get()

    def show_min_delay_mail(self, value):
        self.scale_delay_mail_value_label.configure(text=value)
        self.cam_controller.min_delay_between_email_notifications=self.min_delay_between_email_notifications_scale.get()


    def update_window(self):
        if self.cam_controller.surveillance_running and self.cam_controller.cam is not None:
            selected_mode = self.selected_mode.get()
            if selected_mode == "Prostokąty":
                frame=self.cam_controller.cam.get_frame_with_rectangles()
            elif selected_mode == "Kontury":
                frame=self.cam_controller.cam.get_frame_with_contours()
            elif selected_mode == "Wysoki kontrast":
                frame=self.cam_controller.cam.get_high_contrast_frame()
            elif selected_mode == "Meksykańska czapka":
                frame=self.cam_controller.cam.get_mexican_hat_effect_frame()
            elif selected_mode == "Standardowy":
                frame=self.cam_controller.cam.get_standard_frame()
            elif selected_mode == "Wyostrzony":
                frame=self.cam_controller.cam.get_sharpened_frame()
            else:
                frame=self.cam_controller.cam.get_gray_frame()

            if frame is not None:
                self.photo = ImageTk.PhotoImage(image=Image.fromarray(frame))
                self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

        self.after(self.refresh_time, self.update_window)
