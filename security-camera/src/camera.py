import cv2
import numpy as np
import time
from threading import Thread


class Camera:
    '''
        class responsible for handling input from the video source, detecting motion, saving videos
    '''

    def __init__(self, emergency_buff_size, detection_sensitivity, max_detection_sensitivity,
                 min_motion_rectangle_area):
        '''
            user's config
        '''
        self.min_motion_rectangle_area = min_motion_rectangle_area
        self.emergency_buff_size = emergency_buff_size
        self.detection_sensitivity = detection_sensitivity
        self.max_detection_sensitivity = max_detection_sensitivity
        self.frame_size = (1280, 720)  # todo: how to adjust it? Should user set it?

        '''
            standard recording
        '''
        self.recording_started = False
        self.recording_file_path = None
        self.recording_output = None
        self.recording_fps = 20

        '''
            emergency recording
        '''
        self.emergency_started = False
        self.emergency_file_path = None
        self.emergency_output = None
        self.emergency_buffered_frames = []  # todo: replace with queue
        self.emergency_fps = 40

        '''
            other settings
        '''
        self.fourcc_codec = cv2.VideoWriter_fourcc(*'h264')  # todo: add linux support
        self.capture = cv2.VideoCapture(0)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_size[0])
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_size[1])
        self.frame = None
        self.kernel = (3, 3)

    def validate_capture(self):
        return self.capture.isOpened()

    def destroy(self):
        self.stop_emergency_recording()
        self.stop_recording()
        self.capture.release()
        cv2.destroyAllWindows()

    def refresh_frame(self):
        success, self.frame = self.capture.read()

        if success:
            '''
                updating buffered frames
            '''
            self.emergency_buffered_frames.append(self.frame)

            if len(self.emergency_buffered_frames) > self.emergency_buff_size:
                self.emergency_buffered_frames.pop(0)

        return success

    def show_window(self):
        cv2.imshow('Capture', self.frame)

    def search_for_motion(self):
        frame1 = self.frame

        if not self.refresh_frame():
            return False

        frame2 = self.frame

        gray_diff = cv2.absdiff(self.convert_frame_to_gray_gb(frame1, self.kernel),
                                self.convert_frame_to_gray_gb(frame2, self.kernel))
        binary_diff = \
            cv2.threshold(gray_diff, thresh=(self.max_detection_sensitivity + 1 - self.detection_sensitivity)
                                            * self.max_detection_sensitivity, maxval=255, type=cv2.THRESH_BINARY)[1]
        binary_diff = cv2.dilate(binary_diff, np.ones(self.kernel), 1)

        contours = cv2.findContours(binary_diff, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)[0]

        for contour in contours:
            if cv2.contourArea(contour) >= self.min_motion_rectangle_area:
                '''
                    motion detected
                '''

                return True

        return False

    def save_frame(self):
        if not self.recording_started:
            '''
                set new recording
            '''
            self.recording_started = True
            current_recording_time = time.strftime("%d-%m-%Y_%H-%M-%S", time.localtime(time.time()))
            self.recording_file_path = f'../recordings/standard/{current_recording_time}.mkv'
            self.recording_output = cv2.VideoWriter(self.recording_file_path, self.fourcc_codec, self.recording_fps,
                                                    self.frame_size)

        if self.frame is not None and self.recording_output is not None:
            try:
                self.recording_output.write(self.frame)
            except:
                # lost frame - log it
                pass

    def emergency_save_frame(self):
        if not self.emergency_started:
            '''
                set new emergency recording
            '''
            self.emergency_started = True
            current_recording_time = time.strftime("%d-%m-%Y_%H-%M-%S", time.localtime(time.time()))
            self.emergency_file_path = f'../recordings/emergency/{current_recording_time}.mkv'
            self.emergency_output = cv2.VideoWriter(self.emergency_file_path, self.fourcc_codec, self.emergency_fps,
                                                    self.frame_size)

            '''
                creating and starting thread that creates emergency video
            '''
            emergency_buff_write_thread = Thread(target=self.write_emergency_buffer)
            emergency_buff_write_thread.start()

        if self.frame is not None:
            self.emergency_buffered_frames.append(self.frame)

    def write_emergency_buffer(self):
        while self.emergency_started or len(self.emergency_buffered_frames) > 0:
            if len(self.emergency_buffered_frames) > 0:
                self.emergency_output.write(self.emergency_buffered_frames.pop(0))

    def stop_recording(self):
        self.recording_started = False
        if self.recording_output is not None:
            try:
                self.recording_output.release()
            except:
                # todo: sometimes makes video not working...
                pass

    def stop_emergency_recording(self):
        self.emergency_started = False
        if self.emergency_output is not None:
            try:
                self.emergency_output.release()
            except:
                pass

    def get_standard_frame(self):
        if self.frame is not None:
            return self.convert_frame_to_rgb(self.frame)

    def get_sharpened_frame(self):
        if self.frame is not None:
            kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])

            rgb_frame = self.convert_frame_to_rgb(self.frame)

            return cv2.filter2D(src=rgb_frame, ddepth=-1, kernel=kernel)

    def get_gray_frame(self):
        if self.frame is not None:
            return cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)

    def get_mexican_hat_effect_frame(self):
        if self.frame is not None:
            kernel = np.array([[0, 0, -1, 0, 0], [0, -1, -2, -1, 0], [-1, -2, 16, -2, -1],
                               [0, -1, -2, -1, 0], [0, 0, -1, 0, 0]])

            rgb_frame = self.convert_frame_to_rgb(self.frame)

            return cv2.filter2D(src=rgb_frame, ddepth=-1, kernel=kernel)

    def get_high_contrast_frame(self):
        if self.frame is not None:
            gray_frame = self.convert_frame_to_gray_gb(self.frame, self.kernel)

            return cv2.threshold(gray_frame, thresh=100, maxval=255, type=cv2.THRESH_BINARY)[1]

    @staticmethod
    def convert_frame_to_gray_gb(frame, kernel):
        if frame is not None:
            return cv2.GaussianBlur(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), kernel, sigmaX=0)

    @staticmethod
    def convert_frame_to_rgb(frame):
        if frame is not None:
            return cv2.cvtColor(src=frame, code=cv2.COLOR_BGR2RGB)
