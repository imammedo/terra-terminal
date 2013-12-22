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

from gi.repository import Gtk, Vte, GLib, Gdk, GdkPixbuf, GObject, GdkX11

from terra import globalhotkeys

from VteObject import VteObjectContainer
from config import ConfigManager, ConfigParser
from layout import LayoutManager
from dialogs import RenameDialog
from dbusservice import DbusService
from i18n import _

from math import floor
import os
import time
import sys

Wins = None

class TerminalWin(Gtk.Window):

    def __init__(self, name, monitor):
        super(TerminalWin, self).__init__()

        self.builder = Gtk.Builder()
        self.builder.set_translation_domain('terra')
        self.builder.add_from_file(ConfigManager.data_dir + 'ui/main.ui')
        self.name = name
        self.screen_id = int(name.split('-')[1])
        ConfigManager.add_callback(self.update_ui)
        
        self.screen = self.get_screen()
        self.monitor = monitor

        self.init_transparency()
        self.init_ui()
        self.update_ui()

        if not ConfigManager.get_conf('hide-on-start'):
            self.show_all()
        self.paned_childs = {}

    def init_ui(self):
        self.set_title(_('Terra Terminal Emulator'))

        if LayoutManager.get_conf(self.name, 'fullscreen'):
            self.is_fullscreen = True
        else:
            self.is_fullscreen = False
        
        self.slide_effect_running = False
        self.losefocus_time = 0
        self.set_has_resize_grip(False)

        self.resizer = self.builder.get_object('resizer')
        self.resizer.unparent()
        self.resizer.connect('motion-notify-event', self.on_resize)
        self.resizer.connect('button-release-event', self.update_resizer)

        self.logo = self.builder.get_object('logo')
        self.logo_buffer = GdkPixbuf.Pixbuf.new_from_file_at_size(ConfigManager.data_dir  + 'image/terra.svg', 32, 32)
        self.logo.set_from_pixbuf(self.logo_buffer)

        self.set_icon(self.logo_buffer)

        self.notebook = self.builder.get_object('notebook')
        self.notebook.set_name('notebook')

        self.tabbar = self.builder.get_object('tabbar')
        self.buttonbox = self.builder.get_object('buttonbox')

        # radio group leader, first and hidden object of buttonbox
        # keeps all other radio buttons in a group
        self.radio_group_leader = Gtk.RadioButton()
        self.buttonbox.pack_start(self.radio_group_leader, False, False, 0)
        self.radio_group_leader.set_no_show_all(True)

        self.new_page = self.builder.get_object('btn_new_page')
        self.new_page.connect('clicked', lambda w: self.add_page())

        self.btn_fullscreen = self.builder.get_object('btn_fullscreen')
        self.btn_fullscreen.connect('clicked', lambda w: self.toggle_fullscreen())

        self.connect('destroy', lambda w: self.quit())
        self.connect('delete-event', lambda w, x: self.delete_event_callback())
        self.connect('key-press-event', self.on_keypress)
        self.connect('focus-out-event', self.on_window_losefocus)
        self.connect('configure-event', self.on_window_move)
        self.add(self.resizer)

        added = False
        for section in LayoutManager.get_sections():
            tabs = str('Tabs-%d'% self.screen_id)
            if (section.find(tabs) == 0 and LayoutManager.get_conf(section, 'enabled') == True):
                self.add_page(page_name=str(section))
                added = True
        if (not added):
            self.add_page()

        for button in self.buttonbox:
            if button == self.radio_group_leader:
                continue
            else:
                button.set_active(True)
                break

    def delete_event_callback(self):
        self.hide()
        return True

    def on_window_losefocus(self, window, event):
        if self.slide_effect_running:
            return
        if ConfigManager.disable_losefocus_temporary:
            return
        if not ConfigManager.get_conf('losefocus-hiding'):
            return

        if self.get_property('visible'):
            self.losefocus_time = GdkX11.x11_get_server_time(self.get_window())
            if ConfigManager.get_conf('use-animation'):
                self.slide_up()
            self.unrealize()
            self.hide()

    def on_window_move(self, window, event):
        winpos = self.get_position()
        if not self.is_fullscreen:
            self.monitor.x = winpos[0]
            self.monitor.y = winpos[1]
            LayoutManager.set_conf(self.name, 'posx', winpos[0])
            LayoutManager.set_conf(self.name, 'posy', winpos[1])

    def exit(self):
        if ConfigManager.get_conf('prompt-on-quit'):
            ConfigManager.disable_losefocus_temporary = True
            msgtext = _("Do you really want to quit?")
            msgbox = Gtk.MessageDialog(self, Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.WARNING, Gtk.ButtonsType.YES_NO, msgtext)
            response = msgbox.run()
            msgbox.destroy()
            ConfigManager.disable_losefocus_temporary = False

            if response != Gtk.ResponseType.YES:
                return False
        quit_prog()

    def save_conf(self, keep=True):
        tabs = str('Tabs-%d'% self.screen_id)
        if (not keep):
            for section in LayoutManager.get_sections():
                if (section.find(tabs) == 0):
                    LayoutManager.del_conf(section)
            LayoutManager.del_conf(self.name)
        else:
            LayoutManager.set_conf(self.name, 'width', self.monitor.width)
            LayoutManager.set_conf(self.name, 'height', self.monitor.height)
            LayoutManager.set_conf(self.name, 'fullscreen', self.is_fullscreen)
            LayoutManager.set_conf(self.name, 'enabled', 'True')

            #we delete all tabs first to avoid unused
            for section in LayoutManager.get_sections():
                if (section.find("Tabs-%d"% (self.screen_id)) == 0):
                    # we won't delete those who are set as disabled
                    if LayoutManager.get_conf(section, 'enabled') == True:
                        LayoutManager.del_conf(section)

            #we delete all layouts first to avoid unused
            for section in LayoutManager.get_sections():
                if (section.find("Child-%d"% (self.screen_id)) == 0):
                    print("Del ChildName: %s"% (section))
                    LayoutManager.del_conf(section)

            #We add them all
            tabid = 0
            for button in self.buttonbox:
                if button != self.radio_group_leader:
                    section = str('Tabs-%d-%d'% (self.screen_id, tabid))
                    LayoutManager.set_conf(section, 'name', button.get_label())
                    LayoutManager.set_conf(section, 'enabled', 'True')
                    #button.progname is inserted via setattr in add_page
                    if (button.progname):
                        LayoutManager.set_conf(section, 'progname', button.progname)
                    tabid = tabid + 1
 
            tabid = 0
            self.paned_childs = {}
            for container in self.notebook.get_children():
                for child in container.get_children():
                    self.print_childs(child, tabid, True)
                    tabid = tabid + 1

            childid = 0
            print("Len: %d"% (len(self.paned_childs)))
            for child in self.paned_childs.itervalues():
                section = str('Child-%d-%d-%d'% (self.screen_id, child[0], childid))
                print("add child: %s => %c:%d"% (section, child[1], child[2]))
                LayoutManager.set_conf(section, 'type', child[1])
                LayoutManager.set_conf(section, 'pos', child[2])
                childid = childid + 1

        LayoutManager.save_config()
        
    def print_pos(self, child, childid):
        if (isinstance(child, Gtk.VPaned)):
            pos = 'v'
            print ("V: %d"% child.get_position())
        elif (isinstance(child, Gtk.HPaned)):
            pos = 'h'
            print ("H: %d"% child.get_position())
        if not str(child.time) in self.paned_childs:
            self.paned_childs[str(child.time)] = (childid, pos, child.get_position())

    def print_childs(self, child, childid, first):
        if isinstance(child, Gtk.Paned):
            if (first):
                print("Child: %s"% str(child))
                self.print_pos(child, childid)
            child1 = child.get_child1()
            child2 = child.get_child2()
            if (child1 and isinstance(child1, Gtk.Paned)):
                print("child1: %s"% str(child1))
                self.print_pos(child1, childid)
                self.print_childs(child1, childid, False)
            if (child2 and isinstance(child2, Gtk.Paned)):
                print("child2: %s"% str(child2))
                self.print_pos(child2, childid)
                self.print_childs(child2, childid, False)

    def quit(self):
        global Wins

        ConfigManager.save_config()
        Wins.remove_app(self)
        self.destroy()

    def on_resize(self, widget, event):
        if Gdk.ModifierType.BUTTON1_MASK & event.get_state() != 0:
            mouse_y = event.device.get_position()[2]
            new_height = mouse_y - self.get_position()[1]
            mouse_x = event.device.get_position()[1]
            new_width = mouse_x - self.get_position()[0]
            if new_height > 0 and new_width > 0:
                self.monitor.height = new_height
                self.monitor.width = new_width
                self.resize(self.monitor.width, self.monitor.height)
                self.show()

    def update_resizer(self, widget, event):
        self.resizer.set_position(self.monitor.height)
        self.resizer.set_position(self.monitor.width)

    def add_page(self, page_name=None):
        progname = LayoutManager.get_conf(page_name, 'progname')
        if (progname and len(progname)):
            container = VteObjectContainer(progname=progname.split())
        else:
            container = VteObjectContainer()
        self.notebook.append_page(container, None)
        self.notebook.set_current_page(-1)
        self.get_active_terminal().grab_focus()

        page_count = 0
        for button in self.buttonbox:
            if button != self.radio_group_leader:
                page_count += 1

        tab_name = LayoutManager.get_conf(page_name, 'name')
        if page_name == None or tab_name == None:
            tab_name = _("Terminal ") + str(page_count+1)

        new_button = Gtk.RadioButton.new_with_label_from_widget(self.radio_group_leader, tab_name)
        setattr(new_button, 'progname', progname)
        new_button.set_property('draw-indicator', False)
        new_button.set_active(True)
        new_button.show()
        new_button.connect('toggled', self.change_page)
        new_button.connect('button-release-event', self.page_button_mouse_event)

        self.buttonbox.pack_start(new_button, False, True, 0)

        for section in LayoutManager.get_sections():
            child = str('Child-%s'%(page_name[len('Tabs-'):]))
            if (section.find(child) == 0):
                print("CHILD: %s"% section)
                val = LayoutManager.get_conf(section, "type")[0]
                print("val: %c"% val)
                container.active_terminal.split_axis(container.active_terminal, axis=val, position=LayoutManager.get_conf(section, "pos"))

    def get_active_terminal(self):
        return self.notebook.get_nth_page(self.notebook.get_current_page()).active_terminal

    def change_page(self, button):
        if button.get_active() == False:
            return

        page_no = 0
        for i in self.buttonbox:
            if i != self.radio_group_leader:
                if i == button:
                    self.notebook.set_current_page(page_no)
                    self.get_active_terminal().grab_focus()
                    return
                page_no = page_no + 1      

    def page_button_mouse_event(self, button, event):
        if event.button != 3:
            return

        self.menu = self.builder.get_object('page_button_menu')
        self.menu.connect('deactivate', lambda w: setattr(ConfigManager, 'disable_losefocus_temporary', False))

        self.menu_close = self.builder.get_object('menu_close')
        self.menu_rename = self.builder.get_object('menu_rename')

        try:
            self.menu_rename.disconnect(self.menu_rename_signal)
            self.menu_close.disconnect(self.menu_close_signal)

            self.menu_close_signal = self.menu_close.connect('activate', self.page_close, button)
            self.menu_rename_signal = self.menu_rename.connect('activate', self.page_rename, button)
        except:
            self.menu_close_signal = self.menu_close.connect('activate', self.page_close, button)
            self.menu_rename_signal = self.menu_rename.connect('activate', self.page_rename, button)

        self.menu.show_all()

        ConfigManager.disable_losefocus_temporary = True
        self.menu.popup(None, None, None, None, event.button, event.time)
        self.get_active_terminal().grab_focus()

    def page_rename(self, menu, sender):
        RenameDialog(sender, self.get_active_terminal())

    def page_close(self, menu, sender):
        button_count = len(self.buttonbox.get_children())

        # don't forget "radio_group_leader"
        if button_count <= 2:
            return self.quit()

        page_no = 0
        for i in self.buttonbox:
            if i != self.radio_group_leader:
                if i == sender:
                    self.notebook.remove_page(page_no)
                    self.buttonbox.remove(i)
                    
                    last_button = self.buttonbox.get_children()[-1]
                    last_button.set_active(True)
                    return True
                page_no = page_no + 1

    def get_screen_rectangle(self):
        display = self.screen.get_display()
        return self.screen.get_monitor_workarea(self.screen.get_monitor_at_point(self.monitor.x, self.monitor.y))

    def update_ui(self):
        self.unmaximize()
        self.stick()
        self.override_gtk_theme()
        self.set_keep_above(ConfigManager.get_conf('always-on-top'))
        self.set_decorated(ConfigManager.get_conf('use-border'))
        self.set_skip_taskbar_hint(ConfigManager.get_conf('skip-taskbar'))

        win_rect = self.monitor
        if ConfigManager.get_conf('hide-tab-bar'):
            self.tabbar.hide()
            self.tabbar.set_no_show_all(True)
        else:
            self.tabbar.set_no_show_all(False)
            self.tabbar.show()

        if self.is_fullscreen:
            win_rect = self.get_screen_rectangle()
            self.reshow_with_initial_size()
            self.move(win_rect.x, win_rect.y)
            self.fullscreen()

            # hide resizer
            if self.resizer.get_child2() != None:
                self.resizer.remove(self.resizer.get_child2())

            # hide tab bar
            if ConfigManager.get_conf('hide-tab-bar-fullscreen'):
                self.tabbar.set_no_show_all(True)
                self.tabbar.hide()
        else:
            # show resizer
            if self.resizer.get_child2() == None:
                self.resizer.add2(Gtk.Box())
                self.resizer.get_child2().show_all()
            
            # show tab bar
            if ConfigManager.get_conf('hide-tab-bar-fullscreen'):
                self.tabbar.set_no_show_all(False)
                self.tabbar.show()

            self.unfullscreen()

            self.reshow_with_initial_size()
            self.resize(win_rect.width, win_rect.height)
            self.move(win_rect.x, win_rect.y)


    def override_gtk_theme(self):
        css_provider = Gtk.CssProvider()

        bg = Gdk.color_parse(ConfigManager.get_conf('color-background'))
        bg_hex =  '#%02X%02X%02X' % (int((bg.red/65536.0)*256), int((bg.green/65536.0)*256), int((bg.blue/65536.0)*256))

        css_provider.load_from_data('''
            #notebook GtkPaned 
            {
                -GtkPaned-handle-size: %i;
            }
            GtkVScrollbar
            {
                -GtkRange-slider-width: 5;
            }
            GtkVScrollbar.trough {
                background-image: none;
                background-color: %s;
                border-width: 0;
                border-radius: 0;

            }
            GtkVScrollbar.slider, GtkVScrollbar.slider:prelight, GtkVScrollbar.button {
                background-image: none;
                border-width: 0;
                background-color: alpha(#FFF, 0.4);
                border-radius: 10px;
                box-shadow: none;
            }
            ''' % (ConfigManager.get_conf('seperator-size'), bg_hex))

        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(self.screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def on_keypress(self, widget, event):
        if ConfigManager.key_event_compare('toggle-scrollbars-key', event):
            ConfigManager.set_conf('show-scrollbar', not ConfigManager.get_conf('show-scrollbar'))
            ConfigManager.save_config()
            ConfigManager.callback()
            return True

        if ConfigManager.key_event_compare('move-up-key', event):
            self.get_active_terminal().move(direction=1)
            return True

        if ConfigManager.key_event_compare('move-down-key', event):
            self.get_active_terminal().move(direction=2)
            return True

        if ConfigManager.key_event_compare('move-left-key', event):
            self.get_active_terminal().move(direction=3)
            return True

        if ConfigManager.key_event_compare('move-right-key', event):
            self.get_active_terminal().move(direction=4)
            return True

        if ConfigManager.key_event_compare('quit-key', event):
            self.quit()
            return True

        if ConfigManager.key_event_compare('select-all-key', event):
            self.get_active_terminal().select_all()
            return True

        if ConfigManager.key_event_compare('copy-key', event):
            self.get_active_terminal().copy_clipboard()
            return True

        if ConfigManager.key_event_compare('paste-key', event):
            self.get_active_terminal().paste_clipboard()
            return True

        if ConfigManager.key_event_compare('split-v-key', event):
            self.get_active_terminal().split_axis(None, 'v')
            return True

        if ConfigManager.key_event_compare('split-h-key', event):
            self.get_active_terminal().split_axis(None, 'h')
            return True

        if ConfigManager.key_event_compare('close-node-key', event):
            self.get_active_terminal().close_node(None)
            return True

        if ConfigManager.key_event_compare('fullscreen-key', event):
            self.toggle_fullscreen()
            return True

        if ConfigManager.key_event_compare('new-page-key', event):
            self.add_page()
            return True

        if ConfigManager.key_event_compare('rename-page-key', event):
            for button in self.buttonbox:
                if button != self.radio_group_leader and button.get_active():
                    self.page_rename(None, button)
                    return True

        if ConfigManager.key_event_compare('close-page-key', event):
            for button in self.buttonbox:
                if button != self.radio_group_leader and button.get_active():
                    self.page_close(None, button)
                    return True

        if ConfigManager.key_event_compare('next-page-key', event):
            page_button_list = self.buttonbox.get_children()[1:]

            for i in range(len(page_button_list)):
                if (page_button_list[i].get_active() == True):
                    if (i + 1 < len(page_button_list)):
                        page_button_list[i+1].set_active(True)
                    else:
                        page_button_list[0].set_active(True)
                    return True


        if ConfigManager.key_event_compare('prev-page-key', event):
            page_button_list = self.buttonbox.get_children()[1:]

            for i in range(len(page_button_list)):
                if page_button_list[i].get_active():
                    if i > 0:
                        page_button_list[i-1].set_active(True)
                    else:
                        page_button_list[-1].set_active(True)
                    return True

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        self.update_ui()

    def init_transparency(self):
        self.set_app_paintable(True)
        visual = self.screen.get_rgba_visual()
        if visual != None and self.screen.is_composited():
            self.set_visual(visual)
        else:
            ConfigManager.use_fake_transparency = True

    def update_events(self):
        while Gtk.events_pending():
            Gtk.main_iteration()
        Gdk.flush()

    def slide_up(self, i=0):
        self.slide_effect_running = True
        step = ConfigManager.get_conf('step-count')
        if not self.is_fullscreen:
            win_rect = self.monitor
        else:
            win_rect = self.get_allocation()
        if self.get_window() != None:
            self.get_window().enable_synchronized_configure()
        if i < step+1:
            self.resize(win_rect.width, win_rect.height - int(((win_rect.height/step) * i)))
            self.queue_resize()
            self.update_events()
            GObject.timeout_add(ConfigManager.get_conf('step-time'), self.slide_up, i+1)
        else:
            self.hide()
            self.unrealize()
        if self.get_window() != None:
            self.get_window().configure_finished()
        self.slide_effect_running = False

    def slide_down(self, i=1):
        step = ConfigManager.get_conf('step-count')
        self.slide_effect_running = True
        if not self.is_fullscreen:
            win_rect = self.monitor
        else:
            win_rect = self.get_screen_rectangle()
        if self.get_window() != None:
            self.get_window().enable_synchronized_configure()
        if i < step + 1:
            self.resize(win_rect.width, int(((win_rect.height/step) * i)))
            self.queue_resize()
            self.resizer.set_property('position', int(((win_rect.height/step) * i)))
            self.resizer.queue_resize()
            self.update_events()
            GObject.timeout_add(ConfigManager.get_conf('step-time'), self.slide_down, i+1)
        if self.get_window() != None:
            self.get_window().configure_finished()
        self.slide_effect_running = False

    def show_hide(self):
        if self.slide_effect_running:
            return
        event_time = self.hotkey.get_current_event_time()
        if(self.losefocus_time and self.losefocus_time >= event_time):
            return

        if self.get_visible():
            if ConfigManager.get_conf('use-animation'):
                self.slide_up()
            else:
                self.hide()
            return
        else:
            self.update_ui()
            self.show()
            x11_win = self.get_window()
            x11_time = GdkX11.x11_get_server_time(x11_win)
            x11_win.focus(x11_time)
            if ConfigManager.get_conf('use-animation'):
                self.slide_down()


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

def quit_prog():
   global Wins

   Wins.app_quit()

def save_conf():
    global Wins

    Wins.save_conf()

def create_app():
    global Wins

    Wins.create_app()

class TerminalWinContainer():
    def __init__(self):
        globalhotkeys.init()
        self.hotkey = globalhotkeys.GlobalHotkey()
        self.bind_success = self.hotkey.bind(ConfigManager.get_conf('global-key'), lambda w: self.show_hide(), None)
        self.apps = []
        self.old_apps = []
        self.screenid = 0
        self.on_doing = False

    def show_hide(self):
        if self.on_doing == False:
            self.on_doing = True
            for app in self.apps:
                app.show_hide()
            self.on_doing = False

    def update_ui(self):
        if self.on_doing == False:
            self.on_doing = True
            for app in self.apps:
                app.update_ui()
            self.on_doing = False

    def get_screen_name(self):
        return (str("screen-%d"% self.screenid))

    def save_conf(self):
        for app in self.apps:
            app.save_conf()
        for app in self.old_apps:
            app.save_conf(False)

    def app_quit(self):
        for app in self.apps:
            if (app.quit() == False):
                return
        sys.stdout.flush()
        sys.stderr.flush()
        Gtk.main_quit()

    def remove_app(self, ext):
        if ext in self.apps:
            self.apps.remove(ext)
        self.old_apps.append(ext)
        if (len(self.apps) == 0):
            self.app_quit()

    def create_app(self, screenName='DEFAULT'):
        monitor = get_screen(screenName)
        if (screenName == 'DEFAULT'):
            screenName = self.get_screen_name()
        if (monitor != None):
            app = TerminalWin(screenName, monitor)
            if (not self.bind_success):
                cannot_bind(app)
            app.hotkey = self.hotkey
            if (len(self.apps) == 0):
                DbusService(app)
            self.apps.append(app)
            self.screenid = max(self.screenid, int(screenName.split('-')[1])) + 1
        else:
            print("Cannot find %s"% screenName)

    def get_apps(self):
        return (self.apps)

def main():
    global Wins

    Wins = TerminalWinContainer()

    toto = ConfigParser.SafeConfigParser({})
    toto.read('~/.config/terra/layout.cfg')
    toto.sections()

    for section in LayoutManager.get_sections():
        if (section.find("screen-") == 0 and (LayoutManager.get_conf(section, 'enabled'))):
            Wins.create_app(section)
    if (len(Wins.get_apps()) == 0):
        Wins.create_app()
    if (len(Wins.get_apps()) == 0):
        print("Cannot initiate any screen")
        return
    Gtk.main()

if __name__ == "__main__":
    main()
