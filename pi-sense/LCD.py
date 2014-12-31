# Copyright 2014 Nashwan Azhari, Robert Krody, Tudor Vioreanu.
# Licensed under the GPLv2, see LICENSE for details.

import time
import RPi.GPIO as gpio


class LCD(object):
    """
        An object-wrapper that models our LCD (Adafruit PI-Shield 16x2 LCD).

        Allows for creation of the LCD object and direct use of its
        writeline(str message) method.

        All apparent "magic constants" present in the code below have a direct
        explanation in the datasheet of our particular model of LCD that may be
        found here:
            https://learn.adafruit.com/downloads/pdf/drive-a-16x2-lcd-directly-with-a-raspberry-pi.pdf
    """

    # define all of out used pins
    # these values are static due to the build and operation mode of the LCD
    __datapin1 = 17
    __datapin2 = 18
    __datapin3 = 22
    __datapin4 = 23
    __enable = 24
    __regsel = 25
    __datapins = [__datapin1, __datapin2, __datapin3, __datapin4]

    # byte instructions for line select
    __line1 = 0x80
    __line2 = 0xC0

    # screen model parameters
    SCREENWIDTH = 16


    def __init__(self, mode=gpio.BCM):
        # set desired mode
        if mode == gpio.BOARD:
            self.__switchtoboard()
        gpio.setmode(mode)

        # setup all the pins for output
        gpio.setup(self.__regsel, gpio.OUT)
        gpio.setup(self.__enable, gpio.OUT)
        for pin in self.__datapins:
            gpio.setup(pin, gpio.OUT)

        self.__initialize()


    def __switchtoboard(self):
        """
            Switches the pin numbering scheme to gpio.BOARD.
            WARNING: for stability reasons, a single scheme should be picked
                from the start and used consistently throughout the project.

            @param: None

            @return: None
        """
        self.__datapin1 = 11
        self.__datapin2 = 12
        self.__datapin3 = 15
        self.__datapin4 = 16
        self.__datapins = [self.__datapin1, self.__datapin2, self.__datapin3,
                        self.__datapin4]

        self.__enable = 18
        self.__regsel = 22


    def __regmode(self, mode="data"):
        """
            Switch the GPIO which signals wether the next incoming byte is a
            data byte (1 logic) or an instruction byte (0 logic).

            @param: mode - str with the operation mode to be used
                data  :: data byte
                instr :: instruction byte

            @return: None
        """
        assert mode in ["data", "instr"]

        if mode == "data":
            gpio.output(self.__regsel, True)
        else:
            gpio.output(self.__regsel, False)


    def __initialize(self):
        """
            Issue initialization commands to the LCD.
            8-bit mode was preffered due to its offering the full range of
            ASCII characters.

            @param: None

            @return: None
        """
        self.__regmode("instr")

        # send initialization instructions
        self.__writebyte(0x33)
        self.__writebyte(0x32)

        # send line configurations
        self.__writebyte(0x28)

        # send cursor off command
        # set to 0x0E to enable
        self.__writebyte(0x0C)

        # shift cursor to beginning
        self.__writebyte(0x06)

        # set operation mode to 8-bit
        self.__writebyte(0x01)


    def __enableread(self):
        """
            Enables reading to the internal register from the four data pins.
            This is done by taking the enable pin thorugh a full cycle with a
            50 micosecond period.

            @param: None

            @return: None
        """
        delay = 5 * 10 ** -5
        time.sleep(delay)
        gpio.output(self.__enable, True)
        time.sleep(delay)
        gpio.output(self.__enable, False)
        time.sleep(delay)


    def __writebyte(self, byte):
        """
            Writes a single byte to the register of the LCD.
            This is done by encoding the first 4 most significant bits on our 4
            data pins, enabling their reading into the internal register, and
            doing the exact same for the 4 least significant bits.

            @param: byte - the character to be written to the LCD's register

            @return: None
        """
        # pre-normalize all data pins:
        for pin in self.__datapins:
            gpio.output(pin, False)

        # encode leading 4 bits to the data pins
        if byte & 0x20 == 0x20:
            gpio.output(self.__datapin1, True)
        if byte & 0x40 == 0x40:
            gpio.output(self.__datapin2, True)
        if byte & 0x80 == 0x80:
            gpio.output(self.__datapin3, True)
        if byte & 0x10 == 0x10:
            gpio.output(self.__datapin4, True)

        self.__enableread()


        # encode trailing 4 bits to the data pins
        for pin in self.__datapins:
            gpio.output(pin, False)

        if byte & 0x02 == 0x02:
            gpio.output(self.__datapin1, True)
        if byte & 0x04 == 0x04:
            gpio.output(self.__datapin2, True)
        if byte & 0x08 == 0x08:
            gpio.output(self.__datapin3, True)
        if byte & 0x01 == 0x01:
            gpio.output(self.__datapin4, True)

        self.__enableread()


    def clear(self):
        """
            Clears the LCD

            @param: None

            @return: None
        """
        self.writeline(" " * self.SCREENWIDTH, line=1)
        self.writeline(" " * self.SCREENWIDTH, line=2)


    def writeline(self, message, line=1):
        """
            Writes a message to a line of the LCD.
            If line width exceeds 16 characters, the output will not be wrapped.

            @param: message - the message to be written.

            @param: line - the line at which we wish to write to.
                1 :: first line
                2 :: second line
                default = 1
            failsafe: if incompatible value is provided, will default to line 1.

            @return: None
        """
        self.__regmode("instr")
        if line != 2:
            self.__writebyte(self.__line1)
        else:
            self.__writebyte(self.__line2)

        # write the message to the LCD, byte by byte
        self.__regmode("data")

        for char in message:
            self.__writebyte(ord(char))
