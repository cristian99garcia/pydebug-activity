# Copyright (C) 2006, Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os, sys
from gettext import gettext as _
from subprocess import Popen, PIPE
import shutil

from gi.repository import Gtk
from gi.repository import WebKit
from gi.repository import GObject

#from time import time
from sugar3 import util

from jarabe.model import shell

from sugar3.activity import activity
from sugar3.graphics.window import Window
from sugar3.graphics.toolbox import Toolbox
from sugar3.activity.activityhandle import ActivityHandle
from sugar3 import wm, env
#from IPython.Debugger import Tracer
from pdb import *
from sugar3.graphics.toolbutton import ToolButton

GObject.threads_init()

HOME = os.path.join(activity.get_bundle_path(), _('help/PyDebug.htm'))
HELP_PANE = 3

# Initialize logging.
import logging
_logger = logging.getLogger('PyDebug')


class Help(Window):

    def __init__(self, parent):

        self.pydebug = parent
        #from hulahop.webview import WebView
        from browser import Browser

        self.help_id = None
        self.handle = ActivityHandle()
        self.handle.activity_id = util.unique_id()
        Window.__init__(self)
        self.connect('realize',self.realize_cb)

        self.props.max_participants = 1

        self._web_view = Browser()

        ##self.toolbox = Toolbox()
        ##self.toolbox.connect('current_toolbar_changed',self.goto_cb)
        ##self.set_toolbox(self.toolbox)
        ##self.toolbox.show()

        activitybar = Gtk.Toolbar()
        ##self.toolbox.add_toolbar(_('Activity'), activitybar)
        activitybar.show_all()

        editbar = Gtk.Toolbar()
        ##self.toolbox.add_toolbar(_('Edit'), editbar)
        #editbar.connect('current_toolbar_changed', self.goto_cb,1)
        editbar.show_all()

        projectbar = Gtk.Toolbar()
        ##self.toolbox.add_toolbar(_('Project'), projectbar)
        #projectbar.connect('current_toolbar_changed', self.goto_cb,2)
        projectbar.show_all()

        self.help_toolbar = Toolbar(self._web_view)
        self.help_toolbar.show()
        ##self.toolbox.add_toolbar(_('Help'), self.help_toolbar)
        ##self.toolbox._notebook.set_current_page(HELP_PANE)

        self.set_canvas(self._web_view)
        self._web_view.show()

        self.toolbox.set_current_toolbar(HELP_PANE)

        self._web_view.load_uri(HOME)
        self.pid = Popen(['/usr/bin/pydoc', '-p', '23432'])

    def get_help_toolbar(self):
        return self.help_toolbar

    def realize_help(self):
        _logger.debug('realize help called Version: %s pydebug activity id:%s' % (version, self.pydebug.handle.activity_id))
        self.pywin = self.get_wnck_window_from_activity_id(str(self.pydebug.handle.activity_id))
        if self.pywin:
            self.pywin.activate(gtk.get_current_event_time())
            _logger.debug('pywin.activate called')

        self.show_all()
        self.toolbox._notebook.set_current_page(HELP_PANE)
        return self
    
    def realize_cb(self, window):
        self.help_id = util.unique_id()
        wm.set_activity_id(window.window, self.help_id)
        self.help_window = window
            
    def activate_help(self):
        _logger.debug('activate_help called')
        self.help_window.show()
        window = self.get_wnck_window_from_activity_id(self.help_id)
        self.toolbox._notebook.set_current_page(HELP_PANE)

        if window:
            window.activate(gtk.get_current_event_time())
        else:
            _logger.debug('failed to get window')
            
    def goto_cb(self, page, tab):
        _logger.debug('current_toolbar_changed event called goto_cb. tab: %s'%tab)
        if tab == HELP_PANE:
            return

        if not self.help_id:
            return

        self.pydebug.set_toolbar(tab)
        self.help_window.hide()
        self.pywin = self.get_wnck_window_from_activity_id(str(self.pydebug.handle.activity_id))
        if self.pywin:
            self.pywin.activate(gtk.get_current_event_time())

    def get_wnck_window_from_activity_id(self, activity_id):
        """Use shell model to look up the wmck window associated with activity_id
           --the home_model code changed between .82 and .84 sugar
           --so do the lookup differently depending on sugar version
        """
        _logger.debug('get_wnck_window_from_activity_id. id:%s' % activity_id)
        _logger.debug('sugar version %s' % version)
        home_model = shell.get_model()
        activity = home_model.get_activity_by_id(activity_id)
        if activity:
            return activity.get_window()

        else:
            _logger.debug('wnck_window was none')
            return None


class Toolbar(Gtk.Toolbar):

    def __init__(self, web_view):
        GObject.GObject.__init__(self)

        self._web_view = web_view

        self._back = ToolButton('go-previous-paired')
        self._back.set_tooltip(_('Back'))
        self._back.props.sensitive = False
        self._back.connect('clicked', self._go_back_cb)
        self.insert(self._back, -1)
        self._back.show()

        self._forward = ToolButton('go-next-paired')
        self._forward.set_tooltip(_('Forward'))
        self._forward.props.sensitive = False
        self._forward.connect('clicked', self._go_forward_cb)
        self.insert(self._forward, -1)
        self._forward.show()

        home = ToolButton('zoom-home')
        home.set_tooltip(_('Home'))
        home.connect('clicked', self._go_home_cb)
        self.insert(home, -1)
        home.show()

        ##progress_listener = self._web_view.progress
        ##progress_listener.connect('location-changed',
        ##                          self._location_changed_cb)
        ##progress_listener.connect('loading-stop', self._loading_stop_cb)

    def _location_changed_cb(self, progress_listener, uri):
        self.update_navigation_buttons()

    def _loading_stop_cb(self, progress_listener):
        self.update_navigation_buttons()
        
    def update_navigation_buttons(self):
        self._back.set_sensitive(self._web_view.can_go_back())
        self._forward.set_sensitive(self._web_view.can_go_forward())

    def _go_back_cb(self, button):
        self._web_view.go_back()
    
    def _go_forward_cb(self, button):
        self._web_view.go_forward()

    def _go_home_cb(self, button):
        self._web_view.load_uri(HOME)

