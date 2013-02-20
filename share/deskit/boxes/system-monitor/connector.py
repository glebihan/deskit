#! /usr/bin/python
# -*- coding=utf-8 -*-

BOX_TITLE = "System"
ADDITIONAL_SCRIPTS = ["clock/clock.js"]
ADDITIONAL_STYLESHEETS = ["clock/clock.css"]

import os
import gobject
import commands
from Deskit.BaseConnector import BaseConnector

class UptimeWatcher(object):
    def __init__(self, callback):
        self._callback = callback
        self._timeout = None
    
    def start(self):
        self._timeout = gobject.timeout_add(30000, self._check_uptime)
        gobject.timeout_add(3000, self._check_uptime, False)
    
    def stop(self):
        if self._timeout:
            gobject.source_remove(self._timeout)
    
    def _check_uptime(self, keep_running = True):
        try:
            self._callback(",".join(commands.getoutput("uptime").split(" up ")[1].split(",")[:2]))
        except:
            pass
        return keep_running

class RAMUsageWatcher(object):
    def __init__(self, callback):
        self._callback = callback
        self._timeout = None
    
    def start(self):
        self._timeout = gobject.timeout_add(1000, self._check_usage)
    
    def stop(self):
        if self._timeout:
            gobject.source_remove(self._timeout)
    
    def _check_usage(self):
        try:
            data = {}
            for line in commands.getoutput("cat /proc/meminfo").splitlines():
                if ":" in line:
                    i = line.index(":")
                    key = line[:i]
                    value = line[i+1:].rstrip().lstrip()
                    data[key] = value
            if "MemTotal" in data:
                res = {}
                res["total"] = float(data["MemTotal"][:-3])
                res["free"] = float(data["MemFree"][:-3])
                res["cached"] = float(data["Cached"][:-3])
                res["usage"] = 100 * (res["total"] - res["free"] - res["cached"]) / res["total"]
                self._callback(res)
        except:
            pass
        return True

class CPUUsageWatcher(object):
    def __init__(self, callback):
        self._callback = callback
        self._pipe_read_end = None
        self._pipe_write_end = None
        self._watcher_pid = None
    
    def _start_watcher(self):
        self._pipe_read_end, self._pipe_write_end = os.pipe()
        watcher_pid = os.fork()
        if watcher_pid == 0:
            os.dup2(self._pipe_write_end, 1)
            os.execvp("mpstat", ("", "-P", "ALL", "1"))
        else:
            self._watcher_pid = watcher_pid
            gobject.timeout_add(1000, self._watch_usage)
    
    def _read_usage_line(self):
        res = ""
        try:
            c = os.read(self._pipe_read_end, 1)
            while c and c != "\n":
                res += c
                c = os.read(self._pipe_read_end, 1)
        except:
            res = ""
        return res
    
    def _parse_usage_line(self, line):
        try:
            fields = line.split()
            if len(fields) == 12 and fields[2] != "CPU":
                cpu, usage = fields[2:4]
                self._callback(cpu, float(usage))
        except:
            pass
        
    def _watch_usage(self):
        line = self._read_usage_line()
        while line:
            self._parse_usage_line(line)
            line = self._read_usage_line()
        return True
    
    def start(self):
        self._start_watcher()
    
    def stop(self):
        try:
            if self._watcher_pid:
                os.kill(self._watcher_pid, 9)
        except:
            pass
        try:
            os.close(self._pipe_read_end)
        except:
            pass
        try:
            os.close(self._pipe_write_end)
        except:
            pass

class Connector(BaseConnector):
    def _init(self):
        self._cpu_usage_watcher = CPUUsageWatcher(self._on_cpu_usage_update)
        self._ram_usage_watcher = RAMUsageWatcher(self._on_ram_usage_update)
        self._uptime_watcher = UptimeWatcher(self._on_uptime_update)
    
    def _on_cpu_usage_update(self, cpu, usage):
        self._emit("cpu_usage_update", {"cpu": cpu, "usage": usage})
    
    def _on_ram_usage_update(self, usage):
        self._emit("ram_usage_update", usage)
    
    def _on_uptime_update(self, uptime):
        self._emit("uptime_update", uptime)
    
    def start(self):
        self._cpu_usage_watcher.start()
        self._ram_usage_watcher.start()
        self._uptime_watcher.start()
    
    def stop(self):
        self._cpu_usage_watcher.stop()
        self._ram_usage_watcher.stop()
        self._uptime_watcher.stop()
    
    def render_element(self, element, *params):
        if element == "hostname":
            return commands.getoutput("hostname")
        if element == "kernel_version":
            return commands.getoutput("uname -r")
            
        return None
