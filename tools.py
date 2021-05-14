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
import asyncio
import subprocess
from typing import Tuple


def humanize_file_size(filesize):
    filesize = abs(filesize)

    if filesize == 0:
        return "0 Bytes"
    p = int(math.floor(math.log(filesize, 2)/10))
    return "%0.2f%s" % (filesize/math.pow(1024, p),
                         ['Bytes', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'][p])


class SubprocessShell(object):

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


