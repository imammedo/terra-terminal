#!/usr/bin/env python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# Copyright (C) 2012 Ozcan ESEN <ozcanesen@gmail.com>
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE

import os
import sys
import glob
import subprocess
import shutil

try:
    import DistUtilsExtra.auto
    from distutils.extension import Extension
except ImportError:
    sys.stderr.write('To build terra you need https://launchpad.net/python-distutils-extra\n')
    sys.exit(1)
assert DistUtilsExtra.auto.__version__ >= '2.18', 'needs DistUtilsExtra.auto >= 2.18'

PO_DIR = 'po'
MO_DIR = os.path.join('build', 'mo')

def update_config(file_orig, values = {}):

    oldvalues = {}
    try:
        fin = open(file_orig, 'r')
        fout = open(fin.name + '.new', 'w')

        for line in fin:
            fields = line.split(' = ') # Separate variable from value
            if fields[0] in values:
                oldvalues[fields[0]] = fields[1].strip()
                line = "%s = %s\n" % (fields[0], values[fields[0]])
            fout.write(line)

        fout.flush()
        fout.close()
        fin.close()
        os.rename(fout.name, fin.name)
    except (OSError, IOError) as e:
        print ("ERROR: Can't find %s"% (file_orig))
        sys.exit(1)
    return oldvalues

def update_desktop_file(datadir):

    try:
        fin = open('terra.desktop.in', 'r')
        fout = open(fin.name + '.new', 'w')

        for line in fin:
            if 'Icon=' in line:
                line = "Icon=%s\n" % (datadir + 'image/terra.svg')
            fout.write(line)
        fout.flush()
        fout.close()
        fin.close()
        os.rename(fout.name, fin.name)
    except (OSError, IOError) as e:
        print ("ERROR: Can't find terra.desktop.in")
        sys.exit(1)

def move_data_files(datadir, bindir):
    if os.path.exists(datadir):
        shutil.rmtree(datadir)
    shutil.copytree('data/', datadir)
    shutil.copyfile('main/terra', bindir + 'terra')

class InstallAndUpdateDataDirectory(DistUtilsExtra.auto.install_auto):
    def run(self):
        values = {'__terra_data_directory__': "'%s'" % (self.prefix + '/share/terra/'),
                  '__version__': "'%s'" % self.distribution.get_version()}
        previous_values = update_config('terra/config.py', values)
        update_desktop_file(self.prefix + '/share/terra/')
        DistUtilsExtra.auto.install_auto.run(self)
        update_config('terra/config.py', previous_values)
        move_data_files(self.prefix + '/share/terra/', self.prefix + '/bin/')
        for po in glob.glob (os.path.join (PO_DIR, '*.po')):
            lang = os.path.basename(po[:-3])
            mo = os.path.join(MO_DIR, lang, 'terra.mo')

            directory = os.path.dirname(mo)
            if not os.path.exists(directory):
                os.makedirs(directory)
            try:
                rc = subprocess.call(['msgfmt', '-o', mo, po])
                if rc != 0:
                    raise (Warning, "msgfmt returned %d" % rc)
            except Exception as e:
                print(e)
                sys.exit(1)

def parse_pkg_config(command, components, options_dict=None):
    if options_dict is None:
        options_dict = {
            'include_dirs': [],
            'library_dirs': [],
            'libraries': [],
            'extra_compile_args': []
        }
    commandLine = "%s --cflags --libs %s" % (command, components)
    output = get_command_output(commandLine).strip()
    for comp in output.split():
        prefix, rest = comp[:2], comp[2:]
        if prefix == '-I':
            options_dict['include_dirs'].append(rest)
        elif prefix == '-L':
            options_dict['library_dirs'].append(rest)
        elif prefix == '-l':
            options_dict['libraries'].append(rest)
        else:
            options_dict['extra_compile_args'].append(comp)

    commandLine = "%s --variable=libdir %s" % (command, components)
    output = get_command_output(commandLine).strip()

    return options_dict

def get_command_output(cmd, warnOnStderr=True, warnOnReturnCode=True):
    """Wait for a command and return its output.  Check for common
    errors and raise an exception if one of these occurs.
    """
    p = subprocess.Popen(cmd, shell=True, close_fds=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = p.communicate()
    stdout = output[0].decode(encoding='UTF-8')
    stderr = output[1].decode(encoding='UTF-8')
    if warnOnStderr and stderr != '':
        raise RuntimeError("%s outputted the following error:\n%s" %
                           (cmd, stderr))
    if warnOnReturnCode and p.returncode != 0:
        raise RuntimeError("%s had non-zero return code %d" %
                           (cmd, p.returncode))
    return stdout

gtk_config = parse_pkg_config('pkg-config','gtk+-3.0')
globalhotkeys = Extension("terra.globalhotkeys", ['terra/globalhotkeys/globalhotkeys.c', 'terra/globalhotkeys/bind.c'], **gtk_config)

DistUtilsExtra.auto.setup(
    name='terra',
    version='0.2.0',
    license='GPL-3',
    author='Arnaud Sourioux',
    author_email='six.dsn@gmail.com',
    description='Terra Terminal Emulator',
    long_description='''Terra is GTK+3.0 based terminal emulator with useful user interface, it also supports multiple terminals with splitting screen horizontally or vertically. New features will be added soon. It's very new and experimental project. It's written in python with python-gobject, If you want to contribute just checkout and try. Feel free to open issues for bug report or new features.''',
    url='https://github.com/Sixdsn/terra-terminal',
    cmdclass={'install': InstallAndUpdateDataDirectory},
    ext_modules=[globalhotkeys]
    )

