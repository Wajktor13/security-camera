import pytest
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.camera import Camera


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