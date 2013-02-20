#! /usr/bin/python
# -*- coding=utf-8 -*-

import gtk
import webkit
import os
import sys
import urlparse
import urllib
import logging
from DesktopBox import DesktopBox

class DeskitWindow(gtk.Window):
    def __init__(self, application):
        gtk.Window.__init__(self)
        self._application = application
        
        if not self._application.options.test:
            self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DESKTOP)
            screen = gtk.gdk.screen_get_default()
            self.set_size_request(screen.get_width(), screen.get_height())
        else:
            self.fullscreen()
        self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#000000"))
        
        self._webview = webkit.WebView()
        self.add(self._webview)
        
        self.connect("delete_event", lambda w,e: gtk.main_quit())
    
    def set_html(self, html):
        self._webview.load_html_string(html, "file:///")
    
    def execute_script(self, script):
        self._webview.execute_script(script)

class Deskit(object):
    def __init__(self, options):
        self.options = options
        self._window = DeskitWindow(self)
        
        self.share_dir = os.path.abspath(self.options.share_dir)
        self.theme_path = os.path.join(self.share_dir, "deskit", "themes", self.options.theme)
        
        self._required_js_libs = [
            "file://" + urllib.pathname2url(os.path.join(self.share_dir, "deskit", "js", "connector.js")),
            "http://code.jquery.com/jquery-1.9.1.js",
            "http://code.jquery.com/ui/1.10.1/jquery-ui.js"
        ]
        
        self._required_css_files = [
            "file://" + urllib.pathname2url(os.path.join(self.theme_path, "style.css")),
            "file://" + urllib.pathname2url(os.path.join(self.theme_path, "jqueryui-theme", "jquery-ui.css"))
        ]
        
        self._box_id = 0
        self._boxes_config = {
            "left_column": [
                "rss-feed"
            ],
            "right_column": [
                "system-monitor",
                "weather"
            ]
        }
        self._boxes = {
        }
    
    def _load_desktop(self):
        template_file = os.path.join(self.theme_path, "index.html")
        f = open(template_file)
        data = f.read()
        f.close()
        
        data = self._replace_vars(data)
        
        self._window.set_html(data)
        #~ print data
    
    def _render_element(self, element, *params):
        if element == "javascript_libraries_includes":
            res = ""
            for lib in self._required_js_libs:
                res += "<script type='text/javascript' src='%s'></script>" % lib
            for zone in self._boxes:
                for box in self._boxes[zone]:
                    for lib in box.additional_scripts:
                        res += "<script type='text/javascript' src='file://%s'></script>" % urllib.pathname2url(os.path.join(box.box_path, lib))
            return res
        if element == "css_files_includes":
            res = ""
            for css in self._required_css_files:
                res += "<link rel='stylesheet' type='text/css' href='%s'/>" % css
            for zone in self._boxes:
                for box in self._boxes[zone]:
                    for css in box.additional_stylesheets:
                        res += "<link rel='stylesheet' type='text/css' href='file://%s'/>" % urllib.pathname2url(os.path.join(box.box_path, css))
            return res
        if element == "boxes":
            box_zone = params[0]
            if box_zone in self._boxes:
                res = ""
                for box in self._boxes[box_zone]:
                    res += box.render()
                return res
            else:
                return ""
        if element == "init_scripts":
            res = "<script type='text/javascript'>\n"
            for zone in self._boxes:
                for box in self._boxes[zone]:
                    res += "var connector%d = new Connector(%d);\n" % (box.box_id, box.box_id)
            res += "</script>\n"
            return res
            
        print element, params
        return ""
    
    def _load_boxes(self):
        box_id = 0
        for zone in self._boxes_config:
            if not zone in self._boxes:
                self._boxes[zone] = []
            for box_name in self._boxes_config[zone]:
                box = self._load_box(box_id, box_name)
                if box:
                    self._boxes[zone].append(box)
                    box_id += 1
    
    def _load_box(self, box_id, box_name):
        try:
            box = DesktopBox(self, box_id, box_name)
            return box
        except:
            logging.warn(sys.exc_info())
    
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
    
    def run(self):
        self._load_boxes()
        self._load_desktop()
        self._window.show_all()
        
        for zone in self._boxes:
            for box in self._boxes[zone]:
                box.start_connector()
        
        gtk.main()
        
        for zone in self._boxes:
            for box in self._boxes[zone]:
                box.stop_connector()
    
    def execute_script(self, script):
        self._window.execute_script(script)
