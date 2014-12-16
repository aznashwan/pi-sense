# Copyright 2014 Nashwan Azhari, Robert Krody, Tudor Vioreanu.
# Licensed under the GPLv2, see LICENSE for details.

import time
import RPi.GPIO as gpio

class LCD(object):
    """ An object-wrapper that models our LCD (Adafruit PI-Shield 16x2 LCD).

        Allows for creation of the LCD object and direct use of its
        write(str message, int line) method.

        All apparent "magic constants" present in the code below have a direct
        explanation in the datasheet of our particular model of LCD that may be
        found here:
            https://learn.adafruit.com/downloads/pdf/drive-a-16x2-lcd-directly-with-a-raspberry-pi.pdf
    """
    # define all of out used pins
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
    __screenwidth = 16
    __delay = 0.00005


    def __init__(self, mode=gpio.BCM):
        # set desired mode
        if mode == gpio.BOARD:
            self.__switchtoboard()
        gpio.setmode(mode)
        gpio.setwarnings(False)

        # setup all the pins for output
        gpio.setup(self.__regsel, gpio.OUT)
        gpio.setup(self.__enable, gpio.OUT)
        for pin in self.__datapins:
            gpio.setup(pin, gpio.OUT)

        self.__initialize()


    def __initialize(self):
        """ Initialize the LCD for operation
            @param: None
            @return: None
        """
        # send initialization instructions
        self.__writebyte(0x33, False)
        self.__writebyte(0x32, False)

        # send line configurations
        self.__writebyte(0x28, False)

        # send cursor off command
        # set to 0x0E to enable
        self.__writebyte(0x0C, False)

        # shift cursor to beginning
        self.__writebyte(0x06, False)

        # set operation mode to 8-bit
        self.__writebyte(0x01, False)


    def __switchtoboard(self):
        """ Switches the pin numbering scheme to gpio.BOARD.
            WARNING: for stability reasons, a single scheme should be picked
                from the start and used consistently throughout the project.
            @param: None
            @return: None
        """
        self.__datapin1 = 11
        self.__datapin2 = 12
        self.__datapin3 = 15
        self.__datapin4 = 16
        self.__enable = 18
        self.__regsel = 22


    def __enableread(self):
        """ Enables reading to the internal register from the four data pins.
            @param: None
            @return: None
        """
        # initial delay
        time.sleep(self.__delay)
        # set read enable to True
        gpio.output(self.__enable, True)
        # intermediary delay
        time.sleep(self.__delay)
        # reset to false
        gpio.output(self.__enable, False)
        # trailing delay
        time.sleep(self.__delay)


    def __writebyte(self, byte, mode=True):
        """ Writes a single byte to the register of the LCD.
            @param: byte - the character to be written to the LCD's register
            @param: mode - the register mode for the byte we are about to send.
                False :: instruction byte
                True  :: data byte
                default = True
            @return: None
        """
        gpio.output(self.__regsel, mode)

        # encode leading 4 bits to the data pins
        for pin in self.__datapins:
            gpio.output(pin, False)
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


    def write(self, message, line=1, align=1):
        """ Writes a message to a single line of the LCD.
            @param: message - the message to be written.
            If line width exceeds 16 characters, will not wrap/sway the output.
            @param: line - the line at which we wish to write to.
                1 :: first line
                2 :: second line
                default = 1
            @param: alignment - the alignment of the message on the screen.
                1 :: left
                2 :: center
                3 :: right
                default = 1
            @return: none
        """
        # set the line we are writing on
        if line == 1:
            self.__writebyte(self.__line1, False)
        else:
            self.__writebyte(self.__line2, False)

        # apply the alignment to the string
        if align == 1:
            string = message.ljust(self.__screenwidth)
        elif align == 2:
            string = message.center(self.__screenwidth)
        else:
            string = message.rjust(self.__screenwidth)

        # write the message to the LCD, byte by byte
        for char in string:
            self.__writebyte(ord(char))

