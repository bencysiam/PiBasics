from picamera import PiCamera
import time

cam = PiCamera()
cam.start_preview()
time.sleep(30)
cam.stop_preview()
