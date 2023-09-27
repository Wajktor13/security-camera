from src.camera import Camera
import pytest
import os
import sys
import numpy as np

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


@pytest.mark.usefixtures("camera")
def test_capture(camera: Camera):
    assert camera.validate_capture()


@pytest.mark.usefixtures("camera")
def test_destroy(camera: Camera):
    assert camera.validate_capture()

    camera.destroy()

    assert not camera.validate_capture()
    assert not camera.emergency_recording_started
    assert not camera.standard_recording_started


@pytest.mark.usefixtures("camera")
def test_refresh_frame_no_capture(camera: Camera):
    assert camera.validate_capture()
    
    camera.destroy()

    assert not camera.validate_capture()


@pytest.mark.usefixtures("camera")
def test_validate_frame(camera: Camera):
    assert not camera.validate_frame(None)
    assert not camera.validate_frame("None")
    
    for resolution in ((1, 1), (1280, 720), (1920, 1080), (2560, 1440)):
        assert camera.validate_frame(np.random.choice(range(256), resolution))