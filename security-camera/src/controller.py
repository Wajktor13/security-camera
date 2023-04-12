import cv2
from camera import Camera
import time


class Controller:
    '''
        class responsible for surveillance logic
    '''

    def __init__(self, refresh_time, emergency_recording_length, standard_recording_length, emergency_buff_size,
                 detection_sensitivity, max_detection_sensitivity, min_motion_rectangle_area):
        self.refresh_time = refresh_time
        self.emergency_recording_length = emergency_recording_length
        self.standard_recording_length = standard_recording_length
        self.emergency_buff_size = emergency_buff_size
        self.detection_sensitivity = detection_sensitivity
        self.max_detection_sensitivity = max_detection_sensitivity
        self.min_motion_rectangle_area = min_motion_rectangle_area
        self.cam = Camera(emergency_buff_size=emergency_buff_size, detection_sensitivity=detection_sensitivity,
                          max_detection_sensitivity=max_detection_sensitivity,
                          min_motion_rectangle_area=min_motion_rectangle_area)

        self.surveillance_running = False

    def start_surveillance(self):
        self.surveillance_running = True
        emergency_recording_start_time = None
        surveillance_start_time = time.time()

        while not self.cam.validate_capture():
            '''
                opening input stream failed, try again
            '''

            self.cam = Camera(emergency_buff_size=self.emergency_buff_size,
                              detection_sensitivity=self.detection_sensitivity,
                              max_detection_sensitivity=self.max_detection_sensitivity,
                              min_motion_rectangle_area=self.min_motion_rectangle_area)

        standard_recording_start_time = time.time()

        while self.surveillance_running:
            self.cam.refresh_frame()
            self.cam.save_frame()

            '''
                check if standard recording should end
            '''
            if time.time() - standard_recording_start_time >= self.standard_recording_length + 1:
                self.cam.stop_recording()
                standard_recording_start_time = time.time()

            '''
                handle emergency recording
            '''
            if not self.cam.emergency_started:
                if time.time() - surveillance_start_time >= 2 and self.cam.search_for_motion():
                    if self.surveillance_running:
                        emergency_recording_start_time = time.time()
                        self.cam.emergency_save_frame()

            elif time.time() - emergency_recording_start_time >= self.emergency_recording_length + 1:
                self.cam.stop_emergency_recording()

            else:
                self.cam.emergency_save_frame()

            if cv2.waitKey(self.refresh_time) == ord('q'):
                self.cam.destroy()
                self.surveillance_running = False
