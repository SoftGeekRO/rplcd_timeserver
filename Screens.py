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

from typing import Tuple, Union, Any
import psutil
import time
import datetime
from itertools import cycle

from LCDScreen import LCDScreen

from libs.vcgencmd_pi import VcgencmdParser
from libs.ntpq import NtpqParser
from libs.chrony import ChronyParser
from libs.gpsd import Gpsd, NoFixError

from tools import humanize_file_size
from decorators import class_register_screen, register_screen

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


@class_register_screen
class Screens(object):
    """

    """

    # what NTP daemons list to be search by
    ntp_daemons_list = ['ntpq', 'chronyd']

    # NTP daemon currently running
    ntp_daemon_running = None

    lcd_screen = None

    screen_exceptions = []
    cycle_exceptions = []

    current_timer_cycle_delay = 0
    current_running_method = ''

    screen_current = ()
    screen_method = ''
    screen_option_time = 5

    def __init__(self):
        self.lcd_screen = LCDScreen("Atomic Clock NTP")

        self.vcgencmd = VcgencmdParser()

        self.gpsd = Gpsd()

        self.chrony = ChronyParser()

        self.ntpq = NtpqParser()

        self.screens_iter = cycle(self.methods_ordered)

        # load initial screen
        self.load_screen()

    def add_screen_exception(self, screen, cycles=5):
        """

        :param screen:
        :param cycles:
        :return:
        """
        if len(self.screen_exceptions):
            for exception in self.screen_exceptions:
                if screen == exception[0]:
                    break
                else:
                    self.screen_exceptions.append([screen, cycles, 0])
        else:
            self.screen_exceptions.append([screen, cycles, 0])

    def process_screen(self):
        """

        :return:
        """

        screen_current = next(self.screens_iter)
        screen_method = screen_current[0].split('.')[1]
        screen_option_flash = screen_current[1].get('flash', False)

        # check if is any exception is present
        if len(self.screen_exceptions) > 0:
            for ndx, screen in enumerate(self.screen_exceptions):
                method, cycles_to_skip, cycles_count = screen

                # check if the current screen is in exceptions
                # if not return the screen
                if method == screen_method:
                    # check if is permanent, if not means that is timed by cycles
                    if cycles_to_skip < 0:
                        #self.process_screen()
                        continue
                    else:
                        # if the screen is exception and the exception not reached to end, increment a new cycle
                        if cycles_count <= cycles_to_skip:
                            self.screen_exceptions[ndx][2] += 1
                        else:
                            # @TODO: print in log or cli the screen removed from exception
                            self.screen_exceptions.pop(ndx)
                            # check if the screen is flash mode
        if screen_option_flash:
            self.add_screen_exception(screen_method, -1)

        return screen_current

    def load_screen(self):
        """

        :return:
        """

        current_screen = self.process_screen()
        self.screen_method = current_screen[0].split('.')[1]

    def display_screen(self):
        # execute the screen method
        line0, line1 = getattr(self, self.screen_method)()

        self.lcd_screen.print_line(line0[0], line0[1], align='CENTER')
        self.lcd_screen.print_line(line1[0], line1[1], align='CENTER')

    def loop_screens(self):
        if self.current_timer_cycle_delay >= self.screen_option_time:
            self.current_timer_cycle_delay = 0
            self.load_screen()
        else:
            self.current_timer_cycle_delay += 1
            self.display_screen()

    @staticmethod
    @register_screen(order=1)
    def big_time_view() -> Tuple[Tuple[bytes, int], Tuple[bytes, int]]:
        """Shows custom large local time on LCD

        :return:
        """

        hrs = int(time.strftime("%H"))
        minutes = int(time.strftime("%M"))
        sec = int(time.strftime("%S"))

        # Build string representing top and bottom rows
        line_1 = "0" + str(digits[hrs][0]).zfill(5) + str(digits[minutes][0]).zfill(5) + str(digits[sec][0]).zfill(5)
        line_2 = "0" + str(digits[hrs][1]).zfill(5) + str(digits[minutes][1]).zfill(5) + str(digits[sec][1]).zfill(5)

        # Convert strings from digits into pointers to custom character
        i = 0
        _line_1 = ""
        _line_2 = ""
        while i < len(line_1):
            _line_1 = _line_1 + chr(int(line_1[i]))
            _line_2 = _line_2 + chr(int(line_2[i]))
            i += 1

        return (_line_1, 0), (_line_2, 1)

    @register_screen(order=2)
    def gps_time(self):

        try:
            gpsd = self.gpsd.get_current()
            gps_datetime = gpsd.get_time()
            gps_date = gps_datetime.strftime("%d-%m-%Y")
            gps_time = gps_datetime.strftime("%H:%M:%S")

            if gps_datetime.tzinfo:
                _tzinfo = ''
            else:
                _tzinfo = 'UTC'

            l1 = gps_date
            l2 = "{0} {1}".format(gps_time, _tzinfo)
        except (NoFixError, Exception) as e:
            l1 = 'GPS TIME Error!'
            l2 = 'GPS TIME Error!'

        return (l1, 0), (l2, 1)

    @register_screen(order=3)
    def psutil_cpu_freq(self):
        cpu_freq = psutil.cpu_freq()

        l1 = "Now:{:d} Mhz".format(int(cpu_freq.current))
        l2 = "Min:{:d} Max:{:d}".format(int(cpu_freq.min), int(cpu_freq.max))

        return (l1, 0), (l2, 1)

    @register_screen(order=4)
    def psutil_cpu_load(self):
        cpu_load = psutil.getloadavg()

        l1 = "1:{0}".format(cpu_load[0])
        l2 = "5:{0} 15:{1}".format(cpu_load[1], cpu_load[2])

        return (l1, 0), (l2, 1)

    @register_screen(order=4)
    def psutil_network_counters(self):
        net = psutil.net_io_counters(pernic=True)
        interface = net.get('eth0')

        l1 = "U:{0}".format(humanize_file_size(interface[0]))
        l2 = "D:{0}".format(humanize_file_size(interface[1]))

        return (l1, 0), (l2, 1)

    @register_screen(order=5)
    def vcgencmd_measure_temp(self):
        stderr, gpu_temp = self.vcgencmd.measure_temp()
        psutil_sensors_temperature = psutil.sensors_temperatures()
        current_cpu_temp = psutil_sensors_temperature.get('cpu_thermal')[0].current

        hight_cpu_temp = psutil_sensors_temperature.get('cpu_thermal')[0].high
        critical_cpu_temp = psutil_sensors_temperature.get('cpu_thermal')[0].critical

        state_cpu_temp = None
        if hight_cpu_temp:
            state_cpu_temp = 'H'
        elif critical_cpu_temp:
            state_cpu_temp = 'C'

        l1 = "CPU: {:.1f}{}C".format(current_cpu_temp, chr(223))
        l2 = "GPU: {:.1f}{}C".format(gpu_temp.get('measure_temp'), chr(223))
        if state_cpu_temp:
            l2 = l2 + " " + state_cpu_temp
        return (l1, 0), (l2, 1)

    #@register_screen(order=6)
    def chrony_stats(self):
        chrony = self.chrony.chrony_tracking()

        print(chrony)

        l1 = ''
        l2 = ''
        return (l1, 0), (l2, 1)

    @register_screen(order=7)
    def gpsd_stats(self):
        stats = self.gpsd.get_current()
        mode = stats.get_mode()

        l1 = "{} {}[{}]".format(mode, stats.sats, stats.sats_valid)
        l2 = 'H:{:.2f} P:{:.2f}'.format(stats.hdop, stats.pdop)
        return (l1, 0), (l2, 1)


