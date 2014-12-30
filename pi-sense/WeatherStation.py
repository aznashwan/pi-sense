# Copyright 2014 Nashwan Azhari, Robert Krody, Tudor Vioreanu.
# Licensed under the GPLv2, see LICENSE for details.

from configparser import ConfigParser
import os
import signal
import sys
import time

import RPi.GPIO as gpio

from LED import LED
from LCD import LCD
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
            print("Error has occured whist accessing config file:")
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
            try:
                self.query_led.on()
                temperature = self.sensor.temperature()
                humidity = self.sensor.humidity(temperature)
                self.query_led.off()

                self.__trigger_leds(humidity, temperature)

                message_temp = self.__lcd_message(temperature, "(C)")
                message_humidity = self.__lcd_message(humidity, "(RH%)")

                self.lcd.writeline(message_temp, line=1)
                self.lcd.writeline(message_humidity, line=2)
            except Exception:
                self.sensor.reset()
                time.sleep(1)

            time.sleep(frequency)

        self.status_led.off()


    def __lcd_message(self, reading, measurement=""):
        """
            Helper function to generate the LCD message for a reading

            @param reading: The numeric value that should appear in the string
            @type reading: Numeric

            @param measurement: The string representation of the measured element
            @type measurement: String

            @return: The message to be displayed on the LCD
            @rtype: String
        """

        return ("%.2f %s" % (reading, measurement)).center(self.lcd.SCREENWIDTH, " ")


    def __trigger_leds(self, humidity, temperature):
        """
            Lights up the LEDs based on the current status

            @param humidity: Current humidity reading
            @type humidity: Numeric
            @param temperature: Current temperature reading
            @type humidity: Numeric

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

