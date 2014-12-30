import RPi.GPIO as gpio
import sys
import signal
import time

from LED import LED
from LCD import LCD
from SHT11 import SHT11


class WeatherStation(object):
    """
        Control class for the entire hardware setup. Lights LEDs, outputs to the LCD
            and reads from the SHT11 sensor
    """

    MIN_TEMPERATURE = 15.0
    MAX_TEMPERATURE = 35.0
    MIN_HUMIDITY = 30.0
    MAX_HUMIDITY = 90.0

    def __init__(self, configs):
        # TODO To be changed to read from file or option array
        # make use of the __main__ part below to feed correct options

        args = sys.argv
        args.pop(0)  # removes the script name
        if len(sys.argv) != 4:
            print "The pins for green, blue, red and yellow LEDs should be set as args"
            sys.exit(1)

        try:
            args = map(int, args)
        except ValueError:
            print "The args should be numeric"
            sys.exit(1)

        self.sensor = SHT11()
        self.lcd = LCD()

        self.status_led = LED(args[0])
        self.temperature_led = LED(args[1])
        self.humidity_led = LED(args[2])
        self.query_led = LED(args[3])

        self.status_led.on()

    def monitor(self, run_time=600, frequency=1):
        """
            Lights the appropriate LEDs and displays the result on the LCD for a given ammount
                of time and at a specified frequency

            @param run_time: Time to run in seconds
            @param frequency: The frequency at which the update occurs
        """
        start_time = time.time()
        end_time = start_time + run_time

        while time.time() <= end_time:
            try:
                self.query_led.on()
                temperature = self.sensor.temperature()
                humidity = self.sensor.humidity()
                self.query_led.off()

                self.__trigger_leds(humidity, temperature)

                message_temp = self.__lcd_message(temperature, "Temperature")
                message_humidity = self.__lcd_message(humidity, "   Humidity")

                self.lcd.write(message_temp, 1)
                self.lcd.write(message_humidity, 2)
            except Exception:
                self.sensor.reset()

            time.sleep(frequency)

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

        return "%s %d" % (measurement, reading)

    def __trigger_leds(self, humidity, temperature):
        """
            Lights up the LEDs based on the current status

            @param humidity: Current humidity reading
            @type humidity: Numeric
            @param temperature: Current temperature reading
            @type humidity: Numeric

            @return: None
        """

        if self.MIN_HUMIDITY > humidity or self.MAX_HUMIDITY < humidity:
            self.humidity_led.on()
        else:
            self.humidity_led.off()

        if self.MIN_TEMPERATURE > temperature or self.MAX_TEMPERATURE < temperature:
            self.temperature_led.on()
        else:
            self.temperature_led.off()


def signal_handler(signal, frame):
    """
        System handler for system wide interrupts. Mainly for cleaning purposes

        @param signal: Unused
        @param frame: Unused
    """
    gpio.cleanup()
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)

    weather_station = WeatherStation()
    weather_station.monitor()
    gpio.cleanup()




