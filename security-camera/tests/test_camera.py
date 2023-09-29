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


@pytest.mark.usefixtures("camera", "random_frame")
def test_validate_frame(camera: Camera, random_frame):
    assert not camera.validate_frame(None)
    assert not camera.validate_frame("None")
    
    for _ in range(100):
        assert camera.validate_frame(random_frame)


@pytest.mark.usefixtures("camera", "random_frame")
def test_update_emergency_buffer(camera: Camera, random_frame):
    for i in range(1, min(camera.emergency_buff_size, 30)):
        camera._Camera__frame_new = random_frame
        camera.update_emergency_buffer()

        assert len(camera._Camera__emergency_recording_buffered_frames) == i


@pytest.mark.usefixtures("camera")
def test_stop_standard_recording(camera: Camera):
    camera.standard_recording_started = True
    camera.stop_standard_recording()

    assert not camera.standard_recording_started


@pytest.mark.usefixtures("camera")
def test_stop_emergency_recording(camera: Camera):
    camera.emergency_recording_started = True
    camera.stop_emergency_recording()

    assert not camera.emergency_recording_started
    

@pytest.mark.usefixtures("camera", "random_frame")
def test_get_frame(camera: Camera, random_frame):
    for get_frame_with_mode in camera.frame_modes.values():
        for _ in range(5):
            camera._Camera__frame_old = random_frame
            camera._Camera__frame_new = random_frame
                
            assert camera.validate_frame(get_frame_with_mode())
    