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

from tools import humanize_file_size, normalize_timespec
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
        #self.screen_option_time = current_screen[1].get('screen_time')

    def display_screen(self):
        # execute the screen method
        line0, line1 = getattr(self, self.screen_method)()

        line0_align = 'CENTER' if len(line0) == 2 else line0[2]

        self.lcd_screen.print_line(line0[0], line0[1], align=line0_align)
        self.lcd_screen.print_line(line1[0], line1[1], align=line0_align)

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

        l1 = "CPU Frequency".format()
        l2 = "{:d}[{:d}]Mhz".format(int(cpu_freq.current), int(cpu_freq.max))

        return (l1, 0), (l2, 1)

    @register_screen(order=4)
    def psutil_cpu_load(self):
        cpu_load = psutil.getloadavg()

        l1 = "CPU Load".format(cpu_load[0])
        l2 = "{0}/{1}/{2}".format(cpu_load[0], cpu_load[1], cpu_load[2])

        return (l1, 0), (l2, 1)

    @register_screen(order=5)
    def psutil_network_counters(self):
        net = psutil.net_io_counters(pernic=True)
        interface = net.get('eth0')

        l1 = "U:{0}".format(humanize_file_size(interface[0]))
        l2 = "D:{0}".format(humanize_file_size(interface[1]))

        return (l1, 0), (l2, 1)

    @register_screen(order=6)
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

    @register_screen(order=7)
    def chrony_status(self):
        stderr, chrony = self.chrony.chrony_tracking()

        reference_name = chrony.get('reference_name')
        clock_status = chrony.get('clock_status')

        l1 = '{reference_name}'.format(reference_name=reference_name)
        l2 = '{clock_status}'.format(clock_status=clock_status)
        return (l1, 0), (l2, 1)

    @register_screen(order=8)
    def chrony_root_delay(self):
        """This is the total of the network path delays to the stratum-1 computer from which the computer is ultimately
        synchronised. In certain extreme situations, this value can be negative.
        (This can arise in a symmetric peer arrangement where the computers’ frequencies are not tracking each other
        and the network delay is very short relative to the turn-around time at each computer.)

        :return:
        """
        stderr, chrony = self.chrony.chrony_tracking()

        reference_name = chrony.get('reference_name')
        root_delay = chrony.get('root_delay')
        root_root_dispersion = chrony.get('root_dispersion')

        _root_delay = normalize_timespec(float(root_delay))
        _root_root_dispersion = normalize_timespec(float(root_root_dispersion))

        l1 = '{} Root Delay'.format(reference_name)
        l2 = '{root_delay} {root_delay_unit}'.format(root_delay=int(_root_delay[0]),
                                                    root_delay_unit=_root_delay[1])
        return (l1, 0, 'CENTER'), (l2, 1, 'CENTER')

    @register_screen(order=9)
    def chrony_root_dispersion(self):
        """This is the total dispersion accumulated through all the computers back to the stratum-1 computer from
        which the computer is ultimately synchronised. Dispersion is due to system clock resolution,
        statistical measurement variations etc.

        :return:
        """
        stderr, chrony = self.chrony.chrony_tracking()

        reference_name = chrony.get('reference_name')
        root_delay = chrony.get('root_delay')
        root_root_dispersion = chrony.get('root_dispersion')

        _root_delay = normalize_timespec(float(root_delay))
        _root_root_dispersion = normalize_timespec(float(root_root_dispersion))

        l1 = '{} Root Disper'.format(reference_name)
        l2 = '{root_root_dispersion} {root_root_dispersion_unit}'.format(
            root_root_dispersion=int(_root_root_dispersion[0]),
            root_root_dispersion_unit=chr(228)+"s" if _root_root_dispersion[1] == 'µs' else _root_root_dispersion[1])
        return (l1, 0, 'CENTER'), (l2, 1, 'CENTER')

    @register_screen(order=10)
    def chrony_last_offset(self):
        """This is the estimated local offset on the last clock update.

        :return:
        """
        stderr, chrony = self.chrony.chrony_tracking()

        reference_name = chrony.get('reference_name')
        last_offset = chrony.get('last_offset', 0.0)

        last_off = normalize_timespec(float(last_offset))

        l1 = '{} Last offset'.format(reference_name)
        l2 = '{last_off} {last_off_unit}'.format(last_off=int(last_off[0]),
                                                 last_off_unit=chr(228)+"s" if last_off[1] == 'µs' else last_off[1])
        return (l1, 0), (l2, 1)

    @register_screen(order=11)
    def chrony_rms_offset(self):
        """This is a long-term average of the offset value.

        :return:
        """
        stderr, chrony = self.chrony.chrony_tracking()

        reference_name = chrony.get('reference_name')
        rms_offset = chrony.get('rms_offset', 0.0)

        rms_off = normalize_timespec(float(rms_offset))

        l1 = '{} RMS offset'.format(reference_name)
        l2 = '{rms_off} {rms_off_unit}'.format(rms_off=int(rms_off[0]),
                                               rms_off_unit=chr(228)+"s" if rms_off[1] == 'µs' else rms_off[1])
        return (l1, 0), (l2, 1)

    @register_screen(order=12)
    def chrony_system_time(self):
        """In normal operation, chronyd never steps the system clock, because any jump in the timescale can have
        adverse consequences for certain application programs. Instead, any error in the system clock is corrected by
        slightly speeding up or slowing down the system clock until the error has been removed,
        and then returning to the system clock’s normal speed.
        A consequence of this is that there will be a period when the system clock
        (as read by other programs using the gettimeofday() system call, or by the date command in the shell)
        will be different from chronyd's estimate of the current true time (which it reports to NTP clients when it is
        operating in server mode). The value reported on this line is the difference due to this effect.

        :return:
        """
        stderr, chrony = self.chrony.chrony_tracking()

        reference_name = chrony.get('reference_name')
        system_time = chrony.get('system_time', 0.0)

        st = normalize_timespec(float(system_time))

        l1 = '{0} SysTime'.format(reference_name)
        l2 = '{0}{1} {2}'.format(int(st[0]), chr(228)+"s" if st[1] == 'µs' else st[1], "fast" if st[0] > 1 else "slow")

        return (l1, 0), (l2, 1)

    @register_screen(order=13)
    def chrony_frequency(self):
        """The ‘frequency’ is the rate by which the system’s clock would be would be wrong if chronyd was not
        correcting it. It is expressed in ppm (parts per million). For example, a value of 1ppm would mean that when
        the system’s clock thinks it has advanced 1 second, it has actually advanced by 1.000001 seconds relative to
        true time.

        :return:
        """
        stderr, chrony = self.chrony.chrony_tracking()

        reference_name = chrony.get('reference_name')
        frequency = chrony.get('frequency', 0.0)

        l1 = '{0} Frequency'.format(reference_name)
        l2 = '{0} ppm {1}'.format(frequency, "fast" if float(frequency) > 1 else "slow")

        return (l1, 0), (l2, 1)

    @register_screen(order=14)
    def chrony_residual_freq(self):
        """This shows the ‘residual frequency’ for the currently selected reference source.
        This reflects any difference between what the measurements from the reference source indicate the frequency
        should be and the frequency currently being used. The reason this is not always zero is that a smoothing
        procedure is applied to the frequency. Each time a measurement from the reference source is obtained and a new
        residual frequency computed, the estimated accuracy of this residual is compared with the estimated accuracy
        (see ‘skew’ next) of the existing frequency value. A weighted average is computed for the new frequency,
        with weights depending on these accuracies. If the measurements from the reference source follow a consistent
        trend, the residual will be driven to zero over time.

        :return:
        """
        stderr, chrony = self.chrony.chrony_tracking()

        reference_name = chrony.get('reference_name')
        residual_freq = chrony.get('residual_freq', 0.0)

        l1 = '{0} Residual freq'.format(reference_name)
        l2 = '{0} ppm'.format(residual_freq)

        return (l1, 0), (l2, 1)

    @register_screen(order=15)
    def chrony_skew(self):
        """This is the estimated error bound on the frequency.

        :return:
        """
        stderr, chrony = self.chrony.chrony_tracking()

        reference_name = chrony.get('reference_name')
        skew = chrony.get('skew', 0.0)

        l1 = '{0} Skew'.format(reference_name)
        l2 = '{0} ppm'.format(skew)

        return (l1, 0), (l2, 1)

    @register_screen(order=16)
    def gpsd_stats(self):
        stats = self.gpsd.get_current()
        mode = stats.get_mode()

        l1 = "{} {}[{}]".format(mode, stats.sats, stats.sats_valid)
        l2 = 'H:{:.2f} P:{:.2f}'.format(stats.hdop, stats.pdop)
        return (l1, 0), (l2, 1)


