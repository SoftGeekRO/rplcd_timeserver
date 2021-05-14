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

from tools import SubprocessShell


class ChronyParser(object):

    shell = SubprocessShell()

    chronyc_path = '/usr/bin/chronyc'

    def __init__(self):
        pass

    def chrony_tracking(self):

        indata = {}

        stderr, stdout = self.shell.shell_run(self.chronyc_path + ' tracking')

        data = stdout.decode('utf-8')

        rows = data.strip().split('\n')

        for line in rows:
            stats = line.split(':')
            if len(stats) < 2:
                return "unexpected output from chronyc, expected ':' in %s".format(data), indata
            name = stats[0].strip().replace(" ", "_").lower()

            if 'ref_time' in name:
                continue

            value_fields = stats[1].strip().split(" ")

            if "slow" in stats[1]:
                value_fields[0] = "-{0}".format(value_fields[0])

            indata[name] = value_fields[0]
        return stderr.decode('UTF-8'), indata
