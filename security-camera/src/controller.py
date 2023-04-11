import cv2
from camera import Camera
import time


class Controller:
    def __init__(self):
        self.refresh_time = 10
        self.emergency_recording_length = 4
        self.standard_recording_length = 3
        self.monitoring = True
        self.cam = Camera()

    def start_monitoring(self):
        
        emergency_recording_started = False
        emergency_recording_start_time = None

        while not self.cam.validate_capture():
            print('cannot open input stream')
            time.sleep(1)
            self.cam = Camera()

        standard_recording_start_time = time.time()

        while self.monitoring:
            self.cam.refresh_frame()
            self.cam.save_frame()

            if time.time() - standard_recording_start_time >= self.standard_recording_length + 1:
                self.cam.stop_recording()
                standard_recording_start_time = time.time()

            if not emergency_recording_started:
                if self.cam.search_for_motion():
                    emergency_recording_started = True
                    emergency_recording_start_time = time.time()
                    self.cam.emergency_save_frame()
                    
            elif time.time() - emergency_recording_start_time >= self.emergency_recording_length + 1:
                emergency_recording_started = False
                self.cam.stop_emergency_recording()

            else:
                self.cam.emergency_save_frame()

            if cv2.waitKey(self.refresh_time) == ord('q'):
                self.cam.destroy()
                break


if __name__ == "__main__":
    c = Controller()
    c.start_monitoring()
