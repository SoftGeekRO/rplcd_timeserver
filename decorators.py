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

import psutil


def class_register_screen(cls) -> type:
    """

    :param cls:
    :return:
    """
    cls._propdict = {}
    cls.methods_ordered = []

    # what NTP daemons list to be search by
    ntp_daemons_list = ['ntpq', 'chronyd']
    ntp_daemon = ntp_daemons_list

    # NTP daemon currently running
    ntp_daemon_running = None

    # check if in the current deploy is running chrony or ntpq
    for proc in psutil.process_iter(['name']):
        proc_name = proc.info.get('name')
        if proc.info.get('name') in ntp_daemons_list:
            ntp_daemon_running = proc_name
            break

    for method_name in dir(cls):
        method = getattr(cls, method_name)
        if hasattr(method, '_args') and ('order' in method._args.keys()):
            cls._propdict.update(
                {"{}.{}".format(cls.__name__, method_name): method._args})

    if ntp_daemon_running:
        ntp_daemon.remove(ntp_daemon_running)
        for key, val in cls._propdict.copy().items():
            daemon = key.split('.')[1]
            if daemon.startswith(ntp_daemon[0]):
                cls._propdict.pop(key, None)

    cls.methods_ordered = sorted(cls._propdict.items(), key=lambda x: x[1]['order'])

    return cls


def register_screen(order, screen_time=5, *args, **kwargs):
    """Define the default attributes for registered screen methods.

    :param order: int Order for each screen
    :param screen_time: int Time of each screen
    :param dynamic: bool set if the screen is updated every cycle
    :param args:
    :param kwargs:
    :return:
    """
    def wrapper(func):
        kwargs.update({'order': order, 'screen_time': screen_time})
        func.args = args
        func._args = kwargs
        return func
    return wrapper
