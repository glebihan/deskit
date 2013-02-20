#! /usr/bin/python
# -*- coding=utf-8 -*-

import json

class BaseConnector(object):
    def __init__(self, deskit, box):
        self._deskit = deskit
        self._box = box
        self._init()
    
    def _init(self):
        pass
    
    def _emit(self, signal_name, param = None):
        self._deskit.execute_script("connector%d.emit(\"%s\", %s);" % (self._box.box_id, signal_name, json.dumps(param)))
    
    def render_element(self, element, *params):
        return None
