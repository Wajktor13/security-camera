import matplotlib.pyplot as plt
from matplotlib import pyplot
from matplotlib import ticker
from stats_data_manager import StatsDataManager
from datetime import datetime


class StatsDataVisualizer:
    """Class responsible for transforming and visualizing statistical data in matplotlib"""

    def __init__(self, db_path):
        self.__stats_data_manager = StatsDataManager(db_path)

    def transform_motion_detection_data(self, date_from, date_to):
        """Filters motion detection data and prepares it for plotting.
            :param date_from starting date in milliseconds
            :param date_to ending date in milliseconds
            :return: x, y ready for plotting"""

        motion_detection_data = self.__stats_data_manager.fetch_motion_detection_data()
        motion_detection_data = [log[0] for log in motion_detection_data]
        motion_detection_data.sort()

        motion_detection_data_between_dates = []

        i = 0
        while i < len(motion_detection_data) and motion_detection_data[i] < date_from:
            i += 1
        while i < len(motion_detection_data) and motion_detection_data[i] <= date_to:
            dt = datetime.fromtimestamp(motion_detection_data[i] / 1000)
            motion_detection_data_between_dates.append(str(dt)[5:16])
            i += 1

        return motion_detection_data_between_dates, [1 for _ in range(len(motion_detection_data_between_dates))]

    def show_motion_detection_plot(self, date_from, date_to):
        """Plots motion detection data between provided dates.
            :param date_from starting date in milliseconds
            :param date_to ending date in milliseconds
            :return: None"""

        xs, ys = self.transform_motion_detection_data(date_from, date_to)
        fig, ax = pyplot.subplots()
        pyplot.scatter(xs, ys, color='red')
        pyplot.gcf().autofmt_xdate()
        ax.xaxis.set_major_locator(ticker.MaxNLocator(12))
        plt.yticks([])
        plt.ylabel('motion detected')
        plt.xlabel('datetime')
        pyplot.show()

    def show_surveillance_plot(self):
        pass

    def show_notification_plot(self):
        pass
