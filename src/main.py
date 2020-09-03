# -*- coding: utf-8 -*-

# Find and Replace Tags using Regular Expressions: an Anki Add-on
# Copyright (C) 2020  RumovZ
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


from aqt import gui_hooks
from aqt.qt import QAction, QKeySequence
from .replacer import Replacer


def setup_menu(browser):
    menu = browser.form.menu_Notes
    before = browser.form.actionClear_Unused_Tags
    browser.form.actionFind_replace_tags = action = QAction('Find and Replace Tags (RegEx)')
    menu.insertAction(before, action)
    action.setShortcut(QKeySequence("Ctrl+Alt+Shift+R"))
    action.triggered.connect(lambda: Replacer(browser))


gui_hooks.browser_menus_did_init.append(setup_menu)
