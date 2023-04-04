import cv2
from camera.camera import Camera
import time
import tkinter as tk
from PIL import Image, ImageTk
import time

'''

* tests *

'''

REFRESH_TIME = 35
EMERGENCY_RECORDING_LENGTH = 4
STANDARD_RECORDING_LENGTH = 15

def show_video():
    cam = Camera()
    emergency_started = False
    emergency_recording_start_time = None

    while not cam.validate_capture():
        print('cannot open input stream')
        time.sleep(1)
        cam = Camera()

    standard_recording_start_time = time.time()

    while True:
        cam.refresh_frame()
        cam.save_frame()
        cam.show_window()

        if time.time() - standard_recording_start_time >= STANDARD_RECORDING_LENGTH + 1:
            cam.stop_recording()
            standard_recording_start_time = time.time()

        if not emergency_started:
            if cam.search_for_motion():
                print('motion detected')
                emergency_started = True
                emergency_recording_start_time = time.time()
                cam.emergency_save_frame()
        elif time.time() - emergency_recording_start_time >= EMERGENCY_RECORDING_LENGTH + 1:
            emergency_started = False
            cam.stop_emergency_recording()

        else:
            cam.emergency_save_frame()

        if cv2.waitKey(REFRESH_TIME) == ord('q'):
            cam.destroy()
            break


if __name__ == "__main__":
    show_video()
