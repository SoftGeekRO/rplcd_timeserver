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

import subprocess
import re
import time
from RPLCD.i2c import CharLCD

__version__ = 1.0


# TODO: Don't forget to add the rplcd user to i2c group
class LCDScreen(object):

    def __init__(self, welcome_text, i2c_bus=1, i2c_addr=0x27, lcd_width=16, lcd_rows=2):

        self.lcd = CharLCD(i2c_expander='PCF8574', address=i2c_addr, port=i2c_bus,
                           cols=lcd_width, rows=lcd_rows, dotsize=8,
                           charmap='A02',
                           auto_linebreaks=True,
                           backlight_enabled=True)

        self._lcd_width = lcd_width

        self.prevStr = ''

        # Create some custom characters
        self.lcd.create_char(0, (0, 0, 0, 0, 0, 0, 0, 0))
        self.lcd.create_char(1, (16, 24, 24, 24, 24, 24, 24, 16))
        self.lcd.create_char(2, (1, 3, 3, 3, 3, 3, 3, 1))
        self.lcd.create_char(3, (17, 27, 27, 27, 27, 27, 27, 17))
        self.lcd.create_char(4, (31, 31, 0, 0, 0, 0, 0, 0))
        self.lcd.create_char(5, (0, 0, 0, 0, 0, 0, 31, 31))
        self.lcd.create_char(6, (31, 31, 0, 0, 0, 0, 0, 31))
        self.lcd.create_char(7, (31, 0, 0, 0, 0, 0, 31, 31))

        self.lcd.backlight_enabled = True
        self.lcd.clear()
        self.print_line(welcome_text, 0, align='CENTER')
        self.print_line(__version__, 1, align='CENTER')
        self.lcd.home()

    def print_line(self, text, line=0, align='LEFT'):
        """Checks the string, if different than last call, update screen.

        :param text:
        :param line:
        :param align:
        :return:
        """

        if isinstance(text, float):
            text = str(text)
            
        text = text.encode('utf-8')

        if self.prevStr != text:  # Oh what a shitty way around actually learning the ins and outs of encoding chars...
            # Display string has changed, update LCD
            #self.lcd.clear()

            text_length = len(text)
            if text_length < self._lcd_width:
                blank_space = self._lcd_width - text_length
                if align == 'LEFT':
                    text = text + b' ' * blank_space
                elif align == 'RIGHT':
                    text = b' ' * blank_space + text
                else:
                    text = b' ' * (blank_space // 2) + text + b' ' * (blank_space - blank_space // 2)
            else:
                text = text[:self._lcd_width]

            self.lcd.cursor_pos = (line, 0)

            self.lcd.write_string(text.decode('utf-8'))
            # Save so we can test if screen changed between calls, don't update if not needed to reduce LCD flicker
            self.prevStr = text

