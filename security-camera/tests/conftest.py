import pytest
import os
import sys
import numpy as np

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.camera import Camera


@pytest.fixture(scope="function", params=(
    {"emergency_buff_size": 10, "detection_sensitivity": 1, "max_detection_sensitivity": 25, "min_motion_contour_area": 10, "fps": 100, "camera_number": 0, "recording_mode": "Gray"},
    
    {"emergency_buff_size": 200, "detection_sensitivity": 10, "max_detection_sensitivity": 15, "min_motion_contour_area": 1000, "fps": 24, "camera_number": 0, "recording_mode": "Sharpened"},
    
    {"emergency_buff_size": 12011, "detection_sensitivity": 100, "max_detection_sensitivity": 1555, "min_motion_contour_area": 1, "fps": 1440, "camera_number": 0, "recording_mode": "Standard"}
))
def camera_params(request):
    yield request.param


@pytest.fixture(name="camera", scope="function")
@pytest.mark.usefixtures("camera_params")
def make_camera(camera_params):
    camera = Camera(camera_params["emergency_buff_size"], camera_params["detection_sensitivity"], 
                    camera_params["max_detection_sensitivity"],camera_params["min_motion_contour_area"], 
                    camera_params["fps"], camera_params["camera_number"], camera_params["recording_mode"])
    
    yield camera
    
    camera.destroy()


@pytest.fixture(name="frame_resolution", scope="module", params=((1, 1), (640, 480), (1280, 720), (1920, 1080),
                                                                 (2560, 1440), (3840, 2160)))
def frame_resolution(request):
    yield request.param


@pytest.fixture(name="random_frame")
@pytest.mark.usefixtures("frame_resolution")
def random_frame(frame_resolution):
    yield np.random.randint(0, 256, (frame_resolution[0], frame_resolution[1], 3), dtype="uint8")
    