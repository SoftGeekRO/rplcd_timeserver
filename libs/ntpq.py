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

from typing import Tuple
import re
import sys

from tools import SubprocessShell


class NtpqParser(object):

    header_line = []

    shell = SubprocessShell()

    def __init__(self):
        pass

    def parse_row(self, row):
        entry = row.split()
        result = {}
        # check if every entry has the same length with headers
        if len(entry) == len(self.header_line):
            for k, v in enumerate(self.header_line):
                result[v] = entry[k]
            return result
        return result

    def ntpq_pn(self) -> Tuple[str, list]:
        """Get the stdout of "ntpq -pn"

        :return:
        """
        indata = []

        stderr, stdout = self.shell.shell_run("ntpq -pn")

        data = stdout.decode("utf-8")

        rows = data.split("\n")

        self.header_line = re.findall(r'\w+', rows[0])

        for row in rows[:-1]:
            if row == "\n":
                # ignore any \n separator
                continue
            elif row.startswith("="):
                # detect the split row between header and data
                continue
            elif row.split()[0] == self.header_line[0]:
                # detect the header row and ignore any process
                continue
            else:
                indata.append(self.parse_row(row))
        return stderr.decode("UTF-8"), indata

    def ntpq_rv(self) -> Tuple[str, dict]:
        """Calculate and display the NTPD accuracy
        Retrieve the precision and clock_jitter from the ntp server

        :return:
        """
        indata = {}
        stderr, stdout = self.shell.shell_run('ntpq -c rv')

        data = stdout.decode("UTF-8")

        precision_search = re.search(r'precision=(.*?),', data, re.S)
        precision = precision_search.group(1)

        clock_jitter_search = re.search(r'.*clk_jitter=(.*?),', data, re.S)
        clock_jitter = clock_jitter_search.group(1)

        rootdisp_search = re.search(r'.*rootdisp=(.*?),', data, re.S)
        rootdisp = rootdisp_search.group(1)

        offset_search = re.search(r'.*offset=(.*?),', data, re.S)
        offset = offset_search.group(1)

        frequency_search = re.search(r'.*frequency=(.*?),', data, re.S)
        frequency = frequency_search.group(1)

        sys_jitter_search = re.search(r'.*sys_jitter=(.*?),', data, re.S)
        sys_jitter = sys_jitter_search.group(1)

        if all([precision, clock_jitter, rootdisp, sys_jitter, frequency, sys_jitter]):
            precision = (1 / 2.0 ** abs(float(precision))) * 1000000.0
            indata.update({
                'precision': "{:.5f} {}s".format(precision, chr(0xE4)),
                'clock_jitter': "{:>4} ms".format(clock_jitter),
                'rootdisp': rootdisp,
                'offset': "{:>6}".format(offset),
                'frequency': "{:>3}".format(frequency),
                'sys_jitter': "{:>6} ms".format(sys_jitter)
            })

        return stderr.decode('UTF-8'), indata

    def ntptime(self) -> Tuple[str, dict]:
        """Statistics from ntptime command

        :return:
        """
        indata = {}
        stdout, stderr = self.shell.asyncio_run("/usr/sbin/ntptime")

        data = stdout.decode("UTF-8")

        precision_tolerance = re.search(r'precision (.* us).*tolerance (.* ppm)', data, re.M | re.S)
        frequency_search = re.search(r'frequency (.* ppm).*interval (.* s),', data, re.S)

        if all([precision_tolerance]):
            indata.update({
                'precision': "{:>8}".format(precision_tolerance.group(1)),
                'tolerance': "{:>7}".format(precision_tolerance.group(2)),
                'frequency': "{:>9}".format(frequency_search.group(1)),
                'interval': "{:>3}".format(frequency_search.group(2)),
            })

        return stderr.decode('UTF-8'), indata


