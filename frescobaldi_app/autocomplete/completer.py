# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2011 - 2014 by Wilbert Berendsen
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
The completer for Frescobaldi.
"""


import re

from PyQt6.QtCore import QMutex, QObject, QThread, pyqtSignal
from PyQt6.QtGui import QTextCursor

import app
import textformats
import widgets.completer


class Completer(widgets.completer.Completer):
    def __init__(self):
        super().__init__()
        self.setMaxVisibleItems(16)
        self.popup().setMinimumWidth(100)
        app.settingsChanged.connect(self.readSettings)
        self.readSettings()

        self._mutex = QMutex()
        self._workerThread = QThread()
        self._workerThread.finished.connect(self._workerThread.deleteLater)
        self._worker = CompleterWorker(self)
        self.popupRequested.connect(self._worker.slotPrepareCompletionCursor)
        self._worker.haveCompletionCursor.connect(self.slotShowCompletionPopup)
        self._worker.moveToThread(self._workerThread)
        self._workerThread.start()

    def __del__(self):
        self._workerThread.quit()
        self._workerThread.wait()

    def readSettings(self):
        self.popup().setFont(textformats.formatData('editor').font)
        self.popup().setPalette(textformats.formatData('editor').palette())

    def completionCursor(self):
        pass

    def showCompletionPopup(self, forced=True):
        self.popupRequested.emit(self.textCursor(), forced)

    def mutex(self):
        return self._mutex

    popupRequested = pyqtSignal('PyQt_PyObject', bool)


class CompleterWorker(QObject):
    """Worker to create a completion model in a background thread."""
    def __init__(self, plugin):
        super().__init__()  # no parent
        self._plugin = plugin

    def slotPrepareCompletionCursor(self, cursor, forced):
        plugin = self._plugin
        try:
            plugin.mutex().lock()
            # trick: if we are still visible we don't have to analyze the text again
            if not (plugin.popup().isVisible() and self._pos < cursor.position()):
                analyzer = self.analyzer()
                pos, model = analyzer.completions(cursor)
                if not model:
                    return
                self._pos = cursor.block().position() + pos
                if plugin.model() != model:
                    plugin.setModel(model)
            cursor.setPosition(self._pos, QTextCursor.MoveMode.KeepAnchor)
            self.haveCompletionCursor.emit(cursor, forced)
        finally:
            plugin.mutex().unlock()

    def analyzer(self):
        from . import analyzer
        return analyzer.Analyzer()

    haveCompletionCursor = pyqtSignal('PyQt_PyObject', bool)


