import cv2
import time
import logging
from camera import Camera
from notifications import NotificationSender


class Controller:
    """
        Class responsible for controlling the camera, surveillance logic
    """

    def __init__(self, refresh_time, emergency_recording_length, standard_recording_length, emergency_buff_length,
                 detection_sensitivity, max_detection_sensitivity, min_motion_rectangle_area, fps, camera_number,
                 send_system_notifications, min_delay_between_system_notifications, send_email_notifications,
                 min_delay_between_email_notifications):
        # logging
        self.__logger = logging.getLogger("security_camera_logger")

        # user's config
        self.refresh_time = refresh_time
        self.no_emergency_recording_frames = emergency_recording_length * fps
        self.no_standard_recording_frames = standard_recording_length * fps
        self.no_emergency_buff_frames = emergency_buff_length * fps
        self.detection_sensitivity = detection_sensitivity
        self.max_detection_sensitivity = max_detection_sensitivity
        self.min_motion_rectangle_area = min_motion_rectangle_area
        self.fps = fps
        self.camera_number = camera_number
        self.send_system_notifications = send_system_notifications
        self.min_delay_between_system_notifications = min_delay_between_system_notifications
        self.send_email_notifications = send_email_notifications
        self.min_delay_between_email_notifications = min_delay_between_email_notifications

        # other
        self.cam = None
        self.surveillance_running = False
        self.notification_sender = NotificationSender()

    def start_surveillance(self):
        """
            Opens the camera and starts surveillance.
            :return: None
        """

        self.surveillance_running = True
        emergency_recording_loaded_frames = 0
        standard_recording_loaded_frames = 0
        last_system_notification_time = None
        last_email_notification_time = None

        while self.cam is None or not self.cam.validate_capture():

            # opening input stream failed - try again

            self.__logger.warning("failed to open input stream")

            self.cam = Camera(emergency_buff_size=self.no_emergency_buff_frames,
                              detection_sensitivity=self.detection_sensitivity,
                              max_detection_sensitivity=self.max_detection_sensitivity,
                              min_motion_contour_area=self.min_motion_rectangle_area,
                              fps=self.fps,
                              camera_number=self.camera_number)

            time.sleep(0.005)

        while self.surveillance_running and self.cam is not None:
            self.cam.refresh_frame()

            '''
                standard recording
            '''
            # refresh frame and save it to standard recording
            if self.surveillance_running:
                self.cam.write_standard_recording_frame()
                standard_recording_loaded_frames += 1

            # check if standard recording should end
            if standard_recording_loaded_frames >= self.no_standard_recording_frames:
                self.cam.stop_standard_recording()
                standard_recording_loaded_frames = 0

            '''
                emergency recording
            '''
            # check if emergency recording should start
            if not self.cam.emergency_recording_started:
                if self.cam.search_for_motion() and self.surveillance_running:
                    self.__logger.info("motion detected")
                    self.cam.save_emergency_recording_frame(controller=self)

                    if self.send_system_notifications and (last_system_notification_time is None or
                                                           time.time() - last_system_notification_time >
                                                           self.min_delay_between_system_notifications):
                        last_system_notification_time = time.time()
                        self.cam.save_frame_to_img(self.notification_sender.tmp_img_path + ".jpg")

                        self.notification_sender.send_system_notification(
                            path_to_photo=self.notification_sender.tmp_img_path + ".jpg",
                            title="Security Camera",
                            message="Motion detected!")

                    if self.send_email_notifications and (last_email_notification_time is None or
                                                          time.time() - last_email_notification_time >
                                                          self.min_delay_between_system_notifications):
                        last_email_notification_time = time.time()
                        self.notification_sender.send_email_notification(recipient="wajktor007@gmail.com",
                                                                         subject="Motion detected!",
                                                                         body="Check recordings.",
                                                                         path_to_photo=self.notification_sender.tmp_img_path)

            # check if emergency recording should end
            elif emergency_recording_loaded_frames >= self.no_emergency_recording_frames:
                self.cam.stop_emergency_recording()
                emergency_recording_loaded_frames = 0

            # save frame to emergency recording
            else:
                self.cam.save_emergency_recording_frame(controller=self)
                emergency_recording_loaded_frames += 1

            # delay
            if cv2.waitKey(self.refresh_time) == ord('q'):
                self.cam.destroy()
                self.surveillance_running = False

        self.cam = None
