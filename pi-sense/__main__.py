import sys
import signal
import argparse

from WeatherStation import WeatherStation


parser = argparse.ArgumentParser()
parser.add_argument("-r", "--runtime", default=600, type=int,
                    help="Time the script should run in seconds")
parser.add_argument("-f", "--frequency", default=1, type=int,
                    help="Sensor read frequency in seconds")
parser.add_argument("-c", "--config", default="./example.conf",
                    help="Station configuration file")
args = parser.parse_args()


def signal_handler(signal, frame):
    """
        System handler for system wide interrupts. Mainly for cleaning purposes
        @param signal: Unused
        @param frame: Unused
    """
    weather_station.cleanup()
    sys.exit(0)


weather_station = WeatherStation(args.config)
signal.signal(signal.SIGINT, signal_handler)


weather_station.monitor(args.runtime, args.frequency)
weather_station.cleanup()
