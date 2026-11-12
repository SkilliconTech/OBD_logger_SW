import os

from PySide6.QtCore import Qt, QSize, QRect, QEvent, QTimer, QUrl
from PySide6.QtGui import (
    QFont, QColor, QAction, QShortcut, QKeySequence, QPainter, QDesktopServices
)
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, QFrame, QListWidget,
    QListWidgetItem, QHBoxLayout, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QFileDialog, QMessageBox, QMenu, QGraphicsDropShadowEffect,
    QStackedWidget, QSizePolicy, QStyledItemDelegate, QStyle
)

from resources.theme import LIGHT, DARK, RADIUS_SM, RADIUS_LG, FONT_FAMILY
from resources.icons import make_theme_icon, trash_pixmap, logo_icon
from views.tree_delegate import ModernTreeDelegate
from views.slide_switch import SlideSwitch
from models.modes import MODES
from views.mode_page import ModePage
from views.mode_tree import ModeTree


APP_TITLE = "OBD Tool"
COMPANY_URL = "https://skillicon.in/"


class NewFileDelegate(QStyledItemDelegate):
    """Row height + trash icon on the selected row of the files list."""
    ROW_HEIGHT = 34
    ICON_SIZE = 15
    ICON_RIGHT_GAP = 14

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        size.setHeight(self.ROW_HEIGHT)
        return size

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect.adjusted(2, 3, -60, -3))

    @classmethod
    def trash_rect(cls, row_rect):
        s = cls.ICON_SIZE
        return QRect(row_rect.right() - cls.ICON_RIGHT_GAP - s,
                     row_rect.center().y() - s // 2 + 1, s, s)

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        if (option.state & QStyle.State_Selected) and index.data(Qt.UserRole):
            painter.save()
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            painter.drawPixmap(self.trash_rect(option.rect), trash_pixmap())
            painter.restore()


class ObdMainWindow(QMainWindow):
    """UI shell only: sidebar (files + tree), top bar, page area, theme.
    No business logic. Hook your own code into the on_* methods."""

    def __init__(self):
        super().__init__()
        self.dark_mode = False
        self.pages = {}              # tree-item name -> page widget
        self._current_page = None
        self.imported_files = []
        self.selected_modes = []
        self.setWindowTitle(APP_TITLE)
        self.resize(1400, 950)
        self._create_actions()

        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self._build_sidebar())
        root_layout.addWidget(self._build_main_area(), 1)

        self.apply_theme()
        self._build_tree()

    # ------------------------------------------------------------------
    # Shortcuts (no toolbar, buttons live in the sidebar)
    # ------------------------------------------------------------------
    def _create_actions(self):
        self.act_new = QAction("New", self)
        self.act_new.setShortcut("Ctrl+N")
        self.act_new.triggered.connect(self.on_new)
        self.act_save = QAction("Save", self)
        self.act_save.setShortcut("Ctrl+S")
        self.act_save.triggered.connect(self.on_save)
        self.act_save_as = QAction("Save As...", self)
        self.act_save_as.setShortcut("Ctrl+Shift+S")
        self.act_save_as.triggered.connect(self.on_save_as)
        for a in (self.act_new, self.act_save, self.act_save_as):
            self.addAction(a)

    # ------------------------------------------------------------------
    # Left sidebar
    # ------------------------------------------------------------------
    def _build_sidebar(self):
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(300)
        self.sidebar.setAttribute(Qt.WA_StyledBackground, True)
        lay = QVBoxLayout(self.sidebar)
        lay.setContentsMargins(20, 24, 20, 24)
        lay.setSpacing(0)

        self.brand_label = QLabel(APP_TITLE)
        f = QFont()
        f.setFamilies(["Segoe UI Variable Display", "Segoe UI", "Arial"])
        f.setPointSizeF(12.5)
        f.setWeight(QFont.DemiBold)
        self.brand_label.setFont(f)
        row = QHBoxLayout()
        row.addWidget(self.brand_label)
        row.addStretch(1)
        lay.addLayout(row)
        lay.addSpacing(14)

        section_font = QFont()
        section_font.setFamilies(["Segoe UI Variable Text", "Segoe UI", "Arial"])
        section_font.setPointSizeF(10.5)
        section_font.setWeight(QFont.DemiBold)
        # ---- Section 1: imported files ----
        self.imported_section = QFrame()
        self.imported_section.setObjectName("importedSection")
        self.imported_section.setAttribute(Qt.WA_StyledBackground, True)
        il = QVBoxLayout(self.imported_section)
        il.setContentsMargins(0, 0, 0, 0)
        il.setSpacing(8)

        self.imported_label = QLabel("IMPORTED FILES")
        self.imported_label.setFont(section_font)
        il.addWidget(self.imported_label)

        self.imported_list = QListWidget()
        self.imported_list.setObjectName("importedList")
        self.imported_list.setUniformItemSizes(True)
        self.imported_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.imported_list.setMinimumHeight(90)
        self.imported_list.setMaximumHeight(120)
        self.imported_list.setItemDelegate(NewFileDelegate(self.imported_list))
        self.imported_list.itemClicked.connect(self.on_file_clicked)
        sc = QShortcut(QKeySequence("Delete"), self.imported_list)
        sc.setContext(Qt.WidgetShortcut)
        sc.activated.connect(self.on_delete_selected_file)
        self._press_item = None
        self._press_was_selected = False
        self.imported_list.viewport().installEventFilter(self)
        il.addWidget(self.imported_list)

        self.new_button = QPushButton("+  New")
        self.new_button.setObjectName("newButton")
        self.new_button.clicked.connect(self.on_new)
        self.save_button = QPushButton("Save")
        self.save_button.setObjectName("saveButton")
        self.save_button.clicked.connect(self.on_save)
        self.save_arrow_button = QPushButton("▾")
        self.save_arrow_button.setObjectName("saveArrowButton")
        self.save_arrow_button.setFixedWidth(30)
        self.save_arrow_button.clicked.connect(self._show_save_menu)
        self._save_menu = QMenu(self)
        self._save_menu.addAction(self.act_save_as)
        self.import_button = QPushButton("Import")
        self.import_button.setObjectName("importButton")
        self.import_button.clicked.connect(self.on_import)
        for b in (self.new_button, self.save_button,
                  self.save_arrow_button, self.import_button):
            b.setCursor(Qt.PointingHandCursor)
            b.setMinimumHeight(40)

        save_group = QHBoxLayout()
        save_group.setSpacing(0)
        save_group.addWidget(self.save_button, 1)
        save_group.addWidget(self.save_arrow_button)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addWidget(self.new_button)
        btn_row.addWidget(self.import_button)
        btn_row.addLayout(save_group)
        il.addLayout(btn_row)
        lay.addWidget(self.imported_section, 0)
        lay.addSpacing(12)

        # ---- Section 2: configuration tree ----
        self.config_section = QFrame()
        self.config_section.setObjectName("configSection")
        self.config_section.setAttribute(Qt.WA_StyledBackground, True)
        cl = QVBoxLayout(self.config_section)
        cl.setContentsMargins(10, 10, 10, 10)
        cl.setSpacing(6)
        self.config_label = QLabel("Modes")
        self.config_label.setFont(section_font)
        cl.addWidget(self.config_label)

        self.new_tree = ModeTree()
        self.new_tree.setHeaderHidden(True)
        self.new_tree.setRootIsDecorated(False)
        self.new_tree.setIndentation(16)
        self.new_tree.setAnimated(True)
        self.new_tree.setExpandsOnDoubleClick(False)
        self.new_tree.setUniformRowHeights(True)
        self.new_tree.setMouseTracking(True)
        self.new_tree.viewport().setAttribute(Qt.WA_Hover, True)
        self.new_tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.new_tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tree_delegate = ModernTreeDelegate(self.new_tree)
        self.new_tree.setItemDelegate(self.tree_delegate)
        self.new_tree.itemClicked.connect(self.on_tree_item_clicked)
        self.new_tree.modes_changed.connect(self.on_modes_changed)
        cl.addWidget(self.new_tree, 1)
        lay.addWidget(self.config_section, 1)
        return self.sidebar

    # ------------------------------------------------------------------
    # Right side: top bar + page area
    # ------------------------------------------------------------------
    def _build_main_area(self):
        self.main_area = QWidget()
        self.main_area.setObjectName("mainArea")
        self.main_area.setAttribute(Qt.WA_StyledBackground, True)
        ml = QVBoxLayout(self.main_area)
        ml.setContentsMargins(24, 12, 24, 12)
        ml.setSpacing(10)

        topbar = QHBoxLayout()
        title_group = QWidget()
        tr = QHBoxLayout(title_group)
        tr.setContentsMargins(0, 0, 0, 0)
        tr.setSpacing(8)
        self.title_label = QLabel(APP_TITLE)
        self.title_label.setFont(QFont(FONT_FAMILY, 21, QFont.Bold))
        self.title_label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        tr.addWidget(self.title_label, 0, Qt.AlignVCenter)

        # optional on/off switch next to the heading (hidden by default)
        self.edit_switch = SlideSwitch()
        self.edit_switch.setToolTip("Switch on to edit this page")
        self.edit_switch.toggled.connect(self.on_edit_switch_toggled)
        self.edit_switch.setVisible(False)
        tr.addWidget(self.edit_switch, 0, Qt.AlignVCenter)

        topbar.addWidget(title_group)
        topbar.addStretch(1)

        self.help_button = QPushButton("?")
        self.help_button.setObjectName("helpButton")
        self.help_button.setFixedSize(42, 42)
        self.help_button.setFont(QFont(FONT_FAMILY, 16, QFont.Bold))
        self.help_button.setCursor(Qt.PointingHandCursor)
        self.help_button.clicked.connect(self.on_help)
        topbar.addWidget(self.help_button)
        topbar.addSpacing(3)

        self.theme_toggle = QPushButton()
        self.theme_toggle.setObjectName("themeToggle")
        self.theme_toggle.setFixedSize(42, 42)
        self.theme_toggle.setCursor(Qt.PointingHandCursor)
        self.theme_toggle.setIconSize(QSize(18, 18))
        self.theme_toggle.clicked.connect(self.toggle_theme)
        topbar.addWidget(self.theme_toggle)
        topbar.addSpacing(4)

        self.brand_btn = QPushButton()
        self.brand_btn.setObjectName("brandButton")
        self.brand_btn.setCursor(Qt.PointingHandCursor)
        self.brand_btn.setFlat(True)
        self.brand_btn.setIcon(logo_icon())
        self.brand_btn.setIconSize(QSize(184, 34))
        self.brand_btn.setToolTip("Visit skillicon.in")
        self.brand_btn.clicked.connect(self.on_logo_clicked)
        topbar.addWidget(self.brand_btn)
        ml.addLayout(topbar)

        self.content_panel = QFrame()
        self.content_panel.setObjectName("contentPanel")
        self.content_panel.setAttribute(Qt.WA_StyledBackground, True)
        self.content_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.content_panel.setMaximumHeight(500)
        pl = QVBoxLayout(self.content_panel)
        pl.setContentsMargins(12, 10, 12, 10)

        self.content_stack = QStackedWidget()
        self.content_stack.setVisible(False)      # empty until a page is opened
        pl.addWidget(self.content_stack)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(16, 24, 40, 40))
        self.content_panel.setGraphicsEffect(shadow)
        ml.addWidget(self.content_panel, 1)
        return self.main_area

    # ------------------------------------------------------------------
    # Tree + pages  (EDIT THIS to define your own OBD sections)
    # ------------------------------------------------------------------
    def add_page(self, name, widget):
        """Register a page. 'name' must match a tree item text."""
        self.pages[name] = widget
        self.content_stack.addWidget(widget)

    def _build_tree(self):
        """Modes list: one checkbox row and one page per mode."""
        self.new_tree.add_modes(MODES)
        for code in MODES:
            self.add_page(f"Mode {code}", ModePage(code))

    def on_modes_changed(self, modes):
        self.selected_modes = modes                  # e.g. ["01", "05"]
        self.statusBar().showMessage(
            "Selected modes: " + (", ".join(modes) or "none"), 3000)
    def on_tree_item_clicked(self, item, column):
        if item.childCount() > 0:                    # parent row: expand/collapse
            item.setExpanded(not item.isExpanded())
            return
        name = item.text(0)
        if name == "Generate Report":                # action item, opens no page
            self.on_generate()
            return
        page = self.pages.get(name)
        if page is None:
            return
        self._current_page = name
        self.title_label.setText(name)
        self.content_stack.setVisible(True)
        self.content_stack.setCurrentWidget(page)

    def clear_page_area(self):
        """Empty right-hand side (no page open)."""
        self._current_page = None
        self.title_label.setText(APP_TITLE)
        self.edit_switch.setVisible(False)
        self.content_stack.setVisible(False)
        self.new_tree.clearSelection()

    # ------------------------------------------------------------------
    # Files list behaviour (UI only)
    # ------------------------------------------------------------------
    def _add_file_row(self, path):
        item = QListWidgetItem(os.path.basename(path))
        item.setData(Qt.UserRole, path)
        self.imported_list.addItem(item)
        self.imported_list.setCurrentItem(item)
        self.imported_files.append(path)

    def on_file_clicked(self, item):
        # load your file here, then:
        self.clear_page_area()
        self.statusBar().showMessage(f"Opened {item.text()}", 3000)

    def on_delete_selected_file(self):
        item = self.imported_list.currentItem()
        if item is None:
            return
        path = item.data(Qt.UserRole)
        name = os.path.basename(path) if path else item.text()
        if QMessageBox.question(
                self, "Remove file", f"Remove '{name}' from the list?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        ) != QMessageBox.Yes:
            return
        self.imported_list.takeItem(self.imported_list.row(item))
        if path in self.imported_files:
            self.imported_files.remove(path)
        self.clear_page_area()          # right side empty until another file is picked
        self.statusBar().showMessage(f"Removed '{name}'", 3000)

    def eventFilter(self, obj, event):
        """Click on the trash icon of the selected row removes the file."""
        if obj is self.imported_list.viewport():
            if event.type() == QEvent.MouseButtonPress:
                self._press_item = self.imported_list.itemAt(event.position().toPoint())
                self._press_was_selected = bool(
                    self._press_item and self._press_item.isSelected())
            elif event.type() == QEvent.MouseButtonRelease:
                pos = event.position().toPoint()
                item = self.imported_list.itemAt(pos)
                if (item is not None and item is self._press_item
                        and self._press_was_selected and item.data(Qt.UserRole)):
                    rect = NewFileDelegate.trash_rect(
                        self.imported_list.visualItemRect(item))
                    if rect.contains(pos):
                        QTimer.singleShot(0, self.on_delete_selected_file)
        return super().eventFilter(obj, event)

    # ------------------------------------------------------------------
    # Button handlers: put your own logic here
    # ------------------------------------------------------------------
    def on_new(self):
        self.statusBar().showMessage("New (add your code)", 3000)

    def on_save(self):
        self.statusBar().showMessage("Save (add your code)", 3000)

    def on_save_as(self):
        self.statusBar().showMessage("Save As (add your code)", 3000)

    def on_import(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import", "", "All files (*)")
        if path:
            self._add_file_row(path)

    def on_generate(self):
        self.statusBar().showMessage("Generate (add your code)", 3000)

    def on_edit_switch_toggled(self, on):
        pass

    def on_help(self):
        QMessageBox.information(self, "Help", "Add your help text here.")

    def on_logo_clicked(self):
        QDesktopServices.openUrl(QUrl(COMPANY_URL))

    def _show_save_menu(self):
        self._save_menu.exec(self.save_arrow_button.mapToGlobal(
            self.save_arrow_button.rect().bottomLeft()))

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------
    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    def apply_theme(self):
        c = DARK if self.dark_mode else LIGHT
        self.sidebar.setStyleSheet(
            f"#sidebar {{ background-color: {c['bg_panel']};"
            f" border-right: 1px solid {c['border']}; }}")
        self.brand_label.setStyleSheet(f"color: {c['text_primary']};")
        self.imported_label.setStyleSheet(
            f"color: {c['text_secondary']}; font-size: 9pt; font-weight: 700;")
        self.config_label.setStyleSheet(
            f"color: {c['text_primary']}; font-weight: 600;")

        self.imported_section.setStyleSheet(f"""
            #importedSection {{ background: transparent; border: none; }}
            QPushButton {{
                color: {c['text_primary']}; background-color: {c['btn_bg']};
                border: 1px solid {c['btn_border']}; border-radius: 12px;
                padding: 0 14px; }}
            QPushButton:hover {{ border: 1px solid {c['accent_blue']}; }}
            QPushButton:pressed {{ background-color: {c['border']}; }}
            QPushButton#newButton {{
                background-color: {c['bg_main']}; border: 1px solid {c['border']};
                font-family: "Segoe UI"; font-size: 10pt; font-weight: 400; }}
            QPushButton#newButton:hover {{ border: 1px solid {c['accent_blue']}; }}
            QPushButton#saveButton, QPushButton#importButton {{
                font-family: "Segoe UI"; font-size: 9pt; font-weight: 700; }}
            QPushButton#saveButton {{
                padding: 0 8px; border-top-right-radius: 0px;
                border-bottom-right-radius: 0px; }}
            QPushButton#saveArrowButton {{
                padding: 0px; font-size: 11pt; font-weight: 700; border-left: none;
                border-top-left-radius: 0px; border-bottom-left-radius: 0px; }}
            QPushButton#saveArrowButton:hover {{
                border: 1px solid {c['accent_blue']}; border-left: none; }}
        """)
        self._save_menu.setStyleSheet(f"""
            QMenu {{ background-color: {c['bg_panel']}; color: {c['text_primary']};
                     border: 1px solid {c['btn_border']}; padding: 6px; }}
            QMenu::item {{ padding: 8px 28px 8px 14px; border-radius: 6px;
                           font-size: 11pt; }}
            QMenu::item:selected {{ background-color: {c['accent_blue']};
                                    color: #FFFFFF; }}
        """)
        self.config_section.setStyleSheet(
            f"#configSection {{ background-color: {c['bg_main']};"
            f" border: 2px solid {c['border']}; border-radius: {RADIUS_LG}px; }}")
        self.main_area.setStyleSheet(
            f"#mainArea {{ background-color: {c['bg_main']}; }}")
        self.title_label.setStyleSheet(f"color: {c['text_primary']};")
        self.edit_switch.set_colors(c['accent_blue'], c['btn_border'], "#FFFFFF")

        for name in ("themeToggle", "helpButton"):
            w = self.theme_toggle if name == "themeToggle" else self.help_button
            extra = f"color: {c['text_primary']};" if name == "helpButton" else ""
            w.setStyleSheet(f"""
                #{name} {{ background-color: {c['bg_panel']}; {extra}
                           border: 1px solid {c['border']};
                           border-radius: {RADIUS_SM}px; }}
                #{name}:hover {{ border: 1px solid {c['accent_blue']}; }}
            """)
        self.brand_btn.setStyleSheet("""
            #brandButton { background-color: transparent; border: none;
                           padding: 6px 12px; }
            #brandButton:hover, #brandButton:pressed {
                background-color: transparent; border: none; }
        """)
        self.theme_toggle.setIcon(make_theme_icon(self.dark_mode, c["toggle_icon"]))

        self.content_panel.setStyleSheet(
            f"#contentPanel {{ background-color: {c['bg_panel']};"
            f" border: 1px solid {c['border']}; border-radius: {RADIUS_LG}px; }}")
        self.imported_list.setStyleSheet(f"""
            QListWidget {{ background-color: {c['list_bg']};
                border: 1px solid {c['btn_border']}; border-radius: {RADIUS_LG}px;
                outline: 0; padding: 3px; font-size: 11pt; }}
            QListWidget::item {{ color: {c['text_primary']}; border-radius: 5px;
                padding: 0px 40px 0px 12px; }}
            QListWidget::item:hover {{ background-color: {c['border']}; }}
            QListWidget::item:selected {{ background-color: {c['accent_blue']};
                color: #FFFFFF; }}
        """)
        self.new_tree.setStyleSheet(
            "QTreeWidget { background-color: transparent; border: none; outline: 0; }")
        self.tree_delegate.set_colors(c)
        self.new_tree.viewport().update()
        self.statusBar().setStyleSheet(
            f"QStatusBar {{ background-color: {c['bg_panel']};"
            f" color: {c['text_secondary']}; }}")