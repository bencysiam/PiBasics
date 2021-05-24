from gpiozero import MotionSensor
import time

pir = MotionSensor(4) 

while(1):
    pir.wait_for_motion() 
    print(”I saw you!")
    time.sleep(3)
