from calibre.gui2 import Dispatcher, error_dialog, info_dialog
from calibre.gui2.actions import InterfaceAction
from calibre.gui2.threaded_jobs import ThreadedJob
from qt.core import QCheckBox, QDialog, QDialogButtonBox, QIcon, QLabel, QPixmap, QTreeWidget, QTreeWidgetItem, QVBoxLayout

from calibre_plugins.audnexus_tag_writer.main import build_jobs_in_background, write_jobs_in_background
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
        self.tree = QTreeWidget()
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels([_('File'), _('Tag'), _('Old value'), _('New value')])
        self.tree.setColumnWidth(0, 330)
        self.tree.setColumnWidth(1, 130)
        self.tree.setColumnWidth(2, 180)
        layout.addWidget(self.tree)
        for _book_id, path, values, old_values in jobs:
            file_item = QTreeWidgetItem([path, '', '', ''])
            self.tree.addTopLevelItem(file_item)
            for key, value in values.items():
                QTreeWidgetItem(file_item, [
                    '',
                    FIELD_LABELS[key],
                    self.display_value(key, old_values.get(key)),
                    self.display_value(key, value),
                ])
        self.tree.expandAll()
        if skipped:
            layout.addWidget(QLabel(_('{0} book(s) have no managed MP3/M4B format and will be skipped.').format(len(skipped))))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(_('Write tags'))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def display_value(key, value):
        if key == 'cover':
            return _('Embedded image') if value else _('Not set')
        return str(value) if value not in (None, '') else _('Not set')


class AudnexusBulkUpdateAction(InterfaceAction):
    name = 'Audnexus Tag Writer'
    action_spec = (_('Update all audiobooks'), None, _('Write Audnexus metadata to every managed MP3/M4B audiobook'), None)

    def genesis(self):
        resource_name = 'images/audnexus-tag-writer.png'
        pixmap = QPixmap()
        pixmap.loadFromData(self.load_resources([resource_name])[resource_name])
        self.qaction.setIcon(QIcon(pixmap))
        self.qaction.triggered.connect(self.run)

    def run(self):
        db = self.gui.current_db.new_api
        ids = sorted(db.all_book_ids())
        if not ids:
            info_dialog(self.gui, _('No books found'), _('The current Calibre library contains no books.'), show=True)
            return
        self.qaction.setEnabled(False)
        job = ThreadedJob(
            'audnexus-tag-writer-preview',
            _('Preparing audiobook tag preview'),
            build_jobs_in_background,
            args=(db, ids),
            kwargs={},
            callback=Dispatcher(self.preview_ready),
            max_concurrent_count=1,
        )
        self.gui.job_manager.run_threaded_job(job)

    def preview_ready(self, job):
        self.qaction.setEnabled(True)
        if job.failed:
            error_dialog(
                self.gui,
                _('Could not prepare audiobook tag preview'),
                _('The background preparation job stopped unexpectedly. Open Calibre\'s Jobs list for details.'),
                det_msg=job.details,
                show=True,
            )
            return
        jobs, skipped, cancelled = job.result
        if cancelled:
            return
        if not jobs:
            info_dialog(self.gui, _('No audiobook files found'), _('None of the selected books has a managed MP3 or M4B format.'), show=True)
            return
        preview = PreviewDialog(self.gui, jobs, skipped)
        if preview.exec() != QDialog.DialogCode.Accepted:
            return
        self.qaction.setEnabled(False)
        job = ThreadedJob(
            'audnexus-tag-writer',
            _('Updating audiobook metadata'),
            write_jobs_in_background,
            args=(jobs, preview.clear_missing.isChecked()),
            kwargs={},
            callback=Dispatcher(self.job_finished),
            max_concurrent_count=1,
        )
        job.skipped_books = skipped
        self.gui.job_manager.run_threaded_job(job)

    def job_finished(self, job):
        self.qaction.setEnabled(True)
        if job.failed:
            error_dialog(
                self.gui,
                _('Audiobook tag update failed'),
                _('The background update stopped unexpectedly. Open Calibre\'s Jobs list for details.'),
                det_msg=job.details,
                show=True,
            )
            return
        updated, unchanged, failures, cancelled = job.result
        lines = [
            _('Updated: {0} file(s)').format(len(updated)),
            _('Unchanged: {0} file(s)').format(len(unchanged)),
            _('Skipped: {0} book(s)').format(len(job.skipped_books)),
        ]
        if cancelled:
            lines.insert(0, _('Update cancelled after {0} file(s)').format(len(updated)))
        if failures:
            lines.append(_('Failed: {0} file(s)').format(len(failures)))
            lines.extend('{}: {}'.format(path, error) for _book_id, path, error in failures)
        info_dialog(self.gui, _('Audnexus tag update complete'), '<br>'.join(lines), show=True)
