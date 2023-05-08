import tkinter as tk
import logging
import time
from tkinter import ttk
from controller import Controller
from threading import Thread
from PIL import Image, ImageTk


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        #logging
        logging.basicConfig(filename="../logs/" + time.strftime("%d-%m-%Y", time.localtime(time.time())) + ".txt",
                            level=logging.DEBUG,
                            format="[%(asctime)s]:[%(levelname)s]:[%(module)s]:%(message)s")
        self.logger = logging.getLogger("security_camera_logger")
        self.logger.info("security camera started")

        self.cam_controller = Controller(refresh_time=1, emergency_recording_length=10, standard_recording_length=180,
                                         emergency_buff_length=4, detection_sensitivity=13,
                                         max_detection_sensitivity=15, min_motion_rectangle_area=100, fps=24,
                                         camera_number=0, send_system_notifications=True,
                                         min_delay_between_system_notifications=0)
        self.surveillance_thread = None

        self.title('Camera window')
        self.app_height = int(self.winfo_screenheight()*0.9)
        self.app_width = int(self.winfo_screenwidth()*0.9)
        self.screen_height = self.winfo_screenheight()
        self.screen_width = self.winfo_screenwidth()
        self.x_coordinate = int((self.screen_width / 2) - (self.app_width / 2))
        ## odjęte 30 pikseli ze względu na pasek nawigacyjny Windowsa
        self.y_coordinate = int((self.screen_height / 2) - (self.app_height / 2))-30
        self.refresh_time = 1

        self.geometry("{}x{}+{}+{}".format(self.app_width, self.app_height, self.x_coordinate, self.y_coordinate))

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


        self.apply_button = ttk.Button(self, text="Zastosuj", command=self.apply_changes)
        self.apply_button.grid(row=6, column=0, columnspan=2, padx=5, pady=5, sticky="W")

        ## przyciski
        buttons_frame = tk.Frame(self)
        self.start_button = tk.Button(buttons_frame, text="Start", command=self.run_surveillance_thread, width=30, height=2)
        self.stop_button = tk.Button(buttons_frame, text="Stop", command=self.kill_surveillance_thread, width=30, height=2)
        self.start_button.grid(row=0, column=0, pady=5)
        self.stop_button.grid(row=1, column=0, pady=5)
        buttons_frame.grid(row=5, column=5, pady=10, sticky="E")

        ## okno aplikacji
        canvas_frame = tk.Frame(self)
        self.canvas = tk.Canvas(canvas_frame, width=int(self.app_width*0.5), height=int(self.app_height*0.5))
        self.canvas.pack(padx=10, pady=10)
        canvas_frame.grid(row=0, column=4, pady=10, rowspan=4, columnspan=3,sticky="E")

        self.photo = None

        self.update_window()

    def run_surveillance_thread(self):
        self.surveillance_thread = Thread(target=self.cam_controller.start_surveillance)
        self.surveillance_thread.start()

    def kill_surveillance_thread(self):
        if self.cam_controller.cam is not None:
            self.cam_controller.surveillance_running = False
            self.cam_controller.cam.destroy()
        # ???

    ## funckja do uzyskiwania aktualnej wartości suwaka
    def show_scale_value_emergency(self, value):
        self.scale_value_emergency_label.configure(text=value)
    
    def show_scale_value_refresh(self, value):
        self.scale_value_refresh_label.configure(text=value)
    
    def show_scale_value_buffer(self, value):
        self.scale_value_buffer_label.configure(text=value)
    
    def show_scale_value_rect(self, value):
        self.scale_value_rect_label.configure(text=value)

    def show_scale_value_sens(self, value):
        self.scale_value_sens_label.configure(text=value)
    
    def show_scale_value_standard(self, value):
        self.scale_value_standard_label.configure(text=value)


    def apply_changes(self):
            ## funkcja do aktualizowania konfiguracji
            self.cam_controller.detection_sensitivity = self.detection_sensitivity_scale.get()
            self.cam_controller.min_motion_rectangle_area = self.min_motion_rectangle_area_scale.get()
            self.cam_controller.refresh_time=int(self.refresh_time_scale.get())
            self.cam_controller.no_emergency_buff_frames=self.emergency_buff_size_scale.get()
            self.cam_controller.no_emergency_recording_frames=self.emergency_recording_length_scale.get()
            self.cam_controller.no_standard_recording_frames=self.standard_recording_length_scale.get()

    def update_window(self):
        if self.cam_controller.surveillance_running and self.cam_controller.cam is not None:

            frame = self.cam_controller.cam.get_frame_with_rectangles()

            if frame is not None:
                self.photo = ImageTk.PhotoImage(image=Image.fromarray(frame))
                self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

        self.after(self.refresh_time, self.update_window)
