# Copyright 2014 Nashwan Azhari, Robert Krody, Tudor Vioreanu.
# Licensed under the GPLv2, see LICENSE for details.

import time
import RPi.GPIO as gpio


class SHT11(object):
    """
        This object is meant to provide an easily accesible interface to the
        Sensiron SHT11 temperature and humidity sensor.
        The below code conforms to the normal operation of the sensor as is
        outlined in its usage manual:
            http://www.sensirion.com/fileadmin/user_upload/customers/sensirion/Dokumente/Humidity/Sensirion_Humidity_SHT1x_Datasheet_V5.pdf
    """

    # humidity calculation constants
    C1 = -2.0468
    C2 =  0.0367
    C3 = -0.0000015955

    # temperature compensation constants for humidity
    T1 =  0.01
    T2 =  0.00008

    # temperature calculation constants
    D1 = -40.1
    D2 = 0.01
    DC = 30

    # command encodings for our sensor:
    __humcmd = 0b00000101
    __tempcmd = 0b00000011


    def __init__(self, datapin, clkpin, mode=gpio.BCM):
        gpio.setmode(mode)        

        self.datapin = datapin
        self.clockpin = clkpin

        # the sensor has an initial startup of 11ms to reach standby mode.
        # although ludicrously unlikely for it not to be pre-initialized, we
        # will issue the wait here in order to be safe:
        time.sleep(11 * (10 ** -3))


    def __tick(self, tick):
        """
            Issues a tick on the clock pin for exactly 100 nanoseconds.

            @param: tick - the value of the clock tick we wish to issue.
                False :: low
                True  :: high

            @return: None
        """
        gpio.output(self.clockpin, tick)
        time.sleep(10 ** -7)


    def __sendcmd(self, cmd):
        """
            Send a command to the sensor through the datapin.
            The procedure for sending a command is as follows:

            First, we must alert the sensor that a command is about to be sent
            by the following sequence of signals:
            data(1) + clock(0)
            clock(1) - data(0) - clock(0) - clock(1) - data(1)
            clock(0) + data(0)

            Then, we send out all 8 command bits one at a time:
            data(bit) - clock(1) - clock(0)

            After all 8 bits are sent, the sensor acknowledges their recieval
            after one clock cycle by pulling data low and then high again.
            clock(1)
            read(data) == 0 - clock(0) - read(data) == 1

            @param: cmd - binary encoding of the command to be issued.

            @return: None
        """
        # setup the pins for output
        gpio.setup(self.datapin, gpio.OUT)
        gpio.setup(self.clockpin, gpio.OUT)

        # alert that command is inbound
        self.__tick(False)
        gpio.output(self.datapin, True)

        self.__tick(True)
        gpio.output(self.datapin, False)
        self.__tick(False)
        self.__tick(True)
        gpio.output(self.datapin, True)
        self.__tick(False)

        # send command bits
        for i in range(8):
            gpio.output(self.datapin, cmd & (1 << (7 - i)))
            self.__tick(True)
            self.__tick(False)

        # wait for acknowledge signal from sensor
        self.__tick(True)
        gpio.setup(self.datapin, gpio.IN)

        self.__tick(False)
        if gpio.input(self.datapin) != True:
            raise Exception("Error whilst sending command \'%d\'." % (cmd))

        
    def __awaitresult(self):
        """
            After a command has been issued, we must wait for the sensor to
            do the necessary computations.
            This should last approximately 320 milliseconds, after which 
            the sensor will pull the data pin to 0 logic and re-enter 
            idle mode until the read sequence isinitiated.

            @param: None

            @return: None
        """
        gpio.setup(self.datapin, gpio.IN)
        assert gpio.input(self.datapin) == True

        # wait for 400 milliseconds to be sure
        time.sleep(4 * 10 ** -1)

        if gpio.input(self.datapin) != False:
            raise Exception("Error occured whilst awaiting result.")


    def __readresult(self):
        """
            Read the result from the sensor.
            In 14-bit mode, the sensor will return the raw result in two
            one-byte chunks, one bit at a time, most significat first.
            After recieving a byte, we must acknowledge it by pulling data
            to 0 logic ourselves.

            @param: None

            @return: integer representing the raw data reading.
        """
        gpio.setup(self.datapin, gpio.IN)
        gpio.setup(self.clockpin, gpio.OUT)

        # read first byte
        byte1 = self.__readbyte()

        # acknowledge reception of firts byte
        gpio.setup(self.datapin, gpio.OUT)
        gpio.output(self.datapin, True)
        gpio.output(self.datapin, False)
        self.__tick(True)
        self.__tick(False)

        # read second byte
        gpio.setup(self.datapin, gpio.IN)
        byte2 = self.__readbyte()

        result = (byte1 << 8) | byte2
        return result


    def __readbyte(self):
        """
            Reads a total of 8 bits, one at a time, and returns them.
            The reading of each bit is governed by one full clock cycle.
            Bits are recieved most-significant first.

            @param: None

            @return: integer containing the 8 bits which were read.
        """
        buff = 0
        for i in range(8):
            self.__tick(True)
            buff = (buff << 1) | gpio.input(self.datapin)
            self.__tick(False)

        return buff


    def __denyCRC(self):
        """
            Sends the command to skip the sending of the CRC checksum by
            the sensor and immediately go back into idle mode.
            This is done by keeping data high for a full clock cycle.

            @param: None

            @return: None
        """
        gpio.setup(self.datapin, gpio.OUT)
        gpio.setup(self.clockpin, gpio.OUT)

        gpio.output(self.datapin, True)
        self.__tick(False)
        self.__tick(True)


    def reset(self):
        """
            Performs a hard reset on the sensor, clearing all registers and
            re-initiating all communications.
            This is done by keeping data high and going through a minimum
            of 9 clock cycles.

            @param: None

            @return: None
        """
        gpio.setup(self.datapin, gpio.OUT)
        gpio.setup(self.clockpin, gpio.OUT)

        gpio.output(self.datapin, True)
        for i in range(9):
            self.__tick(True)
            self.__tick(False)


    def temperature(self):
        """
            The main method of the sensor module which issues the necessary
            command for reading the temperature and fetches the result.
            The equation of conversion from raw value to actual temperature
            is linear and constant dependant.
            NOTE: for some reason, our particular sensor seems to be off by
            approximately 30°, for which we must account at the very end.

            @param: None

            @return: floating point temperature value (°C).
        """
        self.__sendcmd(self.__tempcmd)

        self.__awaitresult()
        raw = self.__readresult()
        self.__denyCRC()

        result = raw * self.D2 + self.D1
        return result - self.DC


    def humidity(self):
        """
            The main method of the sensor module which issues the necessary
            command for reading the humidity.
            Usually, our sensor calculates humidity relative to the ambient
            temperature, in which case, we require the temperature to apply
            the corrections necessary for obtaining the absolute humidity.

            @param: None

            @return: floating point humidity value (%RH).
        """
        temp = self.temperature()

        self.__sendcmd(self.__humcmd)

        self.__awaitresult()
        raw = self.__readresult()
        self.__denyCRC()

        linear = self.C1 + self.C2 * raw + self.C3 * raw ** 2
        result = (temp - 25.0) * (linear * self.T2 + self.T1) + linear
        return result
