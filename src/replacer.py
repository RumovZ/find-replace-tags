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

import re
from typing import List

# noinspection PyProtectedMember
from anki.lang import _
from aqt.qt import Qt, QDialog, QDialogButtonBox
from aqt.utils import tooltip, restore_combo_history, save_combo_history, askUser

from .ui.main import Ui_Dialog
from .utils import on_help


class Replacer:

    find: str
    replace: str
    tags: str
    case: int
    combo = "FindAndReplaceTags"
    find_history: List
    replace_history: List
    n_tags_changed = 0
    n_notes_changed = 0
    n_replacements = 0

    def __init__(self, browser):
        self.b = browser
        if not self.b.selectedNotes():
            tooltip("No cards selected.")
            return
        self.d = QDialog(self.b)
        self.f = Ui_Dialog()
        self.set_up_form()
        self.d.setWindowModality(Qt.WindowModal)
        r = self.d.exec_()
        if not r:
            return
        self.save_history()
        self.b.mw.checkpoint(_("Find and Replace Tags"))
        self.b.model.beginReset()
        self.b.mw.taskman.run_in_background(self.do_find_replace, self.on_done)

    def set_up_form(self):
        self.f.setupUi(self.d)
        self.connect_signals()
        self.restore_history()
        self.f.input_tags.setCol(self.b.col)
        self.on_input_changed()

    def connect_signals(self):
        self.f.input_find.currentTextChanged.connect(self.on_input_changed)
        self.f.input_replace.currentTextChanged.connect(self.on_input_changed)
        self.f.is_case.stateChanged.connect(self.on_input_changed)
        self.f.input_tags.textChanged.connect(self.on_input_changed)
        self.f.buttonBox.button(QDialogButtonBox.Help).pressed.connect(on_help)

    def restore_history(self):
        self.find_history = restore_combo_history(self.f.input_find, self.combo + "Find")
        self.f.input_find.completer().setCaseSensitivity(True)
        self.replace_history = restore_combo_history(self.f.input_replace, self.combo + "Replace")
        self.f.input_replace.completer().setCaseSensitivity(True)

    def save_history(self):
        save_combo_history(self.f.input_find, self.find_history, self.combo + "Find")
        save_combo_history(self.f.input_replace, self.replace_history, self.combo + "Replace")

    def on_input_changed(self):
        self.read_input()
        enable = False
        try:
            re.sub(self.find, self.replace, "")
        except re.error:
            out = "INVALID EXPRESSION"
        else:
            out = self.tag_preview()
            if self.find or self.replace:
                enable = True
        self.toggle_okay(enable)
        self.f.output_tags.setText(out)

    def read_input(self):
        self.find = self.f.input_find.currentText()
        self.replace = self.f.input_replace.currentText()
        self.case = 0 if self.f.is_case.isChecked() else re.I
        self.tags = self.f.input_tags.text().split()

    def tag_preview(self):
        pattern = re.compile(self.find, flags=self.case)
        new_tags = [pattern.sub(self.replace, t) for t in self.tags]
        return " ".join(set(new_tags))

    def toggle_okay(self, enabled):
        self.f.buttonBox.button(QDialogButtonBox.Ok).setEnabled(enabled)

    def do_find_replace(self):
        nids = self.b.selectedNotes()
        pattern = re.compile(self.find, flags=self.case)
        for nid in nids:
            note = self.b.col.getNote(nid)
            tags_subs = [pattern.subn(self.replace, tag) for tag in note.tags]
            new_tags = [t[0] for t in tags_subs]
            note.tags = new_tags
            note.flush()
            replacements = [t[1] for t in tags_subs if t[1] != 0]
            self.n_replacements += sum(replacements)
            n_tags_changed = len(replacements)
            self.n_tags_changed += n_tags_changed
            self.n_notes_changed += (n_tags_changed > 0)

    def on_done(self, _):
        self.b.search()
        self.b.mw.requireReset()
        self.b.model.endReset()
        self.b.mw.reset()
        t1 = " was" if self.n_replacements == 1 else "s were"
        t2 = "" if self.n_tags_changed == 1 else "s"
        t3 = "" if self.n_notes_changed == 1 else "s"
        msg = f"{self.n_replacements} replacement{t1} made " \
              f"in {self.n_tags_changed} tag{t2} " \
              f"of {self.n_notes_changed} note{t3}." \
              f"<br>Do you wish to clear unused tags now?"
        if askUser(msg, parent=self.b):
            self.b.clearUnusedTags()
