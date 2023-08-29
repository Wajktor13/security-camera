import logging
from json import load, dump


class ControllerSettingsManager:
    """
    Class responsible for loading and saving user's settings to JSON file.
    """

    def __init__(self, settings_file_path):
        # logging
        self.__logger = logging.getLogger("security_camera_logger")

        self.settings_file_path = settings_file_path

    def load_settings(self, controller):
        try:
            settings_data = load(open(self.settings_file_path))
        except OSError:
            self.__logger.exception("failed to open controller settings file")
            return

        controller.emergency_recording_length = settings_data["emergency_recording_length"]
        controller.standard_recording_length = settings_data["standard_recording_length"]
        controller.emergency_buff_length = settings_data["emergency_buff_length"]
        controller.refresh_time = settings_data["refresh_time"]
        controller.detection_sensitivity = settings_data["detection_sensitivity"]
        controller.max_detection_sensitivity = settings_data["max_detection_sensitivity"]
        controller.min_motion_rectangle_area = settings_data["min_motion_rectangle_area"]
        controller.fps = settings_data["fps"]
        controller.camera_number = settings_data["camera_number"]
        controller.send_system_notifications = settings_data["send_system_notifications"]
        controller.min_delay_between_system_notifications = settings_data["min_delay_between_system_notifications"]
        controller.send_email_notifications = settings_data["send_email_notifications"]
        controller.min_delay_between_email_notifications = settings_data["min_delay_between_email_notifications"]
        controller.email_recipient = settings_data["email_recipient"]
        controller.upload_to_gdrive = settings_data["upload_to_gdrive"]
        controller.save_recordings_locally = settings_data["save_recordings_locally"]
        controller.gdrive_folder_id = settings_data["gdrive_folder_id"]
        controller.disable_preview = settings_data["disable_preview"]
        controller.recording_mode = settings_data["recording_mode"]

    def save_settings(self, controller):
        settings_data = {
            "emergency_recording_length": controller.emergency_recording_length,
            "standard_recording_length": controller.standard_recording_length,
            "emergency_buff_length": controller.emergency_buff_length,
            "refresh_time": controller.refresh_time,
            "detection_sensitivity": controller.detection_sensitivity,
            "max_detection_sensitivity": controller.max_detection_sensitivity,
            "min_motion_rectangle_area": controller.min_motion_rectangle_area,
            "fps": controller.fps,
            "camera_number": controller.camera_number,
            "send_system_notifications": controller.send_system_notifications,
            "min_delay_between_system_notifications": controller.min_delay_between_system_notifications,
            "send_email_notifications": controller.send_email_notifications,
            "min_delay_between_email_notifications": controller.min_delay_between_email_notifications,
            "email_recipient": controller.email_recipient,
            "upload_to_gdrive": controller.upload_to_gdrive,
            "save_recordings_locally": controller.save_recordings_locally,
            "gdrive_folder_id": controller.gdrive_folder_id,
            "disable_preview": controller.disable_preview,
            "recording_mode": controller.recording_mode
        }

        with open(self.settings_file_path, 'w') as settings_file:
            dump(settings_data, settings_file)
