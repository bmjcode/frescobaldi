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
Base class for worker objects.

A Worker is used to run slow operations in a background thread, which
is normally app.worker_thread(). Subclass it to define slots to perform
work and signals to communicate with its parent.

A Worker keeps a weak reference to its parent in its parent attribute.

"""

import weakref

from PyQt6.QtCore import QObject


class Worker(QObject):
    """Base class for worker objects."""
    def __init__(self, parent):
        super().__init__()  # we can't move this to another thread if we
                            # construct the underlying QObject with a parent
        self.parent = weakref.ref(parent)
