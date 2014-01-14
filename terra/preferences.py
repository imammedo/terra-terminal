#!/usr/bin/python
# -*- coding: utf-8; -*-
"""
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

from gi.repository import Gtk, Gdk, GdkPixbuf, GObject, GdkX11
from config import ConfigManager
from i18n import _
import os

class Preferences():

    def __init__(self):
        
        self.init_ui()

    def init_ui(self):
        builder = Gtk.Builder()
        builder.set_translation_domain('terra')
        builder.add_from_file(ConfigManager.data_dir + 'ui/preferences.ui')

        self.window = builder.get_object('preferences_window')
        self.window.connect('destroy', self.on_cancel_clicked)

        self.logo = builder.get_object('terra_logo')
        self.logo_buffer = GdkPixbuf.Pixbuf.new_from_file_at_size(ConfigManager.data_dir + 'image/terra.svg', 64, 64)
        self.logo.set_from_pixbuf(self.logo_buffer)

        self.version = builder.get_object('version')
        self.version.set_label(_("Version: ") + ConfigManager.version)

        self.btn_cancel = builder.get_object('btn_cancel')
        self.btn_cancel.connect('clicked', self.on_cancel_clicked)

        self.btn_apply = builder.get_object('btn_apply')
        self.btn_apply.connect('clicked', self.on_apply_clicked)

        self.btn_ok = builder.get_object('btn_ok')
        self.btn_ok.connect('clicked', self.on_ok_clicked)

        self.adj_seperator = builder.get_object('adjustment_seperator')
        self.adj_seperator.set_value(int(ConfigManager.get_conf('seperator-size')) * 1.0)

        self.adj_transparency = builder.get_object('adjustment_transparency')
        self.adj_transparency.set_value(int(ConfigManager.get_conf('transparency')) * 1.0)

        self.chk_hide_from_taskbar = builder.get_object('chk_hide_from_taskbar')
        self.chk_hide_from_taskbar.set_active(ConfigManager.get_conf('skip-taskbar'))

        self.chk_use_border = builder.get_object('chk_use_border')
        self.chk_use_border.set_active(ConfigManager.get_conf('use-border'))

        self.color_text = builder.get_object('color_text')
        self.color_text.set_color(Gdk.color_parse(ConfigManager.get_conf('color-text')))

        self.color_background = builder.get_object('color_background')
        self.color_background.set_color(Gdk.color_parse(ConfigManager.get_conf('color-background')))

        self.entry_shell = builder.get_object('entry_shell')
        self.entry_shell.set_text(ConfigManager.get_conf('shell'))

        self.entry_select_by_word = builder.get_object('entry_select_by_word')
        self.entry_select_by_word.set_text(ConfigManager.get_conf('select-by-word'))

        self.dir_custom = builder.get_object('dir_custom')

        self.radio_home = builder.get_object('radio_home')
        self.radio_pwd = builder.get_object('radio_pwd')
        self.radio_dir_custom = builder.get_object('radio_dir_custom')
        self.radio_dir_custom.connect('toggled', lambda w: self.toggle_sensitive(self.radio_dir_custom, [self.dir_custom]))

        dir_conf = ConfigManager.get_conf('dir')
        if dir_conf == '$home$':
            self.radio_home.set_active(True)
        elif dir_conf == '$pwd$':
            self.radio_pwd.set_active(True)
        else:
            self.radio_dir_custom.set_active(True)
            self.dir_custom.set_text(dir_conf)
            self.dir_custom.set_sensitive(True)

        self.background_image = builder.get_object('background_image')
        self.background_image.set_filename(ConfigManager.get_conf('background-image'))

        self.clear_background_image = builder.get_object('clear_background_image')
        self.clear_background_image.connect('clicked', lambda w: self.background_image.unselect_all())

        self.font_name = builder.get_object('font_name')
        self.font_name.set_font_name(ConfigManager.get_conf('font-name'))
        self.font_name.set_sensitive(not ConfigManager.get_conf('use-default-font'))

        self.chk_use_system_font = builder.get_object('chk_use_system_font')
        self.chk_use_system_font.connect('toggled', lambda w: self.toggle_sensitive(self.chk_use_system_font, [self.font_name]))
        self.chk_use_system_font.set_active(ConfigManager.get_conf('use-default-font'))

        self.chk_show_scrollbar = builder.get_object('chk_show_scrollbar')
        self.chk_show_scrollbar.set_active(ConfigManager.get_conf('show-scrollbar'))

        self.chk_always_on_top = builder.get_object('chk_always_on_top')
        self.chk_always_on_top.set_active(ConfigManager.get_conf('always-on-top'))

        self.chk_losefocus = builder.get_object('chk_losefocus')
        self.chk_losefocus.set_active(ConfigManager.get_conf('losefocus-hiding'))

        self.chk_hide_on_start = builder.get_object('chk_hide_on_start')
        self.chk_hide_on_start.set_active(ConfigManager.get_conf('hide-on-start'))

        # store all keyboard shortcut entry boxes in array for connecting signals together.
        key_entries = []

        self.fullscreen_key = builder.get_object('fullscreen_key')
        self.fullscreen_key.set_text(ConfigManager.get_conf('fullscreen-key'))
        key_entries.append(self.fullscreen_key)

        self.quit_key = builder.get_object('quit_key')
        self.quit_key.set_text(ConfigManager.get_conf('quit-key'))
        key_entries.append(self.quit_key)

        self.new_page_key = builder.get_object('new_page_key')
        self.new_page_key.set_text(ConfigManager.get_conf('new-page-key'))
        key_entries.append(self.new_page_key)

        self.close_page_key = builder.get_object('close_page_key')
        self.close_page_key.set_text(ConfigManager.get_conf('close-page-key'))
        key_entries.append(self.close_page_key)

        self.rename_page_key = builder.get_object('rename_page_key')
        self.rename_page_key.set_text(ConfigManager.get_conf('rename-page-key'))
        key_entries.append(self.rename_page_key)

        self.next_page_key = builder.get_object('next_page_key')
        self.next_page_key.set_text(ConfigManager.get_conf('next-page-key'))
        key_entries.append(self.next_page_key)

        self.prev_page_key = builder.get_object('prev_page_key')
        self.prev_page_key.set_text(ConfigManager.get_conf('prev-page-key'))
        key_entries.append(self.prev_page_key)

        self.move_page_left = builder.get_object('move_page_left')
        self.move_page_left.set_text(ConfigManager.get_conf('move-page-left'))
        key_entries.append(self.move_page_left)

        self.move_page_right = builder.get_object('move_page_right')
        self.move_page_right.set_text(ConfigManager.get_conf('move-page-right'))
        key_entries.append(self.move_page_right)

        self.global_key = builder.get_object('global_key')
        self.global_key.set_text(ConfigManager.get_conf('global-key'))
        key_entries.append(self.global_key)

        self.select_all_key = builder.get_object('select_all_key')
        self.select_all_key.set_text(ConfigManager.get_conf('select-all-key'))
        key_entries.append(self.select_all_key)

        self.copy_key = builder.get_object('copy_key')
        self.copy_key.set_text(ConfigManager.get_conf('copy-key'))
        key_entries.append(self.copy_key)

        self.paste_key = builder.get_object('paste_key')
        self.paste_key.set_text(ConfigManager.get_conf('paste-key'))
        key_entries.append(self.paste_key)

        self.split_v_key = builder.get_object('split_v_key')
        self.split_v_key.set_text(ConfigManager.get_conf('split-v-key'))
        key_entries.append(self.split_v_key)

        self.split_h_key = builder.get_object('split_h_key')
        self.split_h_key.set_text(ConfigManager.get_conf('split-h-key'))
        key_entries.append(self.split_h_key)

        self.close_node_key = builder.get_object('close_node_key')
        self.close_node_key.set_text(ConfigManager.get_conf('close-node-key'))
        key_entries.append(self.close_node_key)

        self.move_up_key = builder.get_object('move_up_key')
        self.move_up_key.set_text(ConfigManager.get_conf('move-up-key'))
        key_entries.append(self.move_up_key)

        self.move_down_key = builder.get_object('move_down_key')
        self.move_down_key.set_text(ConfigManager.get_conf('move-down-key'))
        key_entries.append(self.move_down_key)

        self.restore_defaults = builder.get_object('restore_defaults')
        self.restore_defaults.connect('clicked', lambda w: self.restore_defaults_cb())
        
        self.move_left_key = builder.get_object('move_left_key')
        self.move_left_key.set_text(ConfigManager.get_conf('move-left-key'))
        key_entries.append(self.move_left_key)

        self.move_right_key = builder.get_object('move_right_key')
        self.move_right_key.set_text(ConfigManager.get_conf('move-right-key'))
        key_entries.append(self.move_right_key)

        self.move_left_screen_key = builder.get_object('move_left_screen_key')
        self.move_left_screen_key.set_text(ConfigManager.get_conf('move-left-screen-key'))
        key_entries.append(self.move_left_screen_key)

        self.move_right_screen_key = builder.get_object('move_right_screen_key')
        self.move_right_screen_key.set_text(ConfigManager.get_conf('move-right-screen-key'))
        key_entries.append(self.move_right_screen_key)

        self.toggle_scrollbars_key = builder.get_object('toggle_scrollbars_key')
        self.toggle_scrollbars_key.set_text(ConfigManager.get_conf('toggle-scrollbars-key'))
        key_entries.append(self.toggle_scrollbars_key)

        self.chk_run_on_startup = builder.get_object('chk_run_on_startup')
        self.chk_run_on_startup.set_active(os.path.exists(os.environ['HOME'] + '/.config/autostart/terra.desktop'))

        self.open_translation_page = builder.get_object('open_translation_page')
        self.open_translation_page.connect('clicked', lambda w: Gtk.show_uri(self.window.get_screen(), 'https://translations.launchpad.net/terra', GdkX11.x11_get_server_time(self.window.get_window())))

        self.report_bug = builder.get_object('report_bug')
        self.report_bug.connect('clicked', lambda w: Gtk.show_uri(self.window.get_screen(), 'https://github.com/Sixdsn/terra-terminal/issues', GdkX11.x11_get_server_time(self.window.get_window())))

        self.webpage = builder.get_object('webpage')
        self.webpage.connect('clicked', lambda w: Gtk.show_uri(self.window.get_screen(), 'http://terraterminal.org', GdkX11.x11_get_server_time(self.window.get_window())))

        self.entry_scrollback_lines = builder.get_object('entry_scrollback_lines')
        self.entry_scrollback_lines.set_text(str(ConfigManager.get_conf('scrollback-lines')))

        self.chk_scrollback_unlimited = builder.get_object('chk_scrollback_unlimited')
        self.chk_scrollback_unlimited.connect('toggled', lambda w: self.toggle_sensitive(self.chk_scrollback_unlimited, [self.entry_scrollback_lines]))
        self.chk_scrollback_unlimited.set_active(ConfigManager.get_conf('infinite-scrollback'))

        self.chk_scroll_on_output = builder.get_object('chk_scroll_on_output')
        self.chk_scroll_on_output.set_active(ConfigManager.get_conf('scroll-on-output'))

        self.chk_scroll_on_keystroke = builder.get_object('chk_scroll_on_keystroke')
        self.chk_scroll_on_keystroke.set_active(ConfigManager.get_conf('scroll-on-keystroke'))
        
        self.chk_hide_tab_bar = builder.get_object('chk_hide_tab_bar')
        self.chk_hide_tab_bar.set_active(ConfigManager.get_conf('hide-tab-bar'))
        
        self.chk_hide_tab_bar_fullscreen = builder.get_object('chk_hide_tab_bar_fullscreen')
        self.chk_hide_tab_bar_fullscreen.set_active(ConfigManager.get_conf('hide-tab-bar-fullscreen'))

        self.chk_prompt_on_quit = builder.get_object('chk_prompt_on_quit')
        self.chk_prompt_on_quit.set_active(ConfigManager.get_conf('prompt-on-quit'))

        self.spawn_term_on_last_close = builder.get_object('spawn-term-on-last-close')
        self.spawn_term_on_last_close.set_active(ConfigManager.get_conf('spawn-term-on-last-close'))

        self.entry_step_count = builder.get_object('entry_step_count')
        self.entry_step_count.set_text(str(ConfigManager.get_conf('step-count')))

        self.entry_step_time = builder.get_object('entry_step_time')
        self.entry_step_time.set_text(str(ConfigManager.get_conf('step-time')))

        self.chk_use_animation = builder.get_object('chk_use_animation')
        self.chk_use_animation.set_active(ConfigManager.get_conf('use-animation'))
        self.chk_use_animation.connect('toggled', lambda w: self.toggle_sensitive(self.chk_use_animation, [self.entry_step_time, self.entry_step_count]))

        for key_entry in key_entries:
            key_entry.connect('button-press-event', self.clear_key_entry)
            key_entry.connect('key-press-event', self.generate_key_string)

    def clear_key_entry(self, widget, event):
        if event.type == Gdk.EventType._2BUTTON_PRESS:
            widget.set_text("")

    def toggle_sensitive(self, source_object, target_objects):
        for target_object in target_objects:
            target_object.set_sensitive(not source_object.get_active())

    def restore_defaults_cb(self):
        self.global_key.set_text('F12')
        self.quit_key.set_text('<Control>q')
        self.fullscreen_key.set_text('F11')
        self.new_page_key.set_text('<Control>N')
        self.rename_page_key.set_text('F2')
        self.close_page_key.set_text('<Control>W')
        self.next_page_key.set_text('<Control>Right')
        self.prev_page_key.set_text('<Control>Left')
        self.select_all_key.set_text('<Control>A')
        self.copy_key.set_text('<Control><Shift>C')
        self.paste_key.set_text('<Control><Shift>V')
        self.split_v_key.set_text('<Control><Shift>J')
        self.split_h_key.set_text('<Control><Shift>H')
        self.close_node_key.set_text('<Control><Shift>K')
        self.move_up_key.set_text('<Control><Shift>Up')
        self.move_down_key.set_text('<Control><Shift>Down')
        self.move_left_key.set_text('<Control><Shift>Left')
        self.move_right_key.set_text('<Control><Shift>Right')
        self.toggle_scrollbars_key.set_text('<Control><Shift>S')


    def generate_key_string(self, widget, event):
        key_str = ''

        if ((Gdk.ModifierType.CONTROL_MASK & event.state) == Gdk.ModifierType.CONTROL_MASK):
            key_str = key_str + '<Control>'

        if ((Gdk.ModifierType.MOD1_MASK & event.state) == Gdk.ModifierType.MOD1_MASK):
            key_str = key_str + '<Alt>'

        if ((Gdk.ModifierType.SHIFT_MASK & event.state) == Gdk.ModifierType.SHIFT_MASK):
            key_str = key_str + '<Shift>'

        if ((Gdk.ModifierType.SUPER_MASK & event.state) == Gdk.ModifierType.SUPER_MASK):
            key_str = key_str + '<Super>'

        key_str = key_str + Gdk.keyval_name(event.keyval)

        widget.set_text(key_str)

    def show(self):
        self.window.show_all()

    def on_apply_clicked(self, widget):
        ConfigManager.set_conf('seperator-size', int(self.adj_seperator.get_value()))

        ConfigManager.set_conf('transparency', int(self.adj_transparency.get_value()))

        ConfigManager.set_conf('skip-taskbar', self.chk_hide_from_taskbar.get_active())

        ConfigManager.set_conf('use-border', self.chk_use_border.get_active())

        ConfigManager.set_conf('color-text', self.color_text.get_color().to_string())

        ConfigManager.set_conf('color-background', self.color_background.get_color().to_string())

        ConfigManager.set_conf('shell', self.entry_shell.get_text())

        ConfigManager.set_conf('select-by-word', self.entry_select_by_word.get_text())

        if self.radio_home.get_active():
            ConfigManager.set_conf('dir', '$home$')
        elif self.radio_pwd.get_active():
            ConfigManager.set_conf('dir', '$pwd$')
        else:
            ConfigManager.set_conf('dir', self.dir_custom.get_text())

        ConfigManager.set_conf('background-image', self.background_image.get_filename())

        ConfigManager.set_conf('use-default-font', self.chk_use_system_font.get_active())

        ConfigManager.set_conf('font-name', self.font_name.get_font_name())

        ConfigManager.set_conf('show-scrollbar', self.chk_show_scrollbar.get_active())

        ConfigManager.set_conf('always-on-top', self.chk_always_on_top.get_active())

        ConfigManager.set_conf('losefocus-hiding', self.chk_losefocus.get_active())

        ConfigManager.set_conf('hide-on-start', self.chk_hide_on_start.get_active())

        ConfigManager.set_conf('fullscreen-key', self.fullscreen_key.get_text())

        ConfigManager.set_conf('quit-key', self.quit_key.get_text())

        ConfigManager.set_conf('new-page-key', self.new_page_key.get_text())

        ConfigManager.set_conf('close-page-key', self.close_page_key.get_text())

        ConfigManager.set_conf('rename-page-key', self.rename_page_key.get_text())

        ConfigManager.set_conf('next-page-key', self.next_page_key.get_text())

        ConfigManager.set_conf('prev-page-key', self.prev_page_key.get_text())

        ConfigManager.set_conf('global-key', self.global_key.get_text())

        ConfigManager.set_conf('select-all-key', self.select_all_key.get_text())

        ConfigManager.set_conf('copy-key', self.copy_key.get_text())

        ConfigManager.set_conf('paste-key', self.paste_key.get_text())

        ConfigManager.set_conf('split-h-key', self.split_h_key.get_text())

        ConfigManager.set_conf('split-v-key', self.split_v_key.get_text())

        ConfigManager.set_conf('close-node-key', self.close_node_key.get_text())
    
        ConfigManager.set_conf('move-up-key', self.move_up_key.get_text())

        ConfigManager.set_conf('move-down-key', self.move_down_key.get_text())

        ConfigManager.set_conf('move-left-key', self.move_left_key.get_text())

        ConfigManager.set_conf('move-right-key', self.move_right_key.get_text())

        ConfigManager.set_conf('toggle-scrollbars-key', self.toggle_scrollbars_key.get_text())

        try:
            scrollback_line = int(self.entry_scrollback_lines.get_text())
        except ValueError:
            scrollback_line = 1024

        ConfigManager.set_conf('scrollback-lines', str(scrollback_line))

        ConfigManager.set_conf('scroll-on-output', self.chk_scroll_on_output.get_active())

        ConfigManager.set_conf('scroll-on-keystroke', self.chk_scroll_on_keystroke.get_active())

        ConfigManager.set_conf('infinite-scrollback', self.chk_scrollback_unlimited.get_active())

        ConfigManager.set_conf('hide-tab-bar', self.chk_hide_tab_bar.get_active())

        ConfigManager.set_conf('hide-tab-bar-fullscreen', self.chk_hide_tab_bar_fullscreen.get_active())
        
        ConfigManager.set_conf('prompt-on-quit', self.chk_prompt_on_quit.get_active())

        ConfigManager.set_conf('spawn-term-on-last-close', self.spawn_term_on_last_close.get_active())

        try:
            step_time = int(self.entry_step_time.get_text())
            if not step_time > 0:
                step_time = 20
        except ValueError:
            step_time = 20

        try:
            step_count = int(self.entry_step_count.get_text())
            if not step_count > 0:
                step_count = 20
        except ValueError:
            step_count = 20

        ConfigManager.set_conf('use-animation', self.chk_use_animation.get_active())

        ConfigManager.set_conf('step-count', step_count)
        ConfigManager.set_conf('step-time', step_time)



        if (self.chk_run_on_startup.get_active() and not os.path.exists(os.environ['HOME'] + '/.config/autostart/terra.desktop')):
            os.system('cp /usr/share/applications/terra.desktop ' + os.environ['HOME'] + '/.config/autostart/terra.desktop')

        if (not self.chk_run_on_startup.get_active() and os.path.exists(os.environ['HOME'] + '/.config/autostart/terra.desktop')):
            os.system('rm -f ' + os.environ['HOME'] + '/.config/autostart/terra.desktop')

        ConfigManager.save_config()
        ConfigManager.callback()

    def on_ok_clicked(self, widget):
        self.on_apply_clicked(self.btn_ok)
        self.window.hide()
        ConfigManager.disable_losefocus_temporary = False

    def on_cancel_clicked(self, widget):
        self.window.hide()
        ConfigManager.disable_losefocus_temporary = False
