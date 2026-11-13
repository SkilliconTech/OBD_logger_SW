from PySide6.QtCore import Qt, Signal, QTimer, QRect
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QStyledItemDelegate, QStyle
)

from models.pid_directory import get_entries, get_mode_info
from resources.theme import LIGHT
from resources.icons import draw_checked_box

_ID_ROLE = Qt.UserRole


class CheckBoxDelegate(QStyledItemDelegate):
    SIZE = 16
    LEFT_PAD = 28          # space reserved for the checkbox

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        if index.column() == 0 and (index.flags() & Qt.ItemIsUserCheckable):
            size.setWidth(max(size.width() + self.LEFT_PAD, 70))
        return size

    def paint(self, painter, option, index):
        # For non-checkable cells just use the normal painting
        if index.column() != 0 or not (index.flags() & Qt.ItemIsUserCheckable):
            super().paint(painter, option, index)
            return

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # ---- background (hover / selected) ----
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor("#4181EF").lighter(180))
        elif option.state & QStyle.State_MouseOver:
            painter.fillRect(option.rect, QColor("#E7E9F1"))

        # ---- checkbox ----
        state = index.data(Qt.CheckStateRole)
        checked = state in (Qt.Checked, 2)
        box = QRect(
            option.rect.left() + 6,
            option.rect.center().y() - self.SIZE // 2,
            self.SIZE,
            self.SIZE
        )
        if checked:
            draw_checked_box(painter, box, "#4181EF")
        else:
            border = QPen(QColor("#6B7280"))
            border.setWidthF(1.5)
            painter.setPen(border)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(box.adjusted(0, 0, -1, -1), 3, 3)

        # ---- PID text (always to the right of the checkbox) ----
        text = str(index.data(Qt.DisplayRole) or "")
        text_rect = option.rect.adjusted(self.LEFT_PAD, 0, -4, 0)
        painter.setPen(QColor("#1D2631"))
        font = painter.font()
        font.setPointSizeF(10)
        painter.setFont(font)
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, text)

        painter.restore()


class PidPage(QWidget):
    pids_changed = Signal(str, list)

    def __init__(self, mode, parent=None):
        super().__init__(parent)
        self.mode = mode
        self.info = get_mode_info(mode)
        self.entries = get_entries(mode)
        self.table = None
        self._build_ui()
        self.apply_theme(LIGHT)

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
            select_btn = QPushButton("Select all")
            clear_btn = QPushButton("Clear all")
            select_btn.clicked.connect(lambda: self._set_checks(Qt.Checked, False))
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
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 80)
        self.table.setColumnWidth(1, 260)

        self.table.setItemDelegateForColumn(0, CheckBoxDelegate(self.table))

        for row, entry in enumerate(self.entries):
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
        if column != 0:
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

    def _fit_rows(self):
        if self.table is not None:
            QTimer.singleShot(0, self.table.resizeRowsToContents)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_rows()

    def showEvent(self, event):
        super().showEvent(event)
        self._fit_rows()

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
            QTableWidget::indicator {{
                width: 0px;
                height: 0px;
            }}
            QHeaderView::section {{ background-color: {c['bg_panel']};
                color: {c['text_secondary']}; border: none;
                border-bottom: 1px solid {c['border']};
                padding: 6px 8px; font-weight: 600; }}
        """)