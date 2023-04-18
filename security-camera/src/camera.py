import cv2
import numpy as np
import time
from threading import Thread
from collections import deque
from platform import system


class Camera:
    '''
        class responsible for handling input from the video source, detecting motion, saving videos
    '''

    def __init__(self, emergency_buff_size, detection_sensitivity, max_detection_sensitivity,
                 min_motion_rectangle_area):
        '''
            user's config
        '''
        self.min_motion_contour_area = min_motion_rectangle_area
        self.emergency_buff_size = emergency_buff_size
        self.detection_sensitivity = detection_sensitivity
        self.max_detection_sensitivity = max_detection_sensitivity
        self.camera_number = 0  # todo: should user set which camera to use?

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
        self.emergency_buffered_frames = deque()
        self.emergency_fps = 45

        '''
            other settings
        '''
        # todo: look for h264 lib for linux
        if system() == "Windows":
            self.fourcc_codec = cv2.VideoWriter_fourcc(*'h264')
            self.capture = cv2.VideoCapture(self.camera_number, cv2.CAP_DSHOW)
        else:
            self.fourcc_codec = cv2.VideoWriter_fourcc(*'mp4v')
            self.capture = cv2.VideoCapture(self.camera_number)

        self.frame_size = (640, 480)
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
            frame_to_save = np.copy(self.frame)

            if self.validate_frame(frame_to_save):
                '''
                    updating buffered frames
                '''
                self.emergency_buffered_frames.append(frame_to_save)

                if len(self.emergency_buffered_frames) > self.emergency_buff_size:
                    self.emergency_buffered_frames.popleft()

        return success

    def show_window(self):
        if self.validate_frame(self.frame):
            cv2.imshow('Capture', self.frame)

    def get_motion_contours(self, frame1, frame2):
        if not self.validate_frame(frame1) or not self.validate_frame(frame2):
            return None

        gray_diff = cv2.absdiff(self.convert_frame_to_gray_gb(frame1, self.kernel),
                                self.convert_frame_to_gray_gb(frame2, self.kernel))
        binary_diff = \
            cv2.threshold(gray_diff, thresh=(self.max_detection_sensitivity + 1 - self.detection_sensitivity)
                                            * self.max_detection_sensitivity, maxval=255, type=cv2.THRESH_BINARY)[1]
        binary_diff = cv2.dilate(binary_diff, np.ones(self.kernel), 1)

        return cv2.findContours(binary_diff, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)[0]
    
    def get_two_frames(self):
        frame1 = np.copy(self.frame)

        if not self.refresh_frame() or not self.validate_frame(frame1):
            return (False, None, None)

        frame2 = np.copy(self.frame)

        if not self.validate_frame(frame2):
            return (False, None, None)
        
        return (True, frame1, frame2)

    def search_for_motion(self):
        success, frame1, frame2 = self.get_two_frames()

        if not success:
            return False

        contours = self.get_motion_contours(frame1, frame2)

        if contours is not None:
            for contour in contours:
                if cv2.contourArea(contour) >= self.min_motion_contour_area:
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
        
        frame_to_save = np.copy(self.frame)

        if self.validate_frame(frame_to_save) and self.recording_output is not None:
            try:
                self.recording_output.write(frame_to_save)
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

        frame_to_save = np.copy(self.frame)
        self.emergency_buffered_frames.append(frame_to_save)

    def write_emergency_buffer(self):
        if self.emergency_output is not None:
            while self.emergency_started or len(self.emergency_buffered_frames) > 0:
                if len(self.emergency_buffered_frames) > 0:
                    frame_to_save = self.emergency_buffered_frames.popleft()
                    if self.validate_frame(frame_to_save):
                        try:
                            self.emergency_output.write(frame_to_save)
                        except:
                            pass

    def stop_recording(self):
        self.recording_started = False
        if self.recording_output is not None:
            try:
                self.recording_output.release()
            except:
                # todo: sometimes makes video not work...
                pass

    def stop_emergency_recording(self):
        self.emergency_started = False
        if self.emergency_output is not None:
            try:
                self.emergency_output.release()
            except:
                pass

    def get_standard_frame(self):
        frame = np.copy(self.frame)
        if self.validate_frame(frame):
            return self.convert_frame_to_rgb(frame)

    def get_sharpened_frame(self):
        frame = np.copy(self.frame)
        if self.validate_frame(frame):
            kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])

            rgb_frame = self.convert_frame_to_rgb(self.frame)

            return cv2.filter2D(src=rgb_frame, ddepth=-1, kernel=kernel)

    def get_gray_frame(self):
        frame = np.copy(self.frame)
        if self.validate_frame(frame):
            return cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)

    def get_mexican_hat_effect_frame(self):
        frame = np.copy(self.frame)
        if self.validate_frame(frame):
            kernel = np.array([[0, 0, -1, 0, 0], [0, -1, -2, -1, 0], [-1, -2, 16, -2, -1],
                               [0, -1, -2, -1, 0], [0, 0, -1, 0, 0]])

            rgb_frame = self.convert_frame_to_rgb(self.frame)

            return cv2.filter2D(src=rgb_frame, ddepth=-1, kernel=kernel)

    def get_high_contrast_frame(self):
        frame = np.copy(self.frame)
        if self.validate_frame(frame):
            gray_frame = self.convert_frame_to_gray_gb(self.frame, self.kernel)

            return cv2.threshold(gray_frame, thresh=100, maxval=255, type=cv2.THRESH_BINARY)[1]

    def get_frame_with_contours(self):
        success, frame1, frame2 = self.get_two_frames()

        if not success:
            return None

        contours = self.get_motion_contours(frame1, frame2)

        if contours is not None:
            return self.convert_frame_to_rgb(cv2.drawContours(frame2, contours, -1, (0, 255, 0), 3))
        else:
            return frame2

    def get_frame_with_rectangles(self):
        success, frame1, frame2 = self.get_two_frames()

        if not success:
            return None

        contours = self.get_motion_contours(frame1, frame2)

        if contours is not None:
            for contour in contours:
                (x, y, w, h) = cv2.boundingRect(contour)
                if w > 30 and h > 30:
                    cv2.rectangle(frame2, (x - 5, y - 5), (x + w + 5, y + h + 5), (0, 255, 0), 2)

        return self.convert_frame_to_rgb(frame2)

    @staticmethod
    def convert_frame_to_gray_gb(frame, kernel):
        frame = np.copy(frame)
        if Camera.validate_frame(frame):
            return cv2.GaussianBlur(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), kernel, sigmaX=0)

    @staticmethod
    def convert_frame_to_rgb(frame):
        frame = np.copy(frame)
        if Camera.validate_frame(frame):
            return cv2.cvtColor(src=frame, code=cv2.COLOR_BGR2RGB)
    
    @staticmethod
    def validate_frame(frame):
        return frame is not None and str(frame) != 'None'
