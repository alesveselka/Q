#!/usr/bin/python

import time
from enum import EventType
from event_dispatcher import EventDispatcher


class Timer(EventDispatcher):

    def __init__(self, interval):
        super(Timer, self).__init__()

        self._interval = interval

    def start(self):
        while True:
            self.dispatch(EventType.HEARTBEAT)
            # time.sleep(self._interval)
            break
