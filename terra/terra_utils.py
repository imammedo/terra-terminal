#!/usr/bin/python
# -*- coding: utf-8; -*-
"""
Copyright (C) 2013 - Arnaud SOURIOUX <six.dsn@gmail.com>
Copyright (C) 2012 - Ozcan ESEN <ozcanesen~gmail.com>

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

from gi.repository import Gtk, Gdk
from layout import LayoutManager
from config import ConfigManager
from operator import attrgetter

import os
import commands

def get_paned_parent(vte_list, ParId):
    parent = [item for item in vte_list if item.id == ParId]
    if len(parent):
        return parent[0]
    return None

def check_heritage(val, elems, _elems, liste):
    parent = get_paned_parent(_elems, val.parent)
    if parent and parent in _elems:
        _elems.append(val)
        if (val in liste):
            liste.remove(val)
        for vale in liste:
            if vale.parent == val.parent and vale.id <= min(liste, key=lambda a: attrgetter('id')(a)).id:
                return check_heritage(vale, elems, _elems, liste)
        return 1
    return 0

def my_sorted(elems):
    _elems = []
    liste = list(elems)
    while (len(liste)):
        liste.sort(key=lambda a: attrgetter('id')(a))
        for val in liste:
            if val.id == 0:
                _elems.append(val)
                if (val in liste):
                    liste.remove(val)
                break
            if check_heritage(val, elems, _elems, liste):
                break
    return (_elems)

def get_screen(name):
    if (LayoutManager.get_conf(name, 'enabled') == False):
        return None
    posx = LayoutManager.get_conf(name, 'posx')
    posy = LayoutManager.get_conf(name, 'posy')
    width = LayoutManager.get_conf(name, 'width')
    height = LayoutManager.get_conf(name, 'height')
    if (posx == None or posy == None or width == None or height == None):
        posx = LayoutManager.get_conf('DEFAULT', 'posx')
        posy = LayoutManager.get_conf('DEFAULT', 'posy')
        width = LayoutManager.get_conf('DEFAULT', 'width')
        height = LayoutManager.get_conf('DEFAULT', 'height')
    rect = Gdk.Rectangle()
    rect.x = posx
    rect.y = posy
    rect.width = width
    rect.height = height
    return (rect)

def cannot_bind(app):
    ConfigManager.set_conf('hide-on-start', False)
    ConfigManager.set_conf('losefocus-hiding', False)
    msgtext = _("Another application using '%s'. Please open preferences and change the shortcut key.") % ConfigManager.get_conf('global-key')
    msgbox = Gtk.MessageDialog(app, Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.WARNING, Gtk.ButtonsType.OK, msgtext)
    msgbox.run()
    msgbox.destroy()

def get_pwd(pid):
    try:
        pwd = os.popen2("pwdx " + str(pid))[1].read().split(' ')[1].split()[0]
        return pwd
    except:
        return None

def get_running_cmd(ppid):
    pid = commands.getstatusoutput("ps -o pid= --ppid " + str(ppid))[1]
    value = " ".join(commands.getstatusoutput("ps -p " + str(pid) + " o user=,cmd=,etime=")[1].split()).split(' ')
    return(str("%s@%s $>%s %s"% (value[0], os.uname()[1], value[1], value[-1])))
