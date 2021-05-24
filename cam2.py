from picamera import PiCamera
import time

cam = PiCamera()
cam.start_preview()

time.sleep(2)

cam.vflip = True
time.sleep(3)
cam.vflip = True
time.sleep(1)

for i in range(0, 100, 1):
    cam.brightness = i
    time.sleep(0.1)

cam.brightness = 50

cam.image_effect = 'negative'
time.sleep(5)
cam.image_effect = 'solarize'
time.sleep(5)
cam.image_effect = 'oilpaint'
time.sleep(5)

cam.stop_preview()
