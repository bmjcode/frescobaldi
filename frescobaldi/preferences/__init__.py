# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2014 by Wilbert Berendsen
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# See http://www.gnu.org/licenses/ for more information.

"""
The Preferences Dialog.
"""



from PyQt6.QtCore import QMargins, QSettings, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence
from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QGroupBox, QHBoxLayout, QListWidget,
    QListWidgetItem, QScrollArea, QStackedWidget, QVBoxLayout, QWidget)

import app
import qutil
import userguide
import icons
import widgets

_prefsindex = 0 # global setting for selected prefs page but not saved on exit

def pageorder():
    """Yields the page item classes in order."""
    yield General
    yield LilyPond
    yield MusicViewers
    yield Midi
    yield Editor
    yield Tools
    yield Paths
    yield Documentation
    yield Shortcuts
    yield FontsColors
    yield Helpers
    yield Extensions


class CancelClosingPreferences(Exception):
    pass


class PreferencesDialog(QDialog):

    def __init__(self, mainwindow):
        super().__init__(mainwindow)
        self.setWindowModality(Qt.WindowModality.WindowModal)
        if mainwindow:
            self.addAction(mainwindow.actionCollection.help_whatsthis)
        layout = QVBoxLayout()
        layout.setSpacing(10)
        self.setLayout(layout)

        # listview to the left, stacked widget to the right
        top = QHBoxLayout()
        layout.addLayout(top)

        self.pagelist = QListWidget(self)
        self.stack = QStackedWidget(self)
        top.addWidget(self.pagelist, 0)
        top.addWidget(self.stack, 2)

        layout.addWidget(widgets.Separator(self))

        b = self.buttons = QDialogButtonBox(self)
        b.setStandardButtons(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Apply
            | QDialogButtonBox.StandardButton.Reset
            | QDialogButtonBox.StandardButton.Help)
        layout.addWidget(b)
        b.accepted.connect(self.maybeAccept)
        b.rejected.connect(self.reject)
        # saveSettings() may raise CancelClosingPreferences. This is primarily
        # for use when it makes sense for the "Ok" button, but may occur in "Apply",
        # so we need to catch it.
        b.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.trySaveSettings)
        b.button(QDialogButtonBox.StandardButton.Reset).clicked.connect(self.loadSettings)
        b.button(QDialogButtonBox.StandardButton.Help).clicked.connect(self.showHelp)
        b.button(QDialogButtonBox.StandardButton.Help).setShortcut(QKeySequence.StandardKey.HelpContents)
        b.button(QDialogButtonBox.StandardButton.Apply).setEnabled(False)

        # fill the pagelist
        self.pagelist.setIconSize(QSize(32, 32))
        self.pagelist.setSpacing(2)
        for item in pageorder():
            self.pagelist.addItem(item())
        self.pagelist.currentItemChanged.connect(self.slotCurrentItemChanged)

        app.translateUI(self, 100)
        # read our size and selected page
        qutil.saveDialogSize(self, "preferences/dialog/size", QSize(500, 300))
        self.pagelist.setCurrentRow(_prefsindex)

    def translateUI(self):
        self.pagelist.setFixedWidth(self.pagelist.sizeHintForColumn(0) + 12)
        self.setWindowTitle(app.caption(_("Preferences")))

    def trySaveSettings(self):
        try:
            self.saveSettings()
        except CancelClosingPreferences:
            return False
        else:
            return True

    def maybeAccept(self):
        if (not self.buttons.button(QDialogButtonBox.StandardButton.Apply).isEnabled()
              or self.trySaveSettings()):
            self.accept()

    def done(self, result):
        # save our size and selected page
        global _prefsindex
        _prefsindex = self.pagelist.currentRow()
        super().done(result)

    def pages(self):
        """Yields the settings pages that are already instantiated."""
        for n in range(self.stack.count()):
            yield self.stack.widget(n)

    def showHelp(self):
        userguide.show(self.pagelist.currentItem().help)

    def loadSettings(self):
        """Loads the settings on reset."""
        for page in self.pages():
            page.loadSettings()
            page.hasChanges = False
        self.buttons.button(QDialogButtonBox.StandardButton.Apply).setEnabled(False)

    def saveSettings(self):
        """Saves the settings and applies them."""
        for page in self.pages():
            if page.hasChanges:
                page.saveSettings() # this may raise CancelClosingPreferences
                page.hasChanges = False
        self.buttons.button(QDialogButtonBox.StandardButton.Apply).setEnabled(False)

        # emit the signal
        app.settingsChanged()

    def slotCurrentItemChanged(self, item):
        item.activate()

    def changed(self):
        """Call this to enable the Apply button."""
        self.buttons.button(QDialogButtonBox.StandardButton.Apply).setEnabled(True)


class PrefsItemBase(QListWidgetItem):
    help = "preferences"
    def __init__(self):
        super().__init__()
        self._widget = None
        self.setIcon(icons.get(self.iconName))
        app.translateUI(self)

    def activate(self):
        dlg = self.listWidget().parentWidget()
        if self._widget is None:
            w = self._widget = self.widget(dlg)
            dlg.stack.addWidget(w)
            w.loadSettings()
            w.changed.connect(dlg.changed)
            w.changed.connect(w.markChanged)
        dlg.stack.setCurrentWidget(self._widget)


class General(PrefsItemBase):
    help = "prefs_general"
    iconName = "preferences-system"
    def translateUI(self):
        self.setText(_("General"))

    def widget(self, dlg):
        from . import general
        return general.GeneralPrefs(dlg)


class MusicViewers(PrefsItemBase):
    help = "prefs_musicviewers"
    iconName = "Audio-x-generic"
    def translateUI(self):
        self.setText(_("Music View"))

    def widget(self, dlg):
        from . import musicviewers
        return musicviewers.MusicViewers(dlg)


class LilyPond(PrefsItemBase):
    help = "prefs_lilypond"
    iconName = "lilypond-run"
    def translateUI(self):
        self.setText(_("LilyPond"))

    def widget(self, dlg):
        from . import lilypond
        return lilypond.LilyPondPrefs(dlg)


class Midi(PrefsItemBase):
    help = "prefs_midi"
    iconName = "audio-volume-medium"
    def translateUI(self):
        self.setText(_("MIDI"))

    def widget(self, dlg):
        from . import midi
        return midi.MidiPrefs(dlg)


class Helpers(PrefsItemBase):
    help = "prefs_helpers"
    iconName = "applications-other"
    def translateUI(self):
        self.setText(_("Helper Apps"))

    def widget(self, dlg):
        from . import helpers
        return helpers.Helpers(dlg)


class Paths(PrefsItemBase):
    help = "prefs_paths"
    iconName = "folder-open"
    def translateUI(self):
        self.setText(_("Paths"))

    def widget(self, dlg):
        from . import paths
        return paths.Paths(dlg)


class Documentation(PrefsItemBase):
    help = "prefs_lilydoc"
    iconName = "help-contents"
    def translateUI(self):
        self.setText(_("LilyPond Docs"))

    def widget(self, dlg):
        from . import documentation
        return documentation.Documentation(dlg)


class Shortcuts(PrefsItemBase):
    help = "prefs_shortcuts"
    iconName = "preferences-desktop-keyboard-shortcuts"
    def translateUI(self):
        self.setText(_("Shortcuts"))

    def widget(self, dlg):
        from . import shortcuts
        return shortcuts.Shortcuts(dlg)


class Editor(PrefsItemBase):
    help = "prefs_editor"
    iconName = "document-properties"
    def translateUI(self):
        self.setText(_("Editor"))

    def widget(self, dlg):
        from . import editor
        return editor.Editor(dlg)


class FontsColors(PrefsItemBase):
    help = "prefs_fontscolors"
    iconName = "applications-graphics"
    def translateUI(self):
        self.setText(_("Fonts & Colors"))

    def widget(self, dlg):
        from . import fontscolors
        return fontscolors.FontsColors(dlg)


class Tools(PrefsItemBase):
    help = "prefs_tools"
    iconName = "preferences-other"
    def translateUI(self):
        self.setText(_("Tools"))

    def widget(self, dlg):
        from . import tools
        return tools.Tools(dlg)


class Extensions(PrefsItemBase):
    help = "prefs_extensions"
    iconName = "network-plug"
    def translateUI(self):
        self.setText(_("Extensions"))

    def widget(self, dlg):
        from . import extensions
        return extensions.Extensions(dlg)


class Page(QWidget):
    """Base class for settings pages."""
    changed = pyqtSignal()
    hasChanges = False

    def markChanged(self):
        """Called when something changes in the dialog."""
        self.hasChanges = True

    def loadSettings(self):
        """Should load settings from config into our widget."""

    def saveSettings(self):
        """Should write settings from our widget to config."""


class ScrolledPage(Page):
    """Base class for settings pages that are scrollable.

    Te scrolledWidget attribute has the widget the other components
    can be added to.

    """
    def __init__(self, dialog):
        super().__init__(dialog)
        layout = QVBoxLayout(contentsMargins=QMargins(0, 0, 0, 0), spacing=0)
        self.setLayout(layout)
        scrollarea = QScrollArea(frameWidth=0, frameShape=QScrollArea.Shape.NoFrame)
        layout.addWidget(scrollarea)
        self.scrolledWidget = QWidget(scrollarea)
        scrollarea.setWidget(self.scrolledWidget)
        scrollarea.setWidgetResizable(True)


class GroupsPage(Page):
    """Base class for a Page with SettingsGroups.

    The load and save methods of the SettingsGroup groups are automatically called.

    """
    def __init__(self, dialog):
        super().__init__(dialog)
        self.groups = []

    def loadSettings(self):
        for group in self.groups:
            group.loadSettings()

    def saveSettings(self):
        for group in self.groups:
            group.saveSettings()

    def group(self, classname):
        """Access another group on the current page
        by passing its class."""
        for g in self.groups:
            if isinstance(g, classname):
                return g
        raise ValueError("No Group with class \"{}\" on this Page")


class ScrolledGroupsPage(GroupsPage, ScrolledPage):
    def __init__(self, dialog):
        ScrolledPage.__init__(self, dialog)
        self.groups = []


class Group(QGroupBox):
    """This is a QGroupBox that auto-adds itself to a Page."""
    changed = pyqtSignal()

    def __init__(self, page):
        super().__init__()
        self._page = page
        page.groups.append(self)
        self.changed.connect(page.changed)

    def loadSettings(self):
        """Should load settings from config into our widget."""

    def saveSettings(self):
        """Should write settings from our widget to config."""

    def page(self):
        """Return a reference to the Page the Group is on."""
        return self._page

    def siblingGroup(self, classname):
        """Return a reference to another Group on the same page."""
        return self.page().group(classname)
