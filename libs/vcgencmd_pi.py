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


class VcgencmdParser(object):

    shell = SubprocessShell()

    vcgencmd_bin = '/usr/bin/vcgencmd'

    def measure_temp(self):
        """

        :return:
        """

        indata = {}

        stderr, stdout = self.shell.shell_run(self.vcgencmd_bin + ' measure_temp')

        data = stdout.decode('utf-8')

        measure_temp = re.search(r'-?\d+\.?\d*', data)
        indata.update({'measure_temp': float(measure_temp.group())})

        return stderr.decode('UTF-8'), indata
