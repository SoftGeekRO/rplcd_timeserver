
import argparse
import logging
import os
import time

from time import *

from LCDScreen import LCDScreen

LOGGING_LEVELS = {'critical': logging.CRITICAL,
                  'error': logging.ERROR,
                  'warning': logging.WARNING,
                  'info': logging.INFO,
                  'debug': logging.DEBUG}

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Raspberry PI LCD status for NTP Server Help')

    parser.parse_args()

    mylcd = LCDScreen("Atomic Clock NTP")
    sleep(2)

    while True:
        mylcd.update_lcd()
        sleep(0.20)
