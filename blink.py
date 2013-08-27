import RPi.GPIO as GPIO
import time
from pins import *


GPIO.setmode(GPIO.BOARD)

def init_pin(pin):
    GPIO.setup(pin, GPIO.OUT)

def flash_pin(pin):
    GPIO.output(pin, False)
    p = GPIO.PWM(pin, 60)
    p.start(0)
    for i in range(100) + range(100,-1,-1):
        time.sleep(0.005)
        p.ChangeDutyCycle(i)
    p.stop()
    GPIO.output(pin, False)


pins = [PIN_RECORDING_LED, PIN_LED2, PIN_LED3]

for pin in pins:
    init_pin(pin)
    flash_pin(pin)
 
