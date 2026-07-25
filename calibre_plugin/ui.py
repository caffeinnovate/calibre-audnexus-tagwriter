from calibre.gui2 import info_dialog
from calibre.gui2.actions import InterfaceAction
from qt.core import QCheckBox, QDialog, QDialogButtonBox, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout

from calibre_plugins.audnexus_tag_writer.main import build_jobs, write_jobs
from calibre_plugins.audnexus_tag_writer.metadata import FIELD_LABELS


class PreviewDialog(QDialog):
    def __init__(self, parent, jobs, skipped):
        super().__init__(parent)
        self.setWindowTitle(_('Preview Audnexus tag updates'))
        self.resize(900, 500)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(_('Review the tags that will be written. Existing values for absent Calibre fields are preserved unless you select the option below.')))
        self.clear_missing = QCheckBox(_('Clear existing tags when the matching Calibre field is empty'))
        layout.addWidget(self.clear_missing)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels([_('File'), _('Tag'), _('New value')])
        layout.addWidget(self.table)
        for _book_id, path, values in jobs:
            for key, value in values.items():
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(path))
                self.table.setItem(row, 1, QTableWidgetItem(FIELD_LABELS[key]))
                self.table.setItem(row, 2, QTableWidgetItem(_('Embedded image') if key == 'cover' else str(value)))
        if skipped:
            layout.addWidget(QLabel(_('{0} selected book(s) have no managed MP3/M4B format and will be skipped.').format(len(skipped))))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(_('Write tags'))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class AudnexusBulkUpdateAction(InterfaceAction):
    name = 'Audnexus Tag Writer'
    action_spec = (_('Update all audiobooks'), None, _('Write Audnexus metadata to every managed MP3/M4B audiobook'), None)

    def genesis(self):
        self.qaction.triggered.connect(self.run)

    def run(self):
        db = self.gui.current_db
        all_ids = getattr(db, 'all_book_ids', None)
        ids = sorted(all_ids() if all_ids is not None else db.new_api.all_book_ids())
        if not ids:
            info_dialog(self.gui, _('No books found'), _('The current Calibre library contains no books.'), show=True)
            return
        jobs, skipped = build_jobs(db, ids)
        if not jobs:
            info_dialog(self.gui, _('No audiobook files found'), _('None of the selected books has a managed MP3 or M4B format.'), show=True)
            return
        preview = PreviewDialog(self.gui, jobs, skipped)
        if preview.exec() != QDialog.DialogCode.Accepted:
            return
        updated, failures = write_jobs(jobs, preview.clear_missing.isChecked())
        lines = [_('Updated: {0} file(s)').format(len(updated)), _('Skipped: {0} book(s)').format(len(skipped))]
        if failures:
            lines.append(_('Failed: {0} file(s)').format(len(failures)))
            lines.extend('{}: {}'.format(path, error) for _book_id, path, error in failures)
        info_dialog(self.gui, _('Audnexus tag update complete'), '<br>'.join(lines), show=True)
