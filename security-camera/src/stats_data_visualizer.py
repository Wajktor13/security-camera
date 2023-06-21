import matplotlib
from stats_data_manager import StatsDataManager


class StatsDataVisualizer:
    """Class responsible for visualizing statistical data"""

    def __init__(self):
        self.stats_data_manager = StatsDataManager("data/stats.sqlite")

    def show_motion_detection_plot(self):
        pass

    def show_surveillance_plot(self):
        pass

    def show_notification_plot(self):
        pass
