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

# Define digit pairs from 00 to 61 (yes 61 because of leap seconds)
digits = [
    [24341, 25351], [24120, 25120], [24161, 25370], [24161, 25171], [24301, 25141],
    [24360, 25171], [24360, 25371], [24141, 25101], [24361, 25371], [24341, 25141],
    [2241, 2251], [2020, 2020], [2061, 2270], [2061, 2071], [2201, 2041],
    [2260, 2071], [2260, 2271], [2041, 2001], [2261, 2271], [2241, 2041],
    [6341, 27251], [6120, 27020], [6161, 27270], [6161, 27071], [6301, 27041],
    [6360, 27071], [6360, 27271], [6141, 27001], [6361, 27271], [6341, 27041],
    [6341, 7351], [6120, 7120], [6161, 7370], [6161, 7171], [6301, 7141],
    [6360, 7171], [6360, 7371], [6141, 7101], [6361, 7371], [6341, 7141],
    [20341, 4351], [20120, 4120], [20161, 4370], [20161, 4171], [20301, 4141],
    [20360, 4171], [20360, 4371], [20141, 4101], [20361, 4371], [20341, 4141],
    [26241, 7351], [26020, 7120], [26061, 7370], [26061, 7171], [26201, 7141],
    [26260, 7171], [26260, 7371], [26041, 7101], [26261, 7371], [26241, 7141],
    [26241, 27351], [26020, 27120]]

# TODO: Don't forget to add the rplcd user to i2c group
class LCDScreen(object):

    def __init__(self, welcome_text, i2c_bus=1, i2c_addr=0x27, lcd_width=16, lcd_rows=2):

        self.lcd = CharLCD(i2c_expander='PCF8574', address=i2c_addr, port=i2c_bus,
                           cols=lcd_width, rows=lcd_rows, dotsize=8,
                           charmap='A02',
                           auto_linebreaks=True,
                           backlight_enabled=True)

        self._lcd_width = lcd_width

        # Create some custom characters
        self.lcd.create_char(0, (0, 0, 0, 0, 0, 0, 0, 0))
        self.lcd.create_char(1, (16, 24, 24, 24, 24, 24, 24, 16))
        self.lcd.create_char(2, (1, 3, 3, 3, 3, 3, 3, 1))
        self.lcd.create_char(3, (17, 27, 27, 27, 27, 27, 27, 17))
        self.lcd.create_char(4, (31, 31, 0, 0, 0, 0, 0, 0))
        self.lcd.create_char(5, (0, 0, 0, 0, 0, 0, 31, 31))
        self.lcd.create_char(6, (31, 31, 0, 0, 0, 0, 0, 31))
        self.lcd.create_char(7, (31, 0, 0, 0, 0, 0, 31, 31))

        self.lastScreenTime = time.time()  # time since last screen switch
        self.prevStr = ""

        self.screens = (
            (self.big_time_view, 6),
            # Rotating list of views on LCD with how many seconds to display each display. Round robin style.
            #(self.connectedUserView, 4),
            #(self.big_time_view, 6),
            (self.precision_view, 4),
            (self.big_time_view, 6),
            (self.ntptime_info, 5),
            (self.big_time_view, 6),
            (self.clockperf_view, 5),
            (self.get_hostname, 6),
            (self.get_current_ip, 6),
        )  # list of all views for rotation
        self.nrofscreens = len(self.screens)
        self.currentScreen = 0

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
            self.prevStr = text  # Save so we can test if screen changed between calls, don't update if not needed to reduce LCD flicker



    def precision_view(self):
        """Calculate and display the NTPD accuracy"""
        try:
            output = subprocess.check_output("ntpq -c rv", shell=True)
            returncode = 0
        except subprocess.CalledProcessError as e:
            output = e.output
            returncode = e.returncode
            print(returncode)
            exit(1)

        precision = ""
        clkjitter = ""
        clkwander = ""
        theStr = ""
        searchResult = re.search(r'precision=(.*?),', output.decode('utf-8'), re.S)
        precision = searchResult.group(1)
        searchResult = re.search(r'.*clk_jitter=(.*?),', output.decode('utf-8'), re.S)
        clk_jitter = searchResult.group(1)
        if precision and clk_jitter:
            precision = (1 / 2.0 ** abs(float(precision))) * 1000000.0
            theStr = "Prec: {:.5f} {}s\r".format(precision, chr(0xE4))
            theStr += "ClkJit: {:>4} ms".format(clk_jitter)
        else:
            theStr = "Error: No\rPrecision data"
        self.print_line(theStr)
        # return theStr

    def ntptime_info(self):
        """Statistics from ntptime command"""
        try:
            output = subprocess.check_output("ntptime", shell=True)
        except subprocess.CalledProcessError as e:
            output = e.output
            returncode = e.returncode
            print(returncode)
        precision = re.search(r'precision (.* us).*tolerance (.* ppm)', output.decode('utf-8'), re.M | re.S)
        if precision:
            theStr = "Precis: {:>8}\r".format(precision.group(1))
            theStr += "Stabi: {:>9}".format(precision.group(2))
        else:
            theStr = "No info\nError"
        self.print_line(theStr)

    def clockperf_view(self):
        """Shows jitter etc"""
        output = subprocess.check_output("ntptime", shell=True)
        search = re.search(r'TAI offset.*offset (.*? us).*jitter (.* us)', output.decode('utf-8'), re.M | re.S)
        if search:
            theStr = "Offset: {:>8}\r".format(search.group(1))
            theStr += "OSjitt: {:>8}".format(search.group(2))
        else:
            theStr = "No offset\rinfo error"
        self.print_line(theStr)

    def connectedUserView(self):
        """Shows connected clients to ntpd"""
        highestCount = "NaN"
        try:
            output = subprocess.check_output("ntpdc -n -c monlist | awk '{if(NR>2)print $1}' | uniq | wc -l",
                                             shell=True)  # Gets all the connected clients from ntp
        except subprocess.CalledProcessError as e:
            output = e.output
            returncode = e.returncode
            print(returncode)

        try:
            highestCount = subprocess.check_output(
                "ntpdc -n -c monlist | awk '{if(NR>2)print $4}' | sort -nrk1,1 | line",
                shell=True)  # Gets the highest connections from connected clients
        except subprocess.CalledProcessError as e:
            output = e.output
            returncode = e.returncode
            print(returncode)

        theStr = "Con users: {:>6}".format(output.decode('utf-8'))
        theStr += "Hi cons: {:>8}".format(highestCount)
        self.print_line(theStr)

    def get_hostname(self):
        import socket
        hostname = socket.getfqdn()
        if hostname:
            self.print_line(hostname)
        else:
            self.print_line('No hostname')

    def get_current_ip(self):
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('1.1.1.1', 1))  # connect() for UDP doesn't send packets
        local_ip_address = s.getsockname()[0]
        self.print_line(local_ip_address)

    def update_lcd(self):
        if time.time() - self.lastScreenTime > self.screens[self.currentScreen][1]:  # Time to switch display
            self.currentScreen = self.currentScreen + 1
            self.lastScreenTime = time.time()  # reset screen timer
            if self.currentScreen > self.nrofscreens - 1:
                self.currentScreen = 0
        self.screens[self.currentScreen][0]()
