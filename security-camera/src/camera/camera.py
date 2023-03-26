import cv2
from numpy import ones


class Camera:
    '''

        class responsible for handling input from the video source

    '''

    def __init__(self):
        self.capture = cv2.VideoCapture(0)  # might cause error
        self.frame_size = (int(self.capture.get(3)), int(self.capture.get(4)))
        self.fourcc_codec = cv2.VideoWriter_fourcc(*"mp4v")  # todo: mkv might be better, tests needed
        self.frame = None

        # todo: config
        self.max_detection_sensitivity = 15
        self.kernel = (3, 3)
        self.min_motion_rectangle_area = 1000

        # todo: how to adjust it?
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    def validate_capture(self):
        return self.capture.isOpened()

    def release_capture(self):
        self.capture.release()

    def refresh_frame(self):
        success, self.frame = self.capture.read()

        return success

    def show_window(self):
        cv2.imshow('Capture', self.frame)

    def search_for_motion(self):
        if not self.refresh_frame():
            return False

        frame1 = self.frame

        # todo: some delay ?? might not be needed

        if not self.refresh_frame():
            return False

        frame2 = self.frame

        gray_diff = cv2.absdiff(self.convert_frame_to_gray(frame1, self.kernel),
                                self.convert_frame_to_gray(frame2, self.kernel))
        binary_diff = \
            cv2.threshold(gray_diff, thresh=(self.max_detection_sensitivity + 1 - self.max_detection_sensitivity)
                                            * self.max_detection_sensitivity, maxval=255, type=cv2.THRESH_BINARY)[1]
        binary_diff = cv2.dilate(binary_diff, ones(self.kernel), 1)

        contours = cv2.findContours(binary_diff, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)[0]

        for contour in contours:
            if cv2.contourArea(contour) >= self.min_motion_rectangle_area:
                return True

    @staticmethod
    def convert_frame_to_gray(frame, kernel):
        return cv2.GaussianBlur(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), kernel, sigmaX=0)
