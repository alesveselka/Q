#!/usr/bin/python


class EventDispatcher(object):

    def __init__(self):
        self._listeners = []

    def on(self, event_type, listener):
        self._listeners.append((event_type, listener))

    def off(self, event_type):
        self._listeners = [l for l in self._listeners if l[0] != event_type]

    def dispatch(self, event_type, *data):
        map(lambda l: l[1](*data), [l for l in self._listeners if l[0] == event_type])
