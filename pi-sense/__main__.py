# Copyright 2014 Nashwan Azhari, Robert Krody, Tudor Vioreanu.
# Licensed under the GPLv2, see LICENSE for details.

import argparse, signal, sys

from WeatherStation import WeatherStation


# set up command line argument parser
parser = argparse.ArgumentParser()
parser.add_argument("-r", "--runtime", default=600, type=int,
                    help="Time the script should run in seconds")
parser.add_argument("-f", "--frequency", default=1, type=int,
                    help="Sensor read frequency in seconds")
parser.add_argument("-c", "--config", default="./example.conf",
                    help="Station configuration file")

# parse command line arguments
args = parser.parse_args()


def signal_handler(signum, frame):
    """
        System handler for system wide interrupts. Mainly for cleaning purposes

        @param signal: Unused

        @param frame: Unused
    """
    weather_station.cleanup()
    sys.exit(0)


# instantiate weather station
weather_station = WeatherStation(args.config)

# set signal handler
signal.signal(signal.SIGINT, signal_handler)

# only run if main
if __name__ == "__main__":
    weather_station.monitor(args.runtime, args.frequency)

# cleanup at the end of the script
weather_station.cleanup()
