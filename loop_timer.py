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
# Original created by terryltang.
# Modified by Wavky since 2018/2/8.

import threading


class LoopyTimer(object):
    """Python equivalent of JavaScript setInterval function
       Call a function after a specified number of seconds:

            timer = LoopyTimer(5.0, handler_func, args=[], kwargs={})

            timer.set_call_limits(5)    # timer will run eternally if you don't set a limit

            timer.start()

            timer.cancel()     # cancel the timer's further action if it's still waiting,
            will also destroy timer instance

        Ref: https://hg.python.org/cpython/file/2.7/Lib/threading.py
    """

    def __init__(self, interval, timer_handler, args: list = None, kwargs: dict = None):
        # timer interval, set integer or decimal for seconds or milliseconds
        self.interval = interval
        # real timer handler function
        self.timer_handler = timer_handler
        # positional arguments
        self.args = args or []
        # keyword arguments
        self.kwargs = kwargs or {}
        # create an internal timer object of threading.Timer
        self.timer = self.create_timer()
        # timer controls
        self.has_call_limit = False
        self.logger = None
        self.running = False
        self._is_destroyed = False

    def create_timer(self):
        return threading.Timer(self.interval, self.wrapper_handler, args=self.args, kwargs=self.kwargs)

    def set_logger(self, logger, args: list = None, kwargs: dict = None):
        """ This function sets a logger function for the timer, which will be called everytime after
            timer handler is called.
        """
        self.logger = logger
        self.logger_args = args or []
        self.logger_kwargs = kwargs or {}

    def set_call_limits(self, num):
        """
        This function sets timer counter as well as its upper limit.
        For correct functionality, you should only call this before start().

        :param num: enable limit if num > 0, otherwise the limit is disable.
        """
        self.has_call_limit = num > 0
        self.call_limits = num
        self.count = 0

    def wrapper_handler(self, *args, **kwargs):
        if self.has_call_limit and self.count >= self.call_limits:
            self.running = False
            self.__destroy()
            return
        # actually call the timer handler, the timer thread will be destroyed after handler function execution
        self.timer_handler(*args, **kwargs)
        if self.has_call_limit:
            self.count += 1
        # call logger function
        if self.logger:
            self.logger(*self.logger_args, **self.logger_kwargs)
        # create a new timer thread to continue calling wrapper_handler
        self.timer = self.create_timer()
        # start the new timer thread, wait 'interval' amount of time and execute timer_hander again
        self.timer.start()

    def start(self):
        """
        :raise: RuntimeError if timer has been start/cancel/destroyed already.
        """
        if not self._is_destroyed:
            if self.running is True:
                raise RuntimeError('Can not start twice.')
            self.running = True
            # create a new internal timer object of threading.Timer.
            self.timer = self.create_timer()
            self.timer.start()
        else:
            raise RuntimeError('Can not start a destroyed timer.')

    def cancel(self):
        """
        Cancel timer will also destroy timer function.
        You can not reuse the timer after invoke this function.

        :return:
        """
        if not self._is_destroyed:
            self.running = False
            self.timer.cancel()
            # The cancel function only prevents timer being called but the thread might still be active, so make
            # sure you call join() to end the thread
            self.timer.join()
            self.__destroy()

    def __destroy(self):
        self._is_destroyed = True
        # Reset logger and call limit
        self.count = 0
        self.call_limits = 0
        self.has_call_limit = False
        self.set_logger(None)
        self.timer_handler = None

    def is_running(self):
        return self.running
