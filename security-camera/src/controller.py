import cv2
import time
import logging
import gdrive
from threading import Thread
from camera import Camera
from notifications import NotificationSender
from stats_data_manager import StatsDataManager


class Controller:
    """Class responsible for controlling the camera, surveillance logic"""

    def __init__(self, refresh_time, emergency_recording_length, standard_recording_length, emergency_buff_length,
                 detection_sensitivity, max_detection_sensitivity, min_motion_rectangle_area, fps, camera_number,
                 send_system_notifications, min_delay_between_system_notifications, send_email_notifications,
                 min_delay_between_email_notifications, email_recipient, upload_to_gdrive):
        # logging
        self.__logger = logging.getLogger("security_camera_logger")

        # user's config
        self.emergency_recording_length = emergency_recording_length
        self.standard_recording_length = standard_recording_length
        self.emergency_buff_length = emergency_buff_length
        self.refresh_time = refresh_time
        self.detection_sensitivity = detection_sensitivity
        self.max_detection_sensitivity = max_detection_sensitivity
        self.min_motion_rectangle_area = min_motion_rectangle_area
        self.fps = fps
        self.camera_number = camera_number
        self.send_system_notifications = send_system_notifications
        self.min_delay_between_system_notifications = min_delay_between_system_notifications
        self.send_email_notifications = send_email_notifications
        self.min_delay_between_email_notifications = min_delay_between_email_notifications
        self.email_recipient = email_recipient
        self.upload_to_gdrive = upload_to_gdrive
        self.gdrive_folder_id = "1vS3JDBY38vPrzEfTwWBCuHtSn6sI7J7Y"

        # other
        self.no_emergency_recording_frames = emergency_recording_length * fps
        self.no_standard_recording_frames = standard_recording_length * fps
        self.no_emergency_buff_frames = emergency_buff_length * fps
        self.cam = None
        self.surveillance_running = False
        self.notification_sender = NotificationSender()
        self.stats_data_manager = None

    def update_parameters(self):
        if self.cam is not None:
            self.cam.emergency_buff_size = self.emergency_buff_length * self.fps
            self.cam.detection_sensitivity = self.detection_sensitivity
            self.cam.max_detection_sensitivity = self.max_detection_sensitivity
            self.cam.min_motion_contour_area = self.min_motion_rectangle_area
            self.cam.standard_recording_fps = self.cam.emergency_recording_fps = self.fps
            self.cam.camera_number = self.camera_number

            self.no_emergency_recording_frames = self.emergency_recording_length * self.fps
            self.no_standard_recording_frames = self.standard_recording_length * self.fps

    def start_surveillance(self):
        """Opens the camera and starts surveillance.
            :return: None"""

        self.surveillance_running = True
        emergency_recording_loaded_frames = 0
        standard_recording_loaded_frames = 0
        last_system_notification_time = None
        last_email_notification_time = None

        self.stats_data_manager = StatsDataManager("data/stats.sqlite")
        self.stats_data_manager.insert_surveillance_log("ON")

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

            '''standard recording'''
            # refresh frame and save it to standard recording
            if self.surveillance_running:
                self.cam.write_standard_recording_frame()
                standard_recording_loaded_frames += 1

            # check if standard recording should end
            if standard_recording_loaded_frames >= self.no_standard_recording_frames:
                self.cam.stop_standard_recording()
                standard_recording_loaded_frames = 0

            '''emergency recording'''
            # check if emergency recording should start
            if not self.cam.emergency_recording_started:
                if self.cam.search_for_motion() and self.surveillance_running:
                    self.__logger.info("motion detected")
                    self.cam.save_emergency_recording_frame(controller=self)

                    self.stats_data_manager.insert_motion_detection_data()

                    if self.send_system_notifications and (last_system_notification_time is None or
                                                           time.time() - last_system_notification_time >
                                                           self.min_delay_between_system_notifications):
                        last_system_notification_time = time.time()

                        self.cam.save_frame_to_img(self.notification_sender.tmp_img_path + ".jpg")

                        system_notification_thread = Thread(target=self.notification_sender.send_system_notification,
                                                            args=[self.notification_sender.tmp_img_path + ".jpg",
                                                                  "Security Camera", "Motion detected!"])

                        system_notification_thread.start()
                        self.__logger.info("system notification thread started")

                        self.stats_data_manager.insert_notifications_log("system")

                    if self.send_email_notifications and (last_email_notification_time is None or
                                                          time.time() - last_email_notification_time >
                                                          self.min_delay_between_email_notifications):
                        last_email_notification_time = time.time()

                        email_notification_thread = Thread(target=self.notification_sender.send_email_notification,
                                                           args=[self.email_recipient,
                                                                 "motion detected!",
                                                                 "check recordings",
                                                                 self.notification_sender.tmp_img_path])

                        email_notification_thread.start()
                        self.__logger.info("email notification thread started")

                        self.stats_data_manager.insert_notifications_log("email")

            # check if emergency recording should end
            elif emergency_recording_loaded_frames >= self.no_emergency_recording_frames:
                file_path = self.cam.stop_emergency_recording()
                emergency_recording_loaded_frames = 0

                if self.upload_to_gdrive and file_path is not None:
                    gdrive_upload_thread = Thread(target=gdrive.upload_to_cloud,
                                                  args=[
                                                      file_path,
                                                      (file_path.split("/"))[-1],
                                                      self.gdrive_folder_id])

                    gdrive_upload_thread.start()
                    self.__logger.info("system notification thread started")

            # save frame to emergency recording
            else:
                self.cam.save_emergency_recording_frame(controller=self)
                emergency_recording_loaded_frames += 1

            # delay
            if cv2.waitKey(self.refresh_time) == ord("q"):
                self.cam.destroy()
                self.surveillance_running = False

        self.cam = None
        self.stats_data_manager.insert_surveillance_log("OFF")
        self.stats_data_manager.close_connection()
        self.stats_data_manager = None
