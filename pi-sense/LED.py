import time
import RPi.GPIO as gpio


class LED(object):
    def __init__(self, pin, mode=gpio.BCM):
        """
            Creates a LED instance for use on a RasberyPI B+

            @param pin: Pin identification code for the selected mode
            @type pin: int
            @param mode: Can be gpio.BCM or gpio.BOARD
        """
        self.pin = pin
        
        if mode == gpio.BCM or mode == gpio.BOARD:
            self.mode = mode
        
        gpio.setup(pin, gpio.OUT)
        gpio.setwarnings(False)

    def on(self):
        """
            Turns the led ON if it isn't already

            @param self:
            @return: None
        """
        gpio.output(self.pin, True)
    
    def off(self):
        """
            Turns the led OFF if it isn't already

            @param self:
            @return : None
        """
        gpio.output(self.pin, False)

    def blink(self, delay=1):
        """
            Turns the led ON and OFF with a specified delay ONCE

            @param delay: Number of seconds between state transition
            @type delay: float

            @return: None
        """
        gpio.output(self.pin, True)
        time.sleep(delay)
        gpio.output(self.pin, False)
        time.sleep(delay)
