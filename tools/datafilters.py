# -*- coding: utf-8 -*-

"""
    This function is used to process data from the Arduino board.
    It takes a float as input then ... modify it to fit your needs.
    You will need to restart to apply changes.
"""


def datafilter(value):
    # converts arduino analog input(0 - 1023) to voltage(0 - 5v)
    value = value * 5 / 1024
    return value
