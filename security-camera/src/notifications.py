import logging
from plyer import notification
from PIL import Image
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP_SSL


class NotificationSender:
    def __init__(self):
        # logging
        self.__logger = logging.getLogger("security_camera_logger")

        self.tmp_img_path = "tmp/tmp"

    def send_system_notification(self, path_to_photo, title, message):
        img = Image.open(path_to_photo)
        img_converted = img.convert("P", palette=Image.ADAPTIVE, colors=32)
        img_converted.save(self.tmp_img_path + ".ico")

        notification.notify(
            title=title,
            message=message,
            app_icon=self.tmp_img_path + ".ico")

        self.__logger.info("sent system notification")

    def send_email_notification(self, recipient, subject, body):
        port = 465
        smtp_server = "smtp.gmail.com"
        sender_email = "guard.camera,alert@gmail.com"
        # todo: how to safely store password?
        sender_password = ""

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = subject
        body = MIMEText(body)
        msg.attach(body)

        try:
            server = SMTP_SSL(smtp_server, port)
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient, msg.as_string())
            server.quit()
            self.__logger.info("sent email notification")
        except:
            self.__logger.info("failed to send email notification")
