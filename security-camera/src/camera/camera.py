import cv2
from numpy import ones
import time


class Camera:
    '''
        class responsible for handling input from the video source, detecting motion
    '''

    def __init__(self):
        '''
            config
        '''
        self.kernel = (3, 3)    # todo: Should user set it?
        self.min_motion_rectangle_area = 1000
        self.emergency_buff_size = 50
        self.frame_size = (1280, 720)   # todo: how to adjust it? Should user set it?
        self.detection_sensitivity = 12
        self.max_detection_sensitivity = 15

        '''
            standard recording
        '''
        self.recording_started = False
        self.recording_file_path = None
        self.recording_output = None

        '''
            emergency recording
        '''
        self.emergency_started = False
        self.emergency_file_path = None
        self.emergency_output = None
        self.emergency_buffered_frames = []

        '''
            other settings
        '''
        self.fourcc_codec = cv2.VideoWriter_fourcc(*'H264')
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_size[0])
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_size[1])
        self.capture = cv2.VideoCapture(0)
        self.frame = None

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
        # if not self.refresh_frame():
        #     return False

        frame1 = self.frame

        # todo: some delay ?? Might not be needed

        if not self.refresh_frame():
            return False

        frame2 = self.frame

        gray_diff = cv2.absdiff(self.convert_frame_to_gray(frame1, self.kernel),
                                self.convert_frame_to_gray(frame2, self.kernel))
        binary_diff = \
            cv2.threshold(gray_diff, thresh=(self.max_detection_sensitivity + 1 - self.detection_sensitivity)
                                            * self.max_detection_sensitivity, maxval=255, type=cv2.THRESH_BINARY)[1]
        binary_diff = cv2.dilate(binary_diff, ones(self.kernel), 1)

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
            self.recording_output = cv2.VideoWriter(self.recording_file_path, self.fourcc_codec, 20, self.frame_size)

            '''
                insert buffered frames into output video
            '''

        self.recording_output.write(self.frame)

    def emergency_save_frame(self):
        if not self.emergency_started:
            '''
                set new emergency recording
            '''

            self.emergency_started = True
            current_recording_time = time.strftime("%d-%m-%Y_%H-%M-%S", time.localtime(time.time()))
            self.emergency_file_path = f'../recordings/emergency/{current_recording_time}.mkv'
            self.emergency_output = cv2.VideoWriter(self.emergency_file_path, self.fourcc_codec, 20, self.frame_size)

            '''
                insert buffered frames into output video
            '''

            for buffered_frame in self.emergency_buffered_frames:
                self.emergency_output.write(buffered_frame)

        self.emergency_output.write(self.frame)

    def stop_recording(self):
        if self.recording_output is not None:
            self.recording_output.release()
        self.recording_started = False

    def stop_emergency_recording(self):
        if self.emergency_output is not None:
            self.emergency_output.release()
        self.emergency_started = False

    @staticmethod
    def convert_frame_to_gray(frame, kernel):
        return cv2.GaussianBlur(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), kernel, sigmaX=0)
