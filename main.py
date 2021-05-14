#!/usr/bin/python3
# -*- coding: utf-8 -*-
#   Copyright 2021 Constantin Zaharia <constantin.zaharia@progeek.ro>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import logging
import argparse
import os
import sys
import time
import signal

from loop_timer import LoopyTimer
from LCDScreen import LCDScreen
from Screens import Screens

LOGGING_LEVELS = {'critical': logging.CRITICAL,
                  'error': logging.ERROR,
                  'warning': logging.WARNING,
                  'info': logging.INFO,
                  'debug': logging.DEBUG}

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Raspberry PI LCD status for NTP Server Help')

    parser.parse_args()

    screens = Screens()

    _timer = LoopyTimer(1.0, screens.loop_screens, args=[], kwargs={})

    try:
        _timer.start()
    except (KeyboardInterrupt, SystemExit, EOFError):
        print("CTRL+C break command")
        screens.lcd_screen.lcd.clear()
        _timer.cancel()
        sys.exit(0)
    finally:
        pass
