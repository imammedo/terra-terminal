#!/usr/bin/python
# -*- coding: utf-8; -*-
"""
Copyright (C) 2013 - Arnaud SOURIOUX <six.dsn@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>

"""
from gi.repository import Gdk
from base64 import b64encode, b64decode
import ConfigParser
import os

class LayoutManager():

    config = ConfigParser.SafeConfigParser(
        {
            'id': '0',
            'posx': '0',
            'posy': '0',
            'width': '1280',
            'height': '1024',
            'tabs': '0',
            'fullscreen': 'False'
        })

    cfg_dir = os.environ['HOME'] + '/.config/terra/'
    cfg_file = 'layout.cfg'
    cfg_full_path = cfg_dir + cfg_file

    config.read(cfg_full_path)

    callback_list = []

    @staticmethod
    def get_conf(section, key):
        try:
            value = LayoutManager.config.get(section, key)
        except ConfigParser.Error:
            print ("[DEBUG] No option '%s' found in namespace '%s'." %
                    (key, section))
            return None

        try:
            return int(value)
        except ValueError:
            if value == 'True':
                return True
            elif value == 'False':
                return False
            else:
                if key == 'select-by-word':
                    value = b64decode(value)
                return value

    @staticmethod
    def set_conf(section, key, value):
        if key == 'select-by-word':
            value = b64encode(value)
        try:
            LayoutManager.config.set(section, key, str(value))
        except ConfigParser.NoSectionError:
            print ("[DEBUG] No section '%s'." %
                    (section))
            LayoutManager.config.add_section(section)
            LayoutManager.config.set(section, key, str(value))
        except ConfigParser.Error:
            print ("[DEBUG] No option '%s' found in namespace '%s'." %
                    (key, section))
            return

    @staticmethod
    def save_config():
        if not os.path.exists(LayoutManager.cfg_dir):
            os.mkdir(LayoutManager.cfg_dir)

        with open(LayoutManager.cfg_full_path, 'wb') as configfile:
            LayoutManager.config.write(configfile)
