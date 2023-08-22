import logging
import os
from plyer import notification
from PIL import Image
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from smtplib import SMTP_SSL
from json import load


class NotificationSender:

    """
    Class responsible for sending system and email notifications.
    """

    def __init__(self):
        # logging
        self.__logger = logging.getLogger("security_camera_logger")
        
        self.tmp_img_path = "../tmp/tmp"
        self.email_login_data_path = "../config/notification_email_credentials.json"

    def send_system_notification(self, path_to_photo, title, message):
        self.prepare_photo(path_to_photo)

        notification.notify(
            title=title,
            message=message,
            app_icon=self.tmp_img_path + ".ico")

        self.__logger.info("sent system notification")

    def send_email_notification(self, recipient, subject, body, path_to_photo):
        path_to_photo += ".jpg"
        with open(path_to_photo, "rb") as f:
            img_data = f.read()

        port = 465
        smtp_server = "smtp.gmail.com"
        login_data = load(open(self.email_login_data_path))
        sender_email = login_data["login"]
        application_password = login_data["applicationPassword"]

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient
        msg["Subject"] = subject
        body = MIMEText(body)
        msg.attach(body)
        img = MIMEImage(img_data, name=os.path.basename(path_to_photo))
        msg.attach(img)

        try:
            server = SMTP_SSL(smtp_server, port)
            server.login(sender_email, application_password)
            server.sendmail(sender_email, recipient, msg.as_string())
            server.quit()
            self.__logger.info("sent email notification")
        except:
            self.__logger.exception("failed to send email notification")

    def prepare_photo(self, path_to_photo):
        img = Image.open(path_to_photo)
        img_converted = img.convert("P", palette=Image.ADAPTIVE, colors=32)
        img_converted.save(self.tmp_img_path + ".ico")
