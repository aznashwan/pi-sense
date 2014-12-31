# Copyright 2014 Nashwan Azhari, Robert Krody, Tudor Vioreanu.
# Licensed under the GPLv2, see LICENSE for details.

from configparser import ConfigParser
import os, sys, time

import RPi.GPIO as gpio

from LCD import LCD
from LED import LED
from SHT11 import SHT11


class WeatherStation(object):
    """
        Control class for the entire hardware setup.
        Contains:
            - 16x2 LCD
            - temperature & humidity sensor
            - green LED to indicate station is operational
            - blue LED to indicate sensors are currently being queried
            - red LED to indicate extreme temperature readings
            - yellow LED to indicate extreme humidity readings

        Example usage:
        >>> from WeatherStation import WeatherStation
        >>>
        >>> # for details about the config file, see "example.conf"
        >>> ws = WeatherStation("/optional/path/to/config")
        >>> ws.monitor(time=3600, frequency=5)
    """

    def __init__(self, confpath="./example.conf"):
        self.mode = None
        self.warnings = None
        self.params = {}
        self.leds = []
        self.ledpins = {}
        self.sensorpins = {}

        # read through the config file
        try:
            os.stat(confpath)
            self.__parseconfig(confpath)
        except FileNotFoundError:
            print("Config file %r not found." % confpath)
            sys.exit(-1)
        except AssertionError as e:
            print("The config file is missing the following sections: ", e)
            sys.exit(-1)
        except Exception as e:
            print("Error has occured whilst accessing config file:")
            print(e)
            sys.exit(-1)

        # set warnings
        gpio.setwarnings(self.warnings)

        # instantiate all components
        self.lcd = LCD(self.mode)
        self.sensor = SHT11(self.sensorpins["data"], self.sensorpins["clock"],
                self.mode)

        self.status_led = LED(self.ledpins["green"], self.mode)
        self.temperature_led = LED(self.ledpins["red"], self.mode)
        self.humidity_led = LED(self.ledpins["yellow"], self.mode)
        self.query_led = LED(self.ledpins["blue"], self.mode)
        self.leds = [self.status_led, self.temperature_led, self.humidity_led,
                self.query_led]

        # blink all LEDs
        for led in self.leds:
            led.blink(0.3)

        # write status to the screen
        self.__lcd_write("WEATHERSTATION", "OPERATIONAL")


    def __parseconfig(self, confpath):
        """
            Parses the config file, registering all found values.
            In case a paricular value is not present, a fallback is provided.

            @param: confpath - path to the configuration file

            @return: none
        """
        parser = ConfigParser()
        parser.read(confpath)

        # check if all required sections are present:
        sections = parser.sections()
        expected = ["General", "Parameters", "Sensor", "LEDs"]
        assert sections >= expected, "%r" % expected - sections

        # get operations mode
        mode = parser["General"]["MODE"]
        if mode.lower() == "board":
            self.mode = gpio.BOARD
        else:
            self.mode = gpio.BCM

        # get warnings setting
        self.warnings = parser.getboolean("General", "WARNINGS", fallback=False)

        # get operational parameters
        parameters = parser["Parameters"]
        self.params["maxt"] = parameters.getfloat("MAX_TEMP", fallback=40.0)
        self.params["mint"] = parameters.getfloat("MIN_TEMP", fallback=20.0)
        self.params["maxh"] = parameters.getfloat("MAX_HUMID", fallback=30.0)
        self.params["minh"] = parameters.getfloat("MIN_HUMID", fallback=70.0)

        # get sensor pins
        sensorpins = parser["Sensor"]
        self.sensorpins["data"] = sensorpins.getint("DATA", fallback=27)
        self.sensorpins["clock"] = sensorpins.getint("CLOCK", fallback=4)

        # get led pins
        ledpins = parser["LEDs"]
        self.ledpins["green"] = ledpins.getint("GREEN", fallback=12)
        self.ledpins["red"] = ledpins.getint("RED", fallback=19)
        self.ledpins["yellow"] = ledpins.getint("YELLOW", fallback=20)
        self.ledpins["blue"] = ledpins.getint("BLUE", fallback=21)


    def monitor(self, run_time=600, frequency=1):
        """
            Lights the appropriate LEDs and displays the result on the LCD for
            a given ammount of time and at a specified frequency.

            @param run_time: Time to run in seconds.
            @param frequency: The frequency at which the update occurs.

            @return: None
        """
        self.status_led.on()

        start_time = time.time()
        end_time = start_time + run_time

        while time.time() <= end_time:
            # query the sensor
            self.query_led.on()
            try:
                temperature = self.sensor.temperature()
                humidity = self.sensor.humidity(temperature)
            except Exception:
                self.sensor.reset()
                time.sleep(1)
                continue
            self.query_led.off()

            # trigger appropriate LEDs
            self.__trigger_leds(humidity, temperature)

            # write values on the LCD
            self.__lcd_write("%.2f %s" % (temperature, "(C)"),
                    "%.2f %s" % (humidity, "(RH%)"))

            time.sleep(frequency)

        self.clear()
        self.__lcd_write("WEATHERSTATION", "OPERATIONAL")


    def __lcd_write(self, line1="", line2=""):
        """
            Centers and writes the two lines to the LCD.

            @param: line1 - what to write on the first line of the LCD.

            @param: line2 - what to write on the second line of the LCD.

            @return: None
        """
        self.lcd.writeline(line1.center(self.lcd.SCREENWIDTH, " "), line=1)
        self.lcd.writeline(line2.center(self.lcd.SCREENWIDTH, " "), line=2)


    def __trigger_leds(self, humidity, temperature):
        """
            Lights up the LEDs based on the current status.

            @param: humidity - current humidity reading.

            @param: temperature - current temperature reading.

            @return: None
        """

        if self.params["minh"] > humidity or self.params["maxh"] < humidity:
            self.humidity_led.on()
        else:
            self.humidity_led.off()

        if self.params["mint"] > temperature or self.params["maxt"] < temperature:
            self.temperature_led.on()
        else:
            self.temperature_led.off()


    def clear(self):
        """
            Turns off all LED's, clear the LCD, set sensor to idle.

            @param: None

            @return: None
        """
        for led in self.leds:
            led.off()

        self.sensor.reset()

        self.lcd.clear()


    def cleanup(self):
        """
            Turn off associated LED's, clear the LCD, cleanup all pins.
            This method is meant to be called after the instance of
            WeatherStation has done its job and is no longer required.
            After this method is called, this instance of WeatherStation is
            rendered useless.

            @param: None

            @return: None
        """
        self.clear()
        gpio.cleanup()
