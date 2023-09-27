import pytest
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.camera import Camera


@pytest.fixture(scope="function", params=(
    {"emergency_buff_size": 20, "detection_sensitivity": 1, "max_detection_sensitivity": 25, "min_motion_contour_area": 10, "fps": 100, "camera_number": 0, "recording_mode": "Gray"},
    
    {"emergency_buff_size": 200, "detection_sensitivity": 10, "max_detection_sensitivity": 15, "min_motion_contour_area": 1000, "fps": 24, "camera_number": 0, "recording_mode": "Sharpened"}
))
def camera_params(request):
    yield request.param


@pytest.fixture(name="camera", scope="function")
def make_camera(camera_params):
    camera = Camera(camera_params["emergency_buff_size"], camera_params["detection_sensitivity"], camera_params     ["max_detection_sensitivity"],camera_params["min_motion_contour_area"], camera_params["fps"], camera_params["camera_number"], camera_params["recording_mode"])
    
    yield camera
    
    camera.destroy()
