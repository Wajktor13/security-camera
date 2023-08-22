import matplotlib.pyplot as plt
from matplotlib import pyplot
from matplotlib import ticker
from stats_data_manager import StatsDataManager
from datetime import datetime


class StatsDataVisualizer:
    """
    Class responsible for transforming and visualizing statistical data in matplotlib.
    """

    def __init__(self, db_path):
        self.__stats_data_manager = StatsDataManager(db_path)

    def transform_motion_detection_data(self, date_from, date_to):
        """
        Filters motion detection data and prepares it for plotting.
        :param date_from starting date in milliseconds
        :param date_to ending date in milliseconds
        :return: x, y ready for plotting
        """

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
        """
        Plots motion detection data between provided dates.
        :param date_from starting date in milliseconds
        :param date_to ending date in milliseconds
        :return: None
        """

        xs, ys = self.transform_motion_detection_data(date_from, date_to)
        fig, ax = pyplot.subplots()
        pyplot.scatter(xs, ys, color='red')
        pyplot.gcf().autofmt_xdate()
        ax.xaxis.set_major_locator(ticker.MaxNLocator(12))
        plt.yticks([])
        plt.ylabel('motion detected')
        plt.xlabel('datetime')
        pyplot.show()

    def transform_surveillance_data(self, date_from, date_to):
        """
        Filters surveillance data and prepares it for plotting.
        :param date_from starting date in milliseconds
        :param date_to ending date in milliseconds
        :return: x, y ready for plotting
        """

        surveillance_data = self.__stats_data_manager.fetch_surveillance_log()
        surveillance_data.sort(key=lambda log: log[0])
        surveillance_data_between_dates = []

        i = 0
        while i < len(surveillance_data) and surveillance_data[i][0] < date_from:
            i += 1
        while i < len(surveillance_data) and surveillance_data[i][0] <= date_to:
            dt = datetime.fromtimestamp(surveillance_data[i][0] / 1000)

            if surveillance_data[i][1] == 'ON':
                surveillance_data_between_dates.append((str(dt)[5:16], 'OFF'))
            else:
                surveillance_data_between_dates.append((str(dt)[5:16], 'ON'))

            surveillance_data_between_dates.append((str(dt)[5:16], surveillance_data[i][1]))
            i += 1

        return [log[0] for log in surveillance_data_between_dates],\
            [1 if log[1] == 'ON' else 0 for log in surveillance_data_between_dates]

    def show_surveillance_plot(self, date_from, date_to):
        """
        Plots surveillance data between provided dates.
        :param date_from starting date in milliseconds
        :param date_to ending date in milliseconds
        :return: None
        """

        xs, ys = self.transform_surveillance_data(date_from, date_to)
        fig, ax = pyplot.subplots()
        pyplot.gcf().autofmt_xdate()
        ax.xaxis.set_major_locator(ticker.MaxNLocator(12))
        pyplot.plot(xs, ys)
        plt.yticks([])
        plt.ylabel('surveillance on')
        plt.xlabel('datetime')
        pyplot.show()

    def show_notification_plot(self):
        pass
