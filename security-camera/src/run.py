import logging
import time
from gui import SecurityCameraApp


if __name__ == "__main__":
    logging.basicConfig(filename="../logs/" + time.strftime("%d-%m-%Y", time.localtime(time.time())) + ".log",
                        level=logging.DEBUG,
                        format="[%(asctime)s]:[%(levelname)s]:[%(module)s]:%(message)s")
    logger = logging.getLogger("security_camera_logger")
    logger.info("security camera started")

    app = SecurityCameraApp()
    app.mainloop()
    