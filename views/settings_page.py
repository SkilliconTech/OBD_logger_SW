from PySide6.QtCore import Qt, Signal, QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QComboBox, QLineEdit,
    QSpinBox, QPushButton
)

from models import config_rules as R
from models.logger_config import LoggerConfig
from resources.theme import LIGHT
from services.config_validator import validate

_FIELDS = ("bitrate", "address_bits", "tx_id", "rx_id",
           "startup_delay_ms", "run_duration_ms", "response_timeout_ms")


class SettingsPage(QWidget):
    """The logger settings that go into config.json (everything except the requests).

    Whenever a value changes it emits a LoggerConfig that carries the settings."""

    settings_changed = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._loading = False

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(12)

        heading = QLabel("Settings")
        heading.setObjectName("settingsHeading")
        lay.addWidget(heading)
        hint = QLabel("These values go into config.json. Changes are saved automatically.")
        hint.setObjectName("settingsHint")
        lay.addWidget(hint)

        self.bitrate = QComboBox()
        for rate in R.BITRATES:
            self.bitrate.addItem(f"{rate // 1000} kbit/s", rate)
        self.address_bits = QComboBox()
        for bits in R.ADDRESS_BITS:
            self.address_bits.addItem(f"{bits}-bit", bits)

        self.tx_id = QLineEdit()
        self.rx_id = QLineEdit()
        for edit in (self.tx_id, self.rx_id):
            edit.setMaxLength(8)
            edit.setFixedWidth(160)
            edit.setValidator(QRegularExpressionValidator(
                QRegularExpression("[0-9A-Fa-f]*"), edit))

        self.startup_delay = self._spin(R.STARTUP_DELAY_MS[0], R.STARTUP_DELAY_MS[1], 100)
        self.run_duration = self._spin(0, R.RUN_DURATION_MS[1], 1000)
        self.run_duration.setSpecialValueText("0 (run continuously)")
        self.response_timeout = self._spin(R.RESPONSE_TIMEOUT_MS[0], R.RESPONSE_TIMEOUT_MS[1], 10)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setHorizontalSpacing(24)
        form.setVerticalSpacing(12)
        form.addRow("Bitrate", self.bitrate)
        form.addRow("Address bits", self.address_bits)
        form.addRow("Transmit ID (tx_id)", self.tx_id)
        form.addRow("Receive ID (rx_id)", self.rx_id)
        form.addRow("Startup delay", self.startup_delay)
        form.addRow("Run duration", self.run_duration)
        form.addRow("Response timeout", self.response_timeout)
        lay.addLayout(form)

        self.problems = QLabel("")
        self.problems.setObjectName("settingsProblems")
        self.problems.setWordWrap(True)
        lay.addWidget(self.problems)

        reset = QPushButton("Reset to defaults")
        reset.setObjectName("resetButton")
        reset.setFixedWidth(160)
        reset.clicked.connect(self._reset)
        lay.addWidget(reset)
        lay.addStretch(1)

        self.bitrate.currentIndexChanged.connect(self._on_changed)
        self.address_bits.currentIndexChanged.connect(self._on_address_bits_changed)
        self.tx_id.textChanged.connect(lambda text: self._on_id_edited(self.tx_id, text))
        self.rx_id.textChanged.connect(lambda text: self._on_id_edited(self.rx_id, text))
        for box in (self.startup_delay, self.run_duration, self.response_timeout):
            box.valueChanged.connect(self._on_changed)

        self.set_settings(LoggerConfig())
        self.apply_theme(LIGHT)

    @staticmethod
    def _spin(low, high, step):
        box = QSpinBox()
        box.setRange(low, high)
        box.setSingleStep(step)
        box.setSuffix(" ms")
        box.setFixedWidth(200)
        return box

    # ------------------------------------------------------------------ data
    def current_settings(self):
        return LoggerConfig(
            bitrate=self.bitrate.currentData(),
            address_bits=self.address_bits.currentData(),
            tx_id=self.tx_id.text(),
            rx_id=self.rx_id.text(),
            startup_delay_ms=self.startup_delay.value(),
            run_duration_ms=self.run_duration.value(),
            response_timeout_ms=self.response_timeout.value(),
        )

    def set_settings(self, config):
        """Show the settings of a LoggerConfig (also used later when importing)."""
        self._loading = True
        self.bitrate.setCurrentIndex(max(0, self.bitrate.findData(config.bitrate)))
        self.address_bits.setCurrentIndex(
            max(0, self.address_bits.findData(config.address_bits)))
        self.tx_id.setText(str(config.tx_id))
        self.rx_id.setText(str(config.rx_id))
        self.startup_delay.setValue(config.startup_delay_ms)
        self.run_duration.setValue(config.run_duration_ms)
        self.response_timeout.setValue(config.response_timeout_ms)
        self._loading = False
        self._show_problems(self.current_settings())

    def _show_problems(self, settings):
        issues = [i for i in validate(settings) if i.field in _FIELDS]
        if issues:
            self.problems.setText("<br>".join(
                f"<b>{i.field}</b>: {i.message} {i.fix}" for i in issues))
        else:
            self.problems.setText("")

    # ---------------------------------------------------------------- events
    def _on_changed(self, *args):
        if self._loading:
            return
        settings = self.current_settings()
        self._show_problems(settings)
        self.settings_changed.emit(settings)

    def _on_id_edited(self, edit, text):
        upper = text.upper()
        if upper != text:
            edit.setText(upper)              # triggers this handler again
            return
        self._on_changed()

    def _on_address_bits_changed(self, index):
        if self._loading:
            return
        bits = self.address_bits.currentData()
        other = R.FUNCTIONAL_IDS[29 if bits == 11 else 11]
        if self.tx_id.text().upper() == other and self.rx_id.text() in ("", "0"):
            self.tx_id.setText(R.FUNCTIONAL_IDS[bits])    # keep the usual broadcast ID
            self.rx_id.setText("0")
        self._on_changed()

    def _reset(self):
        self.set_settings(LoggerConfig())
        self._on_changed()

    # ------------------------------------------------------------------ theme
    def apply_theme(self, c):
        self.setStyleSheet(f"""
            QLabel#settingsHeading {{ color: {c['text_primary']};
                font-size: 13pt; font-weight: 600; }}
            QLabel#settingsHint {{ color: {c['text_secondary']}; font-size: 10pt; }}
            QLabel#settingsProblems {{ color: #D64545; font-size: 10pt; }}
            QLabel {{ color: {c['text_primary']}; font-size: 10.5pt; }}
            QComboBox, QLineEdit, QSpinBox {{ color: {c['text_primary']};
                background-color: {c['list_bg']}; border: 1px solid {c['btn_border']};
                border-radius: 8px; padding: 5px 10px; font-size: 10.5pt; }}
            QComboBox:focus, QLineEdit:focus, QSpinBox:focus {{
                border: 1px solid {c['accent_blue']}; }}
            QComboBox QAbstractItemView {{ color: {c['text_primary']};
                background-color: {c['list_bg']}; }}
            QPushButton#resetButton {{ color: {c['text_primary']};
                background-color: {c['btn_bg']}; border: 1px solid {c['btn_border']};
                border-radius: 8px; padding: 7px 12px; font-size: 10pt; }}
            QPushButton#resetButton:hover {{ border: 1px solid {c['accent_blue']}; }}
        """)