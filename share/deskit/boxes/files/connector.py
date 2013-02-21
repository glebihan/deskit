#! /usr/bin/python
# -*- coding=utf-8 -*-

BOX_TITLE = "Files"

from Deskit.BaseConnector import BaseConnector
import os
import re
import subprocess
import gtk
import urllib

class Connector(BaseConnector):
    def _init(self):
        self._path = subprocess.check_output(['xdg-user-dir', 'DESKTOP']).splitlines()[0]
        
    def initiate(self, params):
        for filename in os.listdir(self._path):
            self.add_file(os.path.join(self._path, filename))
    
    def add_file(self, filename):
        if os.path.isdir(filename):
            icon_filename = gtk.icon_theme_get_default().lookup_icon("folder", 48, 0).get_filename()
        else:
            icon_filename = gtk.icon_theme_get_default().lookup_icon("gtk-file", 48, 0).get_filename()
        self._emit("add_file", {"filename": filename, "basename": os.path.split(filename)[1], "icon": "file://" + urllib.pathname2url(icon_filename)})
