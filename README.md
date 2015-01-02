pi-sense
========

Raspberry PI + sensors + leds = weather station

#### Abilities:
  * constant monitoring of temperature and humidity
  * displaying registered values on the LCD
  * alerting of extreme values with LED's

#### Hardware:
  * Raspberry PI B+
  * [Adafruit 16x2 LCD](http://www.adafruit.com/product/181)
  * [Sensirion SHT1x](http://www.sensirion.com/en/products/humidity-temperature/humidity-temperature-sensor-sht1x/) temperature and humidity sensor
  * Handful of brick LED's and way too much wiring...

This module is written entirely in Python and relies on the [RPi.GPIO](https://pypi.python.org/pypi/RPi.GPIO) package for GPIO pin handling.

####Usage instructions:
  * properly set up your hardware
  * write a config file for your setup (see [example.conf](https://github.com/aznashwan/pi-sense/blob/master/pi-sense/example.conf))

  * either run
	[\_\_main\_\_.py](https://github.com/aznashwan/pi-sense/blob/master/pi-sense/__main__.py) or do the following in the interpreter:
```python
>>> from WeatherStation import WeatherStation
>>>
>>> ws = WeatherStation("/absolute/path/to/config/file.conf")
>>> ws.monitor(run_time=3600, frequency=5)
>>>
>>> # and after you're done with everything:
>>> ws.cleanup()
```

NOTE: as with any actions involving use of the GPIO pins, this module requires you run it as root.

##### Authors\*:
* [Nashwan Azhari](https://github.com/aznashwan)
* [Robert Krody](https://github.com/krodyrobi)
* [Tudor Vioreanu](https://github.com/tudorvio)

\* The authors are undergraduates at the **Polytechnic University of Timisoara**, this module being done as a special assignment towards getting their degree.

