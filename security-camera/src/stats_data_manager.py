import logging
import sqlite3
from datetime import datetime


class StatsDataManager:
    """
    Class responsible for operations on database that stores data used for statistics.
    """

    def __init__(self, db_path):
        # logging
        self.__logger = logging.getLogger("security_camera_logger")

        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

        self.__logger.info("started connection")

    def create_tables(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS motion_detection_data
                              (id INTEGER PRIMARY KEY AUTOINCREMENT,
                               timestamp INTEGER)''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS surveillance_log
                              (id INTEGER PRIMARY KEY AUTOINCREMENT,
                               timestamp INTEGER,
                               log_type text)''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS notifications_log
                              (id INTEGER PRIMARY KEY AUTOINCREMENT,
                               timestamp INTEGER,
                               notification_type text)''')

        self.conn.commit()

        self.__logger.info("created tables")

    def insert_motion_detection_data(self):
        ts = int(datetime.now().timestamp() * 1000)
        self.cursor.execute("INSERT INTO motion_detection_data (timestamp) VALUES (?)", (ts,))
        self.conn.commit()

        self.__logger.info("inserted motion detection timestamp")

    def fetch_motion_detection_data(self):
        self.cursor.execute("SELECT timestamp FROM motion_detection_data")
        rows = self.cursor.fetchall()
        return rows

    def insert_surveillance_log(self, log_type):
        if log_type not in ('ON', 'OFF'):
            self.__logger.error('invalid log type')
        else:
            ts = int(datetime.now().timestamp() * 1000)
            self.cursor.execute("INSERT INTO surveillance_log (timestamp, log_type) VALUES (?, ?)", (ts, log_type))
            self.conn.commit()

            self.__logger.info("inserted surveillance log")

    def fetch_surveillance_log(self):
        self.cursor.execute("SELECT timestamp, log_type FROM surveillance_log")
        rows = self.cursor.fetchall()
        return rows

    def insert_notifications_log(self, notification_type):
        if notification_type not in ("email", "system"):
            self.__logger.error("invalid log type")
        else:
            ts = int(datetime.now().timestamp() * 1000)
            self.cursor.execute("INSERT INTO notifications_log (timestamp, notification_type) VALUES (?, ?)",
                                (ts, notification_type))
            self.conn.commit()

            self.__logger.info("inserted notification log")

    def fetch_notifications_log(self):
        self.cursor.execute("SELECT timestamp, notification_type FROM notifications_log")
        rows = self.cursor.fetchall()
        return rows

    def close_connection(self):
        self.conn.close()

        self.__logger.info("closed connection")
