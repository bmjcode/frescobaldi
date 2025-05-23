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
Keyboard shortcuts settings page.
"""


from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QStyleFactory,
    QTabWidget,
    QVBoxLayout,
    QWidget
)

import app
import appinfo
import icons
import preferences
import sessions
import util
import i18n
import remote
import language_names

from widgets.urlrequester import UrlRequester


class GeneralPrefs(preferences.ScrolledGroupsPage):
    def __init__(self, dialog):
        super().__init__(dialog)

        layout = QVBoxLayout()
        self.scrolledWidget.setLayout(layout)

        layout.addWidget(General(self))
        layout.addWidget(SessionsAndFiles(self))
        layout.addWidget(ExperimentalFeatures(self))


class General(preferences.Group):
    def __init__(self, page):
        super().__init__(page)

        grid = QGridLayout()
        self.setLayout(grid)

        self.langLabel = QLabel()
        self.lang = QComboBox(currentIndexChanged=self.changed)
        grid.addWidget(self.langLabel, 0, 0)
        grid.addWidget(self.lang, 0, 1)

        self.styleLabel = QLabel()
        self.styleCombo = QComboBox(currentIndexChanged=self.changed)
        grid.addWidget(self.styleLabel, 1, 0)
        grid.addWidget(self.styleCombo, 1, 1)

        self.systemIcons = QCheckBox(toggled=self.changed)
        grid.addWidget(self.systemIcons, 2, 0, 1, 3)
        self.tabsClosable = QCheckBox(toggled=self.changed)
        grid.addWidget(self.tabsClosable, 3, 0, 1, 3)
        self.splashScreen = QCheckBox(toggled=self.changed)
        grid.addWidget(self.splashScreen, 4, 0, 1, 3)
        self.allowRemote = QCheckBox(toggled=self.changed)
        grid.addWidget(self.allowRemote, 5, 0, 1, 3)

        grid.setColumnStretch(2, 1)

        # fill in the language combo
        self._langs = ["C", ""]
        self.lang.addItems(('', ''))
        langnames = [(language_names.languageName(lang, lang), lang) for lang in i18n.available()]
        langnames.sort()
        for name, lang in langnames:
            self._langs.append(lang)
            self.lang.addItem(name)

        # fill in style combo
        self.styleCombo.addItem('')
        self.styleCombo.addItems(QStyleFactory.keys())

        app.translateUI(self)

    def loadSettings(self):
        s = QSettings()
        lang = s.value("language", "", str)
        try:
            index = self._langs.index(lang)
        except ValueError:
            index = 1
        self.lang.setCurrentIndex(index)
        style = s.value("guistyle", "", str).lower()
        styles = [name.lower() for name in QStyleFactory.keys()]
        try:
            index = styles.index(style) + 1
        except ValueError:
            index = 0
        self.styleCombo.setCurrentIndex(index)
        self.systemIcons.setChecked(s.value("system_icons", True, bool))
        self.tabsClosable.setChecked(s.value("tabs_closable", True, bool))
        self.splashScreen.setChecked(s.value("splash_screen", True, bool))
        self.allowRemote.setChecked(remote.enabled())

    def saveSettings(self):
        s = QSettings()
        s.setValue("language", self._langs[self.lang.currentIndex()])
        s.setValue("system_icons", self.systemIcons.isChecked())
        s.setValue("tabs_closable", self.tabsClosable.isChecked())
        s.setValue("splash_screen", self.splashScreen.isChecked())
        s.setValue("allow_remote", self.allowRemote.isChecked())
        if self.styleCombo.currentIndex() == 0:
            s.remove("guistyle")
        else:
            s.setValue("guistyle", self.styleCombo.currentText())
        # update all top-level windows, so icon changes are picked up
        for w in QApplication.topLevelWidgets():
            if w.isVisible():
                w.update()

    def translateUI(self):
        self.setTitle(_("Language and Style"))
        self.langLabel.setText(_("Language:"))
        self.lang.setItemText(0, _("No Translation"))
        self.lang.setItemText(1, _("System Default Language (if available)"))
        self.styleLabel.setText(_("Style:"))
        self.styleCombo.setItemText(0, _("Default"))
        self.systemIcons.setText(_("Use System Icons"))
        self.systemIcons.setToolTip(_(
            "If checked, icons of the desktop icon theme "
            "will be used instead of the bundled icons."))
        self.splashScreen.setText(_("Show Splash Screen on Startup"))
        self.tabsClosable.setText(_("Show Close Button on Document tabs"))
        self.allowRemote.setText(_("Open Files in Running Instance"))
        self.allowRemote.setToolTip(_(
            "If checked, files will be opened in a running Frescobaldi "
            "application if available, instead of starting a new instance."))


class SessionsAndFiles(preferences.Group):
    def __init__(self, page):
        super().__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)

        def changed():
            self.changed.emit()
            self.new_combo.setEnabled(self.template.isChecked())
            self.session_combo.setEnabled(self.session_custom.isChecked())

        def customchanged():
            self.changed.emit()
            self.filenameTemplate.setEnabled(self.customFilename.isChecked())

        self.verbose_toolbuttons = QCheckBox(toggled=self.changed)
        layout.addWidget(self.verbose_toolbuttons)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # New Documents Tab
        self.new_tab = QWidget()
        self.tabs.addTab(self.new_tab, "")
        new_layout_wrap = QVBoxLayout()
        self.new_tab.setLayout(new_layout_wrap)
        new_layout = QGridLayout()
        new_layout_wrap.addLayout(new_layout)

        self.emptyDocument = QRadioButton(toggled=changed)
        self.lilyVersion = QRadioButton(toggled=changed)
        self.template = QRadioButton(toggled=changed)
        self.new_combo = QComboBox(currentIndexChanged=changed)

        new_layout.addWidget(self.emptyDocument, 0, 0, 1, 2)
        new_layout.addWidget(self.lilyVersion, 1, 0, 1, 2)
        new_layout.addWidget(self.template, 2, 0, 1, 1)
        new_layout.addWidget(self.new_combo, 2, 1, 1, 1)
        new_layout_wrap.addStretch()

        # Saving Files Tab
        self.save_tab = QWidget()
        self.tabs.addTab(self.save_tab, "")
        save_layout = QVBoxLayout()
        self.save_tab.setLayout(save_layout)

        self.stripwsp = QCheckBox(toggled=self.changed)
        self.backup = QCheckBox(toggled=self.changed)
        self.metainfo = QCheckBox(toggled=self.changed)
        self.format = QCheckBox(toggled=self.changed)
        save_layout.addWidget(self.stripwsp)
        save_layout.addWidget(self.backup)
        save_layout.addWidget(self.metainfo)
        save_layout.addWidget(self.format)
        basedir_layout = QHBoxLayout()
        save_layout.addLayout(basedir_layout)

        self.basedirLabel = l = QLabel()
        self.basedir = UrlRequester()
        basedir_layout.addWidget(self.basedirLabel)
        basedir_layout.addWidget(self.basedir)
        self.basedir.changed.connect(self.changed)

        filename_layout = QHBoxLayout()
        save_layout.addLayout(filename_layout)

        self.customFilename = QCheckBox(toggled=customchanged)
        self.filenameTemplate = QLineEdit(textEdited=self.changed)
        filename_layout.addWidget(self.customFilename)
        filename_layout.addWidget(self.filenameTemplate)

        # Sessions Tab
        self.session_tab = QWidget()
        self.tabs.addTab(self.session_tab, "")
        session_layout = QGridLayout()
        session_layout_wrap = QVBoxLayout()
        self.session_tab.setLayout(session_layout_wrap)

        self.session_label = QLabel()
        session_layout_wrap.addWidget(self.session_label)
        session_layout_wrap.addLayout(session_layout)

        self.session_none = QRadioButton(toggled=changed)
        self.session_lastused = QRadioButton(toggled=changed)
        self.session_custom = QRadioButton(toggled=changed)
        self.session_combo = QComboBox(currentIndexChanged=changed)

        session_layout.addWidget(self.session_none, 0, 0, 1, 2)
        session_layout.addWidget(self.session_lastused, 1, 0, 1, 2)
        session_layout.addWidget(self.session_custom, 2, 0, 1, 1)
        session_layout.addWidget(self.session_combo, 2, 1, 1, 1)
        session_layout_wrap.addStretch()

        self.loadNewCombo()
        self.page().parent().finished.connect(self.saveTabIndex)
        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Sessions and Files"))
        self.verbose_toolbuttons.setText(_(
            "Add pull-down menus in main toolbar"
        ))
        self.verbose_toolbuttons.setToolTip("<font>{}</font>".format(
            _("If set, the file related buttons in the main toolbar will "
            "provide pull-down menus with additional functions.")
        ))

        # New Documents Tab
        self.tabs.setTabText(0, _("New Document"))
        self.emptyDocument.setText(_("Create an empty document"))
        self.lilyVersion.setText(_("Create a document that contains the LilyPond version statement"))
        self.template.setText(_("Create a document from a template:"))
        from snippet import snippets
        for i, name in enumerate(self._names):
            self.new_combo.setItemText(i, snippets.title(name))

        # Saving Files Tab
        self.tabs.setTabText(1, _("Saving"))
        self.stripwsp.setText(_("Strip trailing whitespace"))
        self.stripwsp.setToolTip(_(
            "If checked, Frescobaldi will remove unnecessary whitespace at the "
            "end of lines (but not inside multi-line strings)."))
        self.backup.setText(_("Keep backup copy"))
        self.backup.setToolTip(_(
            "Frescobaldi always backups a file before overwriting it "
            "with a new version.\n"
            "If checked those backup copies are retained."))
        self.metainfo.setText(_("Remember cursor position, bookmarks, etc."))
        self.format.setText(_("Format document"))

        self.basedirLabel.setText(_("Default directory:"))
        self.basedirLabel.setToolTip(_("The default folder for your LilyPond documents (optional)."))
        self.customFilename.setText(_("Use custom default file name:"))
        self.customFilename.setToolTip(_(
            "If checked, Frescobaldi will use the template to generate a default file name.\n"
            "{title} and {composer} will be replaced by title and composer of that document."))

        # Sessions Tab
        self.tabs.setTabText(2, _("Sessions"))
        self.session_label.setText(_(
            "Session to load if Frescobaldi is started without arguments"
        ))
        self.session_none.setText(_("Start with no session"))
        self.session_lastused.setText(_("Start with last used session"))
        self.session_custom.setText(_("Start with session:"))

    def loadNewCombo(self):
        from snippet import snippets
        self._names = [name for name in snippets.names()
                        if snippets.get(name).variables.get('template')]
        self.new_combo.clear()
        self.new_combo.addItems([''] * len(self._names))

    def loadSettings(self):
        s = QSettings()
        self.verbose_toolbuttons.setChecked(
            s.value("verbose_toolbuttons", False, bool)
        )

        # New Documents Tab
        ndoc = s.value("new_document", "empty", str)
        template = s.value("new_document_template", "", str)
        if template in self._names:
            self.new_combo.setCurrentIndex(self._names.index(template))
        if ndoc == "template":
            self.template.setChecked(True)
        elif ndoc == "version":
            self.lilyVersion.setChecked(True)
        else:
            self.emptyDocument.setChecked(True)

        # Saving Files Tab
        self.stripwsp.setChecked(s.value("strip_trailing_whitespace", False, bool))
        self.backup.setChecked(s.value("backup_keep", False, bool))
        self.metainfo.setChecked(s.value("metainfo", True, bool))
        self.format.setChecked(s.value("format", False, bool))
        self.basedir.setPath(s.value("basedir", "", str))
        self.customFilename.setChecked(s.value("custom_default_filename", False, bool))
        self.filenameTemplate.setText(s.value("default_filename_template", "{composer}-{title}", str))
        self.filenameTemplate.setEnabled(self.customFilename.isChecked())

        # Sessions Tab
        s.beginGroup("session")
        startup = s.value("startup", "none", str)
        if startup ==  "lastused":
            self.session_lastused.setChecked(True)
        elif startup == "custom":
            self.session_custom.setChecked(True)
        else:
            self.session_none.setChecked(True)
        sessionNames = sessions.sessionNames()
        self.session_combo.clear()
        self.session_combo.addItems(sessionNames)
        custom = s.value("custom", "", str)
        if custom in sessionNames:
            self.session_combo.setCurrentIndex(sessionNames.index(custom))
        s.endGroup()
        self.tabs.setCurrentIndex(
            s.value("prefs_general_file_tab_index", 0, int)
        )

    def saveSettings(self):
        s = QSettings()
        s.setValue("verbose_toolbuttons", self.verbose_toolbuttons.isChecked())

        # New Documents Tab
        if self._names and self.template.isChecked():
            s.setValue("new_document", "template")
            s.setValue("new_document_template", self._names[self.new_combo.currentIndex()])
        elif self.lilyVersion.isChecked():
            s.setValue("new_document", "version")
        else:
            s.setValue("new_document", "empty")

        # Saving Files Tab
        s.setValue("strip_trailing_whitespace", self.stripwsp.isChecked())
        s.setValue("backup_keep", self.backup.isChecked())
        s.setValue("metainfo", self.metainfo.isChecked())
        s.setValue("format", self.format.isChecked())
        s.setValue("basedir", self.basedir.path())
        s.setValue("custom_default_filename", self.customFilename.isChecked())
        s.setValue("default_filename_template", self.filenameTemplate.text())

        # Sessions Tab
        s.beginGroup("session")
        s.setValue("custom", self.session_combo.currentText())
        if self.session_custom.isChecked():
            startup = "custom"
        elif self.session_lastused.isChecked():
            startup = "lastused"
        else:
            startup = "none"
        s.setValue("startup", startup)

    def saveTabIndex(self):
        s = app.settings("")
        s.setValue("prefs_general_file_tab_index", self.tabs.currentIndex())


class ExperimentalFeatures(preferences.Group):
    def __init__(self, page):
        super().__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.experimentalFeatures = QCheckBox(toggled=self.changed)
        layout.addWidget(self.experimentalFeatures)
        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Experimental Features"))
        self.experimentalFeatures.setText(_("Enable Experimental Features"))
        self.experimentalFeatures.setToolTip('<qt>' + _(
            "If checked, features that are not yet finished are enabled.\n"
            "You need to restart Frescobaldi to see the changes."))

    def loadSettings(self):
        s = QSettings()
        self.experimentalFeatures.setChecked(s.value("experimental-features", False, bool))

    def saveSettings(self):
        s = QSettings()
        s.setValue(
            "experimental-features", self.experimentalFeatures.isChecked()
        )
