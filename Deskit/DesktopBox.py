#! /usr/bin/python
# -*- coding=utf-8 -*-

import os
import imp
import logging
import sys

class DesktopBox(object):
    def __init__(self, deskit, box_id, box_name):
        self._deskit = deskit
        self.box_id = box_id
        self._box_name = box_name
        
        self._box_title = ""
        self._box_div_class = "desktop_box ui-widget ui-widget-content ui-corner-all ui-front"
        self._box_title_class = "box_title ui-widget-header ui-corner-all ui-helper-clearfix"
        self.additional_scripts = []
        self.additional_stylesheets = []
        
        self.box_path = os.path.join(deskit.share_dir, "deskit", "boxes", self._box_name)
        
        self._load_connector()
    
    def _load_connector(self):
        try:
            connector_filename = os.path.join(self.box_path, "connector.py")
            with open(connector_filename) as f:
                m = imp.load_module("connector%d" % self.box_id, f, connector_filename, ('.py', 'r', imp.PY_SOURCE))
            if hasattr(m, "Connector"):
                connector_class = getattr(m, "Connector")
                self._connector = connector_class(self._deskit, self)
            else:
                self._connector = None
            
            if hasattr(m, "BOX_TITLE"):
                self._box_title = getattr(m, "BOX_TITLE")
            if hasattr(m, "ADDITIONAL_SCRIPTS"):
                self.additional_scripts += getattr(m, "ADDITIONAL_SCRIPTS")
            if hasattr(m, "ADDITIONAL_STYLESHEETS"):
                self.additional_stylesheets += getattr(m, "ADDITIONAL_STYLESHEETS")
        except:
            logging.warn(sys.exc_info())
            self._connector = None
    
    def _replace_vars(self, data):
        while "${" in data:
            i = data.index("${")
            if not "}$" in data[i:]:
                break
            j = data[i:].index("}$")
            params = data[i+2:i+j].split(",")
            element = params[0]
            params = params[1:]
            data = data[:i] + self._render_element(element, *params) + data[i+j+2:]
        return data
    
    def _render_element(self, element, *params):
        if element == "connector":
            return "connector%d" % self.box_id
        if element == "box_id":
            return str(self.box_id)
        if element == "box_content":
            box_filename = os.path.join(self.box_path, "box.html")
            f = open(box_filename)
            box_content = f.read()
            f.close()
            return box_content
        if element == "box_title":
            return self._box_title
        
        if self._connector != None:
            res = self._connector.render_element(element, *params)
            if res != None:
                return res
        
        return self._deskit._render_element(element, *params)
    
    def render(self):
        theme_box_filename = os.path.join(self._deskit.theme_path, "box.html")
        f = open(theme_box_filename)
        box_html = f.read()
        f.close()
        
        box_html = self._replace_vars(box_html)
        
        return box_html
    
    def start_connector(self):
        if self._connector:
            self._connector.start()
    
    def stop_connector(self):
        if self._connector:
            self._connector.stop()
    
    def call_connector_method(self, method_name, params):
        if self._connector and hasattr(self._connector, method_name) and callable(getattr(self._connector, method_name)):
            getattr(self._connector, method_name)(params)
