# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2024 by Benjamin Johnson
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
Simple API for creating worker objects.

A Worker is used to run slow operations in a background thread, which
is normally app.worker_thread(). Subclass Worker to implement your logic,
then call your subclass's create() method to instantiate it.

A Worker does not have a parent QObject, but does keep a weak reference
to its controller in its controller attribute. The controller does not
need to be derived from QObject.

"""

import weakref

from PyQt6.QtCore import QObject, QMutex

import app


class Worker(QObject):
    """Base class for worker objects.

    Subclass this to define slots to perform work and signals to
    communicate with its controller.

    Create workers using your subclass's create() class method.

    """
    def __init__(self, controller):
        super().__init__()  # we can't move this to another thread if we
                            # construct the underlying QObject with a parent
        self.controller = weakref.ref(controller)
        self._mutex = None

    def mutex(self):
        """Return a QMutex for this Worker.

        Use this if you need to exchange data with the Worker from
        another thread but can't use signal/slot parameters, for example
        because you're triggering it from a QTimer.

        The QMutex is created the first time this method is called.

        """
        if self._mutex is None:
            self._mutex = QMutex()
        return self._mutex

    @classmethod
    def create(cls, controller):
        """Create a worker object with the specified controller.

        The worker is moved to the global worker thread and scheduled
        for deletion when that thread exits.

        """
        worker = cls(controller)
        worker.moveToThread(app.worker_thread())
        app.worker_thread().finished.connect(worker.deleteLater)
        return worker
