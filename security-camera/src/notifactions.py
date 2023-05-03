from plyer import notification
from PIL import Image

TMP_IMG_NAME = "tmp"


def send_system_notification(path_to_photo, title, message):
    img = Image.open(path_to_photo)
    img_converted = img.convert("P", palette=Image.ADAPTIVE, colors=32)
    img_converted.save(TMP_IMG_NAME + ".ico")

    notification.notify(
        title=title,
        message=message,
        app_icon=TMP_IMG_NAME + ".ico")
