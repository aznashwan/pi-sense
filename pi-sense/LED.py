import time
import RPi.GPIO as gpio

class LED:
    'Rasbery led class'

    def __init__(self, pin, mode=gpio.BCM):
        self.pin = pin
        
        if mode == gpio.BCM or mode == gpio.BOARD:
            self.mode = mode
        
        gpio.setup(pin, gpio.OUT)
        gpio.setwarnings(False)
        
        
    def on(self):
        gpio.output(self.pin, True)
    
    def off(self):
        gpio.output(self.pin, False)
    
    
    def blink(self, time=1):
        gpio.output(self.pin, True)
        time.sleep(time)
        gpio.output(self.pin, False)
