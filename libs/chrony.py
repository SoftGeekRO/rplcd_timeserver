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

import re

from tools import SubprocessShell, normalize_timespec


class ChronyParser(object):

    shell = SubprocessShell()

    chronyc_path = '/usr/bin/chronyc'

    maximum_divergence_tolerated = float(1)

    tracking_fields = [
        'reference_id',
        'reference_name',
        'stratum',
        'ref_time_(utc)',
        'system_time',
        'last_offset',
        'rms_offset',
        'frequency',
        'residual_freq',
        'skew',
        'root_delay',
        'root_dispersion',
        'update_interval',
        'leap_status',
    ]

    def __init__(self):
        pass

    def chrony_tracking(self):

        indata = {}

        stderr, stdout = self.shell.shell_run(self.chronyc_path + ' -c tracking')

        data = stdout.decode('utf-8')

        data_raw = data.strip()

        clock_data = data_raw.split(',')

        if len(self.tracking_fields) == len(clock_data):
            for ndx, clock in enumerate(clock_data):
                indata[self.tracking_fields[ndx]] = clock

            clock_offset_from_ntp = float(clock_data[4])

            clock_offset = normalize_timespec(clock_offset_from_ntp)

            if abs(clock_offset_from_ntp) >= self.maximum_divergence_tolerated:
                clock_status = '{co}[max{mt}s]slow'.format(
                    co=int(clock_offset_from_ntp), mt=int(self.maximum_divergence_tolerated))
            else:
                clock_status = '{co}{co_unit}[{mt}s]'.format(
                    co=int(clock_offset[0]), co_unit=clock_offset[1], mt=int(self.maximum_divergence_tolerated))
            indata['clock_status'] = clock_status
        else:
            stderr = b'Unexpected error on Chrony tracking'


        #
        # for line in rows:
        #     stats = line.split(':')
        #     if len(stats) < 2:
        #         return "unexpected output from chronyc, expected ':' in %s".format(data), indata
        #     name = stats[0].strip().replace(" ", "_").lower()
        #     print(name)
        #     if 'ref_time' in name:
        #         continue
        #
        #     value_fields = stats[1].strip().split(" ")
        #
        #     if "slow" in stats[1]:
        #         value_fields[0] = "-{0}".format(value_fields[0])
        #
        #     indata[name] = value_fields[0]
        return stderr.decode('UTF-8'), indata
