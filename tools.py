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

import math
import datetime
import subprocess
from typing import Tuple

nsec_per_sec = 1000000000


class Dictionary(object):
    # Time
    # __time_dict = {
    #     'Ys': math.pow(10, 24),
    #     'Zs': math.pow(10, 21),
    #     'Es': math.pow(10, 18),
    #     'Ps': math.pow(10, 15),
    #     'Ts': math.pow(10, 12),
    #     'Gs': math.pow(10, 9),
    #     ('yr', 'yrs', 'year', 'years'): 31540000,
    #     ('mo', 'mos', 'month', 'months'): 2628000,
    #     'Ms': math.pow(10, 6),
    #     ('wk', 'week', 'weeks'): 604800,
    #     'day': 86400,
    #     ('hr', 'hour', 'hours'): 3600,
    #     'ks': 1000,
    #     ('min', 'minutes'): 60,
    #     ('s', 'sec', 'second', 'seconds'): 1,
    #     'ds': .1,
    #     'cs': .01,
    #     'ms': .001,
    #     'µs': math.pow(10, -6),
    #     'ns': math.pow(10, -9),
    #     'ps': math.pow(10, -12),
    #     'fs': math.pow(10, -15),
    #     'as': math.pow(10, -18),
    #     'zs': math.pow(10, -21),
    #     'ys': math.pow(10, -24)
    # }

    __time_dict = {
        'Ys': math.pow(10, 24),
        'Zs': math.pow(10, 21),
        'Es': math.pow(10, 18),
        'Ps': math.pow(10, 15),
        'Ts': math.pow(10, 12),
        'Gs': math.pow(10, 9),
        'yr': 31540000,
        'mo': 2628000,
        'Ms': math.pow(10, 6),
        'wk': 604800,
        'day': 86400,
        'hr': 3600,
        'ks': 1000,
        'min': 60,
        's': 1,
        'ds': .1,
        'cs': .01,
        'ms': .001,
        'µs': math.pow(10, -6),
        'ns': math.pow(10, -9),
        'ps': math.pow(10, -12),
        'fs': math.pow(10, -15),
        'as': math.pow(10, -18),
        'zs': math.pow(10, -21),
        'ys': math.pow(10, -24)
    }

    def time_dict(self):
        return self.__time_dict


# TIME CONVERSION
def convert_time(value, units_from_base, units_to_base):
    return value * units_from_base / units_to_base


def check_time(value, units_from, units_to, decimal_places=1):
    dictionary = Dictionary()  # Dictionary object
    time_dict = dictionary.time_dict()  # Time unit dictionary

    # Metric and Imperial distances
    if units_from in time_dict and units_to in time_dict:
        units_from_base = time_dict.get(
            units_from, None)  # Conversion to seconds
        units_to_base = time_dict.get(
            units_to, None)  # Conversion from seconds

        value = convert_time(value, units_from_base, units_to_base)
        return round(value, decimal_places), units_to

    return False


def normalize_timespec(ts):

    # first convert to raw ns
    timspec = check_time(ts, 's', 'ns', 0)

    if abs(timspec[0]) >= 1000:
        timspec = check_time(ts, 's', 'µs', 0)

        if abs(timspec[0]) >= 1000:
            timspec = check_time(ts, 's', 'ms', 0)

    return timspec


def make_nice(value: float, unit: str = 's'):
    prefixes = iter('µm ')
    while value > 1000:
        value /= 1000
        unit = next(prefixes) + unit[-1]
    return f'{value:g}{unit}'


def human_time(*args, **kwargs):
    secs = float(datetime.timedelta(*args, **kwargs).total_seconds())
    units = [("D", 86400), ("H", 3600), ("min", 60), ("", 1)]
    parts = []
    for unit, mul in units:
        if secs / mul >= 1 or mul == 1:
            if mul > 1:
                n = int(math.floor(secs / mul))
                secs -= n * mul
            else:
                n = secs if secs != int(secs) else int(secs)
            parts.append("%s%s%s" % (n, unit, "" if n == 1 else "s"))
    return ",".join(parts)


class SubprocessShell(object):
    """

    """
    platform_settings = {'executable': '/bin/bash'}

    def shell_run(self, cmd):
        """

        :param cmd:
        :return:
        """

        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, shell=True, **self.platform_settings)
        return proc.stderr, proc.stdout


def humanize_file_size(filesize):
    filesize = abs(filesize)

    if filesize == 0:
        return "0 Bytes"
    p = int(math.floor(math.log(filesize, 2)/10))
    return "%0.2f%s" % (filesize/math.pow(1024, p),
                        ['Bytes', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'][p])

