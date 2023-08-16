import logging
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive


def upload_to_cloud(file_path, file_upload_name, gdrive_folder_id):
    logger = logging.getLogger("security_camera_logger")

    try:
        gauth = GoogleAuth(settings_file="../config/google_drive/settings.yaml")
        drive = GoogleDrive(gauth)
        upload_file = file_path
        gfile = drive.CreateFile({"parents": [{"id": gdrive_folder_id}]})
        gfile["title"] = file_upload_name
        gfile.SetContentFile(upload_file)
        gfile.Upload()
    except:
        logger.exception("failed to upload emergency video to gdrive")
        return

    logger.info("uploaded emergency video to gdrive")
