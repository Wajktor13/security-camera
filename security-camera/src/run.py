import cv2
from camera.camera import Camera
import time
import tkinter as tk
from PIL import Image, ImageTk


'''

* tests *

'''

REFRESH_TIME = 25

def show_video():
    cam = Camera()
    while not cam.validate_capture():
        print('cannot open input stream')
        time.sleep(1)
        cam = Camera()

    while True:
        cam.refresh_frame()
        cam.show_window()

        if cam.search_for_motion():
            print('motion detected')

        if cv2.waitKey(REFRESH_TIME) == ord('q'):
            cam.release_capture()
            break


if __name__ == "__main__":
    show_video()
