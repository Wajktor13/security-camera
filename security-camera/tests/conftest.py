import pytest
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.camera import Camera


@pytest.fixture(scope="module", params=(
    {"emergency_buff_size": 20, "detection_sensitivity": 1, "max_detection_sensitivity": 25, "min_motion_contour_area": 10, "fps": 100, "camera_number": 0, "recording_mode": "Gray"},
))
def camera_params(request):
    yield request.param


@pytest.fixture(name="camera", scope="module")
def make_camera(camera_params):
    return Camera(camera_params["emergency_buff_size"], camera_params["detection_sensitivity"], camera_params     ["max_detection_sensitivity"],camera_params["min_motion_contour_area"], camera_params["fps"], camera_params["camera_number"], camera_params["recording_mode"])

