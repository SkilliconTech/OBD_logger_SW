from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)

from models.pid_directory import get_entries, get_mode_info
from resources.theme import LIGHT

_ID_ROLE = Qt.UserRole          # raw ID ("0C") stored on the first cell of a row


class PidPage(QWidget):
    """Right-hand page for one mode: heading, search box and a table of IDs.

    Modes 01, 02 and 09 have a checkbox per row. Modes 05, 06 and 08 are a
    read-only reference. Modes 03, 04, 07 and 0A only show a short message.
    """

    pids_changed = Signal(str, list)        # mode code, e.g. ("01", ["0C", "0D"])

    def __init__(self, mode, parent=None):
        super().__init__(parent)
        self.mode = mode
        self.info = get_mode_info(mode)
        self.entries = get_entries(mode)
        self.table = None
        self._build_ui()
        self.apply_theme(LIGHT)

    # ------------------------------------------------------------------ build
    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(10)

        heading = QLabel(f"Mode ${self.mode}: {self.info.name}")
        heading.setObjectName("pidHeading")
        lay.addWidget(heading)

        summary = QLabel(self.info.summary)
        summary.setObjectName("pidSummary")
        summary.setWordWrap(True)
        lay.addWidget(summary)

        if not self.entries:
            note = QLabel("This mode has no PIDs, so there is nothing to select.")
            note.setObjectName("pidNote")
            lay.addWidget(note)
            lay.addStretch(1)
            return

        lay.addLayout(self._build_toolbar())
        self._build_table()
        lay.addWidget(self.table, 1)

        if self.info.note:
            note = QLabel(self.info.note)
            note.setObjectName("pidNote")
            note.setWordWrap(True)
            lay.addWidget(note)

    def _build_toolbar(self):
        row = QHBoxLayout()
        row.setSpacing(8)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search by ID or name...")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._apply_filter)
        row.addWidget(self.search, 1)

        self.count_label = QLabel("")
        self.count_label.setObjectName("pidCount")
        if self.info.selectable:
            select_btn = QPushButton("Select shown")
            clear_btn = QPushButton("Clear all")
            select_btn.clicked.connect(lambda: self._set_checks(Qt.Checked, True))
            clear_btn.clicked.connect(lambda: self._set_checks(Qt.Unchecked, False))
            row.addWidget(select_btn)
            row.addWidget(clear_btn)
            row.addWidget(self.count_label)
        return row

    def _build_table(self):
        selectable = self.info.selectable
        self.table = QTableWidget(len(self.entries), 3)
        self.table.setHorizontalHeaderLabels(
            [self.info.id_label or "ID", "Name", "What it requests"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setShowGrid(False)
        self.table.setWordWrap(True)
        self.table.setTextElideMode(Qt.ElideNone)

        header = self.table.horizontalHeader()
        header.setHighlightSections(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 260)

        for row, entry in enumerate(self.entries):
            # single IDs are shown as "$0C"; ranges and labels are shown as they are
            shown = f"${entry.ident}" if len(entry.ident) <= 2 else entry.ident
            id_item = QTableWidgetItem(shown)
            id_item.setData(_ID_ROLE, entry.ident)
            if selectable:
                id_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
                id_item.setCheckState(Qt.Unchecked)
            else:
                id_item.setFlags(Qt.ItemIsEnabled)

            name_item = QTableWidgetItem(entry.name)
            name_item.setFlags(Qt.ItemIsEnabled)
            desc_item = QTableWidgetItem(entry.description)
            desc_item.setFlags(Qt.ItemIsEnabled)

            self.table.setItem(row, 0, id_item)
            self.table.setItem(row, 1, name_item)
            self.table.setItem(row, 2, desc_item)

        if selectable:
            self.table.itemChanged.connect(self._on_item_changed)
            self.table.cellClicked.connect(self._on_cell_clicked)
            self._update_count()

    # -------------------------------------------------------------- selection
    def checked_pids(self):
        if self.table is None or not self.info.selectable:
            return []
        return [self.table.item(r, 0).data(_ID_ROLE)
                for r in range(self.table.rowCount())
                if self.table.item(r, 0).checkState() == Qt.Checked]

    def _update_count(self):
        if self.info.selectable:
            self.count_label.setText(
                f"{len(self.checked_pids())} of {len(self.entries)} selected")

    def _on_item_changed(self, item):
        if item.column() == 0:
            self._update_count()
            self.pids_changed.emit(self.mode, self.checked_pids())

    def _on_cell_clicked(self, row, column):
        if column != 0:                              # clicking the text ticks too
            id_item = self.table.item(row, 0)
            id_item.setCheckState(
                Qt.Unchecked if id_item.checkState() == Qt.Checked else Qt.Checked)

    def _set_checks(self, state, only_visible):
        self.table.blockSignals(True)
        for r in range(self.table.rowCount()):
            if only_visible and self.table.isRowHidden(r):
                continue
            self.table.item(r, 0).setCheckState(state)
        self.table.blockSignals(False)
        self.table.viewport().update()
        self._update_count()
        self.pids_changed.emit(self.mode, self.checked_pids())

    def _apply_filter(self, text):
        text = text.strip().lower()
        for r in range(self.table.rowCount()):
            haystack = " ".join(
                self.table.item(r, c).text() for c in range(3)).lower()
            self.table.setRowHidden(r, bool(text) and text not in haystack)

    # ------------------------------------------------------------ row heights
    def _fit_rows(self):
        if self.table is not None:
            QTimer.singleShot(0, self.table.resizeRowsToContents)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_rows()

    def showEvent(self, event):
        super().showEvent(event)
        self._fit_rows()

    # ------------------------------------------------------------------ theme
    def apply_theme(self, c):
        self.setStyleSheet(f"""
            QLabel#pidHeading {{ color: {c['text_primary']};
                font-size: 13pt; font-weight: 600; }}
            QLabel#pidSummary, QLabel#pidNote, QLabel#pidCount {{
                color: {c['text_secondary']}; font-size: 10pt; }}
            QLineEdit {{ background-color: {c['list_bg']}; color: {c['text_primary']};
                border: 1px solid {c['btn_border']}; border-radius: 8px;
                padding: 6px 10px; font-size: 10pt; }}
            QLineEdit:focus {{ border: 1px solid {c['accent_blue']}; }}
            QPushButton {{ color: {c['text_primary']}; background-color: {c['btn_bg']};
                border: 1px solid {c['btn_border']}; border-radius: 8px;
                padding: 6px 12px; font-size: 10pt; }}
            QPushButton:hover {{ border: 1px solid {c['accent_blue']}; }}
            QTableWidget {{ background-color: {c['list_bg']};
                color: {c['text_primary']}; border: 1px solid {c['btn_border']};
                border-radius: 10px; outline: 0; font-size: 10pt; }}
            QTableWidget::item {{ padding: 4px 8px; }}
            QTableWidget::item:hover {{ background-color: {c['border']}; }}
            QTableWidget::indicator {{ width: 16px; height: 16px;
                border: 1.5px solid {c['text_secondary']};
                border-radius: 3px; background: transparent; }}
            QTableWidget::indicator:checked {{
                background-color: {c['accent_blue']};
                border: 1.5px solid {c['accent_blue']}; }}
            QHeaderView::section {{ background-color: {c['bg_panel']};
                color: {c['text_secondary']}; border: none;
                border-bottom: 1px solid {c['border']};
                padding: 6px 8px; font-weight: 600; }}
        """)