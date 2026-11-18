"""
PyQt6-интерфейс АРМ «Спортивный организатор».
Бизнес-правила и хранение данных остаются в database.py.
"""

import datetime
import os
import sqlite3
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush, QFont, QIcon, QPainter, QPen, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication, QAbstractItemView, QCheckBox, QComboBox, QDialog,
    QDialogButtonBox, QFormLayout, QFrame, QGraphicsScene, QGraphicsView,
    QGridLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QPushButton, QRadioButton, QScrollArea,
    QSizePolicy, QSplitter, QStackedWidget, QTabWidget, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget, QFileDialog
)

import database as dbm
from database import (
    APP_STATUS, MATCH_STATUS, ROLE_COACH, ROLE_ORG, SYSTEM_NAMES,
    TOURNAMENT_STATUS, ValidationError, fmt_date
)

ICON_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.png")

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sport_arm.db")
POSITIONS = [
    "Связующий", "Диагональный", "Доигровщик",
    "Центральный блокирующий", "Либеро"
]
POSITION_PLACEHOLDER = "Выберите амплуа"
POSITION_OPTIONS = [POSITION_PLACEHOLDER] + POSITIONS
SYSTEM_BY_LABEL = {value: key for key, value in SYSTEM_NAMES.items()}


def selected_player_position(value):
    """Не принимает произвольный текст или пропущенное амплуа."""
    if value not in POSITIONS:
        raise ValidationError("Выберите амплуа игрока из выпадающего списка.")
    return value


APP_STYLE = """
QWidget {
    color: #263449;
    font-family: "Segoe UI";
    font-size: 10pt;
    font-weight: 400;
    background-color: #f4f6f9;
}
QMainWindow, QDialog { background-color: #f4f6f9; }
QLabel {
    color: #263449;
    background: transparent;
    border: none;
    font-weight: 400;
}
QLabel#SidebarBrand { color: #ffffff; font-size: 16pt; font-weight: 600; }
QLabel#SidebarSub { color: #aab8ca; font-size: 8pt; }
QLabel#SidebarSection {
    color: #9aacc2; font-size: 8pt; font-weight: 600;
    padding: 14px 10px 5px 10px;
}
QFrame#Sidebar { background-color: #17263b; border: none; }
QPushButton#NavButton {
    background: transparent; color: #c3cedc; text-align: left;
    border: none; border-radius: 7px; padding: 10px 13px;
    margin: 1px 0; font-weight: 500;
}
QPushButton#NavButton:hover { background-color: #243851; color: #ffffff; }
QPushButton#NavActive {
    background-color: #2b4668; color: #ffffff; text-align: left;
    border: none; border-left: 3px solid #4d8be8;
    border-radius: 7px; padding: 10px 10px; margin: 1px 0;
    font-weight: 600;
}
QFrame#ProfileCard {
    background-color: #20334d; border: none; border-radius: 9px;
}
QLabel#ProfileName { color: #ffffff; font-weight: 600; }
QLabel#ProfileRole { color: #afbdd0; font-size: 8pt; }
QFrame#Workspace { background-color: #f4f6f9; border: none; }
QFrame#Topbar {
    background-color: #ffffff; border: none;
    border-bottom: 1px solid #e5e9ef;
}
QLabel#PageTitle { color: #18273b; font-size: 19pt; font-weight: 600; }
QLabel#PageSubtitle { color: #78869a; font-size: 9pt; }
QLabel#Muted { color: #77869a; }
QFrame#Surface, QFrame#MetricCard, QGroupBox {
    background-color: #ffffff; border: 1px solid #e6eaf0;
    border-radius: 10px;
}
QFrame#MetricCard { min-height: 104px; }
QLabel#MetricValue { color: #1e3554; font-size: 23pt; font-weight: 600; }
QLabel#MetricTitle { color: #53647a; font-size: 9pt; font-weight: 600; }
QLabel#MetricHint { color: #8996a8; font-size: 8pt; }
QGroupBox {
    margin-top: 12px; padding: 14px 10px 10px 10px;
    font-weight: 600; color: #38485e;
}
QGroupBox::title {
    subcontrol-origin: margin; left: 12px; padding: 0 5px; color: #53647a;
}
QPushButton {
    background-color: #ffffff; color: #30425a;
    border: 1px solid #dfe5ed; border-radius: 7px;
    padding: 8px 13px; min-height: 20px; font-weight: 500;
}
QPushButton:hover { background-color: #f1f5fa; border-color: #cbd6e4; }
QPushButton:pressed { background-color: #e8eef6; }
QPushButton:disabled {
    background-color: #f1f3f6; color: #a0aab7; border-color: #e5e8ed;
}
QPushButton#Primary {
    background-color: #2864c8; color: #ffffff;
    border: 1px solid #2864c8; font-weight: 600;
}
QPushButton#Primary:hover { background-color: #2057b4; }
QPushButton#Danger {
    background-color: #fff7f7; color: #b84650; border: 1px solid #f0dddd;
}
QPushButton#Danger:hover { background-color: #ffeded; }
QLineEdit, QComboBox {
    background-color: #ffffff; color: #263449;
    border: 1px solid #dce3ec; border-radius: 7px;
    padding: 8px 10px; min-height: 22px;
    selection-background-color: #dce9fb; selection-color: #1a2b42;
}
QLineEdit:hover, QComboBox:hover { border-color: #becbda; }
QLineEdit:focus, QComboBox:focus { border: 1px solid #6d9de2; }
QTabWidget::pane {
    background-color: #ffffff; border: 1px solid #e3e8ef;
    border-radius: 8px; top: -1px;
}
QTabBar::tab {
    background-color: #eef2f7; color: #65748a; padding: 10px 16px;
    margin-right: 4px; border: none; border-top-left-radius: 6px;
    border-top-right-radius: 6px; font-weight: 500;
}
QTabBar::tab:selected {
    background-color: #ffffff; color: #245db6; font-weight: 600;
}
QTableWidget {
    background-color: #ffffff; alternate-background-color: #f8fafc;
    color: #263449; border: 1px solid #e3e8ef; border-radius: 8px;
    gridline-color: transparent; selection-background-color: #e5eefb;
    selection-color: #20334c; outline: none;
}
QHeaderView::section {
    background-color: #f0f3f7; color: #56667c;
    padding: 10px 8px; border: none; border-bottom: 1px solid #e1e6ed;
    font-weight: 600;
}
QTableWidget::item { padding: 7px; border: none; }
QCheckBox, QRadioButton { spacing: 7px; color: #53647a; }
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: transparent; width: 9px; margin: 2px; }
QScrollBar::handle:vertical {
    background-color: #cbd4df; min-height: 26px; border-radius: 4px;
}
QScrollBar::handle:vertical:hover { background-color: #aebbc9; }
QStatusBar {
    background-color: #ffffff; color: #78869a;
    border-top: 1px solid #e6eaf0;
}
QToolTip {
    background-color: #20334d; color: #ffffff; border: none; padding: 5px 8px;
}
QFrame#AuthShell {
    background-color: #ffffff; border: 1px solid #e3e8ef; border-radius: 14px;
}
QFrame#AuthHero {
    background-color: #203650; border: none; border-radius: 10px;
}
QLabel#AuthEyebrow { color: #b5c6dc; font-size: 8pt; font-weight: 600; }
QLabel#AuthHeroTitle { color: #ffffff; font-size: 25pt; font-weight: 600; }
QLabel#AuthHeroText { color: #d0dbe8; font-size: 10pt; }
QFrame#AuthFeature { background-color: #2a435e; border: none; border-radius: 7px; }
QLabel#AuthFeatureIcon {
    background-color: #3c6696; color: #ffffff; border-radius: 6px;
    font-size: 11pt; font-weight: 600;
}
QLabel#AuthFeatureTitle { color: #ffffff; font-weight: 600; }
QLabel#AuthFeatureText { color: #c2d0df; font-size: 8pt; }
QFrame#AuthPanel { background-color: #ffffff; border: none; }
QLabel#AuthTitle { color: #1c2d44; font-size: 20pt; font-weight: 600; }
QLabel#AuthSubtitle { color: #77869a; font-size: 9pt; }
QLabel#FormError { color: #b84650; font-weight: 500; }
"""


def info(parent, title, message):
    QMessageBox.information(parent, title, message)


def warn(parent, title, message):
    QMessageBox.warning(parent, title, message)


def confirm(parent, title, message):
    return QMessageBox.question(
        parent, title, message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No
    ) == QMessageBox.StandardButton.Yes


def make_button(text, callback, role="normal"):
    button = QPushButton(text)
    if role == "primary":
        button.setObjectName("Primary")
    elif role == "danger":
        button.setObjectName("Danger")
    button.clicked.connect(callback)
    return button


class DataTable(QTableWidget):
    """Таблица с выбором строк и хранением ID записи в UserRole."""

    def __init__(self, headers, parent=None, widths=None, height=None):
        super().__init__(0, len(headers), parent)
        self.setHorizontalHeaderLabels(headers)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.setWordWrap(False)
        self.setSortingEnabled(False)
        if widths:
            for i, width in enumerate(widths):
                self.setColumnWidth(i, width)
        if height:
            self.setMinimumHeight(height)

    def fill(self, rows):
        selected = self.selected_id()
        self.setRowCount(0)
        for record_id, values, tags in rows:
            row = self.rowCount()
            self.insertRow(row)
            for col, value in enumerate(values):
                item = QTableWidgetItem("" if value is None else str(value))
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, record_id)
                if col in (0,) and len(values) > 1:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
                    )
                if "mine" in tags:
                    item.setBackground(QBrush(QColor("#fef3c7")))
                elif "played" in tags:
                    item.setForeground(QBrush(QColor("#15803d")))
                elif "bad" in tags:
                    item.setForeground(QBrush(QColor("#b91c1c")))
                elif "warn" in tags:
                    item.setForeground(QBrush(QColor("#b45309")))
                elif "muted" in tags:
                    item.setForeground(QBrush(QColor("#94a3b8")))
                self.setItem(row, col, item)
        if selected is not None:
            for row in range(self.rowCount()):
                item = self.item(row, 0)
                if item and item.data(Qt.ItemDataRole.UserRole) == selected:
                    self.selectRow(row)
                    break

    def selected_id(self):
        row = self.currentRow()
        if row < 0:
            return None
        item = self.item(row, 0)
        if item is None:
            return None
        value = item.data(Qt.ItemDataRole.UserRole)
        try:
            return int(value)
        except (TypeError, ValueError):
            return None


class FormDialog(QDialog):
    """Универсальная форма. Проверку и запись выполняет переданная функция submit."""

    def __init__(self, parent, title, fields, submit, initial=None, hint=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(440)
        self.submit = submit
        self.widgets = {}
        initial = initial or {}

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 18)
        root.setSpacing(12)

        if hint:
            label = QLabel(hint)
            label.setObjectName("Muted")
            label.setWordWrap(True)
            root.addWidget(label)

        form = QFormLayout()
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(10)
        for field in fields:
            key = field["key"]
            kind = field.get("kind", "entry")
            if kind in ("combo", "combo_free"):
                widget = QComboBox()
                widget.addItems(field.get("values", []))
                if kind == "combo_free":
                    widget.setEditable(True)
                if key in initial:
                    index = widget.findText(str(initial[key]))
                    if index >= 0:
                        widget.setCurrentIndex(index)
                    else:
                        widget.setCurrentText(str(initial[key]))
                elif field.get("default") is not None:
                    widget.setCurrentText(str(field["default"]))
            else:
                widget = QLineEdit()
                widget.setText(str(initial.get(key, field.get("default", ""))))
                if field.get("show"):
                    widget.setEchoMode(QLineEdit.EchoMode.Password)
                if field.get("placeholder"):
                    widget.setPlaceholderText(field["placeholder"])
            widget.setMinimumWidth(245)
            form.addRow(field["label"], widget)
            self.widgets[key] = widget
        root.addLayout(form)

        self.error = QLabel("")
        self.error.setStyleSheet("color: #b91c1c;")
        self.error.setWordWrap(True)
        root.addWidget(self.error)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Save
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Сохранить")
        buttons.button(QDialogButtonBox.StandardButton.Save).setObjectName("Primary")
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self._submit)
        root.addWidget(buttons)

    def values(self):
        result = {}
        for key, widget in self.widgets.items():
            if isinstance(widget, QComboBox):
                result[key] = widget.currentText().strip()
            else:
                result[key] = widget.text().strip()
        return result

    def _submit(self):
        try:
            self.submit(self.values())
        except (ValidationError, sqlite3.Error, OSError) as exc:
            self.error.setText(str(exc))
            return
        self.accept()


def show_form(parent, title, fields, submit, initial=None, hint=None):
    dialog = FormDialog(parent, title, fields, submit, initial, hint)
    return dialog.exec() == QDialog.DialogCode.Accepted


class VolleyballResultDialog(QDialog):
    """Диалог ввода счёта каждой партии волейбольного матча."""

    def __init__(self, parent, team1, team2, submit, initial_sets=None):
        super().__init__(parent)
        self.setWindowTitle("Протокол волейбольного матча")
        self.setModal(True)
        self.setMinimumWidth(520)
        self.submit_result = submit
        self.inputs = []
        initial_sets = initial_sets or []

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 18)
        root.setSpacing(12)

        title = QLabel(f"{team1}  —  {team2}")
        title.setStyleSheet("font-size: 13pt; font-weight: 700; color: #1c2d44;")
        title.setWordWrap(True)
        root.addWidget(title)

        hint = QLabel(
            "Первые четыре партии играются до 25 очков, пятая — до 15. "
            "В каждой партии нужна разница минимум в 2 очка. "
            "Матч выигрывает команда, первой взявшая три партии."
        )
        hint.setObjectName("Muted")
        hint.setWordWrap(True)
        root.addWidget(hint)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(8)
        headers = [
            QLabel("Партия"),
            QLabel(team1),
            QLabel(team2)
        ]
        for column, label in enumerate(headers):
            label.setStyleSheet("font-weight: 700; color: #52647b;")
            label.setWordWrap(True)
            grid.addWidget(label, 0, column)

        for index in range(5):
            number = index + 1
            set_label = QLabel(
                f"{number}-я" if number < 5 else "5-я (тай-брейк)"
            )
            set_label.setStyleSheet("font-weight: 600; color: #30425a;")
            left = QLineEdit()
            right = QLineEdit()
            left.setAlignment(Qt.AlignmentFlag.AlignCenter)
            right.setAlignment(Qt.AlignmentFlag.AlignCenter)
            left.setPlaceholderText("25" if number < 5 else "15")
            right.setPlaceholderText("25" if number < 5 else "15")
            left.setMaximumWidth(115)
            right.setMaximumWidth(115)
            if index < len(initial_sets):
                left.setText(str(initial_sets[index][0]))
                right.setText(str(initial_sets[index][1]))
            grid.addWidget(set_label, index + 1, 0)
            grid.addWidget(left, index + 1, 1)
            grid.addWidget(right, index + 1, 2)
            self.inputs.append((left, right))
        root.addLayout(grid)

        self.error = QLabel("")
        self.error.setObjectName("FormError")
        self.error.setWordWrap(True)
        root.addWidget(self.error)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Save
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Сохранить результат")
        buttons.button(QDialogButtonBox.StandardButton.Save).setObjectName("Primary")
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self._submit)
        root.addWidget(buttons)

    def _submit(self):
        scores = []
        found_empty = False
        for index, (left, right) in enumerate(self.inputs, start=1):
            value1, value2 = left.text().strip(), right.text().strip()
            if not value1 and not value2:
                found_empty = True
                continue
            if not value1 or not value2:
                self.error.setText(f"Заполните оба счёта для {index}-й партии.")
                return
            if found_empty:
                self.error.setText(
                    "Заполняйте партии подряд. Нельзя пропускать партию между сыгранными."
                )
                return
            scores.append((value1, value2))
        try:
            self.submit_result(scores)
        except (ValidationError, sqlite3.Error, OSError, ValueError) as exc:
            self.error.setText(str(exc))
            return
        self.accept()


class TournamentSelector(QWidget):
    def __init__(self, db, changed=None, parent=None, label="Турнир:"):
        super().__init__(parent)
        self.db = db
        self.changed = changed
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 8)
        title = QLabel(label)
        title.setStyleSheet("font-weight: 700;")
        self.combo = QComboBox()
        self.combo.setMinimumWidth(300)
        row.addWidget(title)
        row.addWidget(self.combo)
        row.addStretch(1)
        self.combo.currentIndexChanged.connect(self._changed)

    def _changed(self):
        if self.changed:
            self.changed()

    def reload(self, status=None):
        current = self.selected_id()
        rows = self.db.list_tournaments(status)
        self.combo.blockSignals(True)
        self.combo.clear()
        for tournament in rows:
            self.combo.addItem(tournament["name"], tournament["id"])
        index = self.combo.findData(current)
        if index >= 0:
            self.combo.setCurrentIndex(index)
        self.combo.blockSignals(False)
        if self.changed:
            self.changed()

    def selected_id(self):
        value = self.combo.currentData()
        return int(value) if value is not None else None


class BaseTab(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.db = app.db
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 22, 24, 22)
        self.layout.setSpacing(14)

    def title(self, text, hint=None):
        # Заголовок и описание раздела уже находятся в общей верхней панели.
        # Не дублируем их в рабочей области.
        return

    def toolbar(self, *buttons):
        row = QHBoxLayout()
        row.setSpacing(8)
        for button in buttons:
            row.addWidget(button)
        row.addStretch(1)
        self.layout.addLayout(row)

    def run(self, callback, *args, success=None, refresh=True):
        try:
            callback(*args)
        except (ValidationError, sqlite3.Error, OSError) as exc:
            warn(self, "Не удалось выполнить действие", str(exc))
            return False
        if refresh:
            self.app.refresh_all()
        if success:
            self.app.notify(success)
        return True

    def refresh(self):
        pass


class LoginPage(QWidget):
    """Чистый экран входа и регистрации без декоративных эффектов на тексте."""

    def __init__(self, app):
        super().__init__()
        self.app = app
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)

        shell = QFrame()
        shell.setObjectName("AuthShell")
        shell_layout = QHBoxLayout(shell)
        shell_layout.setContentsMargins(12, 12, 12, 12)
        shell_layout.setSpacing(12)

        hero = QFrame()
        hero.setObjectName("AuthHero")
        hero.setMinimumWidth(340)
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(30, 30, 30, 26)
        hero_layout.setSpacing(14)

        brand = QLabel("SPORT ARM")
        brand.setStyleSheet("color: #ffffff; font-size: 15pt; font-weight: 600;")
        hero_layout.addWidget(brand)
        eyebrow = QLabel("УПРАВЛЕНИЕ ВОЛЕЙБОЛЬНЫМИ СОРЕВНОВАНИЯМИ")
        eyebrow.setObjectName("AuthEyebrow")
        eyebrow.setWordWrap(True)
        hero_layout.addSpacing(20)
        hero_layout.addWidget(eyebrow)

        hero_title = QLabel("Всё для турнира.\nВ одном месте.")
        hero_title.setObjectName("AuthHeroTitle")
        hero_title.setWordWrap(True)
        hero_layout.addWidget(hero_title)
        hero_text = QLabel(
            "Организуйте соревнования, ведите команды и составы, "
            "планируйте матчи и контролируйте результаты."
        )
        hero_text.setObjectName("AuthHeroText")
        hero_text.setWordWrap(True)
        hero_layout.addWidget(hero_text)
        hero_layout.addSpacing(10)

        for number, name_text, description in [
            ("01", "Турниры и расписание", "Сетки, матчи и игровые площадки"),
            ("02", "Команды и заявки", "Составы и допуск участников"),
            ("03", "Таблицы и отчёты", "Статистика и экспорт результатов"),
        ]:
            feature = QFrame()
            feature.setObjectName("AuthFeature")
            feature_layout = QHBoxLayout(feature)
            feature_layout.setContentsMargins(11, 10, 11, 10)
            feature_layout.setSpacing(11)
            icon = QLabel(number)
            icon.setObjectName("AuthFeatureIcon")
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon.setFixedSize(36, 36)
            copy = QVBoxLayout()
            copy.setSpacing(3)
            name = QLabel(name_text)
            name.setObjectName("AuthFeatureTitle")
            detail = QLabel(description)
            detail.setObjectName("AuthFeatureText")
            detail.setWordWrap(True)
            copy.addWidget(name)
            copy.addWidget(detail)
            feature_layout.addWidget(icon)
            feature_layout.addLayout(copy, 1)
            hero_layout.addWidget(feature)

        hero_layout.addStretch(1)
        footer = QLabel("ДЛЯ ОРГАНИЗАТОРОВ И ТРЕНЕРОВ")
        footer.setObjectName("AuthEyebrow")
        hero_layout.addWidget(footer)

        panel = QFrame()
        panel.setObjectName("AuthPanel")
        panel.setMinimumWidth(390)
        panel.setMaximumWidth(480)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(28, 28, 28, 28)
        panel_layout.setSpacing(10)

        title = QLabel("Добро пожаловать")
        title.setObjectName("AuthTitle")
        subtitle = QLabel("Войдите в систему или зарегистрируйте команду.")
        subtitle.setObjectName("AuthSubtitle")
        subtitle.setWordWrap(True)
        panel_layout.addWidget(title)
        panel_layout.addWidget(subtitle)
        panel_layout.addSpacing(8)

        tabs = QTabWidget()
        tabs.setDocumentMode(True)

        login_tab = QWidget()
        login_layout = QVBoxLayout(login_tab)
        login_layout.setContentsMargins(7, 14, 7, 10)
        login_layout.setSpacing(12)
        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(12)
        self.login_edit = QLineEdit()
        self.login_edit.setPlaceholderText("Введите логин")
        self.login_edit.setClearButtonEnabled(True)
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Введите пароль")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.returnPressed.connect(self.do_login)
        form.addRow("Логин", self.login_edit)
        form.addRow("Пароль", self.password_edit)
        login_layout.addLayout(form)

        show_password = QCheckBox("Показать пароль")
        show_password.toggled.connect(
            lambda checked: self.password_edit.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        login_layout.addWidget(show_password)
        self.login_error = QLabel("")
        self.login_error.setObjectName("FormError")
        self.login_error.setWordWrap(True)
        self.login_error.setMinimumHeight(22)
        login_layout.addWidget(self.login_error)
        login_button = make_button("Войти", self.do_login, "primary")
        login_button.setMinimumHeight(42)
        login_layout.addWidget(login_button)

        login_layout.addStretch(1)
        tabs.addTab(login_tab, "Вход")

        register_tab = QWidget()
        register_layout = QVBoxLayout(register_tab)
        register_layout.setContentsMargins(7, 14, 7, 10)
        register_layout.setSpacing(10)
        reg_form = QFormLayout()
        reg_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        reg_form.setHorizontalSpacing(12)
        reg_form.setVerticalSpacing(9)
        self.reg_login = QLineEdit()
        self.reg_login.setPlaceholderText("Придумайте логин")
        self.reg_password = QLineEdit()
        self.reg_password.setPlaceholderText("Не менее 4 символов")
        self.reg_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.reg_name = QLineEdit()
        self.reg_name.setPlaceholderText("Фамилия Имя Отчество")
        self.reg_team = QLineEdit()
        self.reg_team.setPlaceholderText("Название команды")
        self.reg_city = QLineEdit()
        self.reg_city.setPlaceholderText("Город")
        reg_form.addRow("Логин", self.reg_login)
        reg_form.addRow("Пароль", self.reg_password)
        reg_form.addRow("ФИО тренера", self.reg_name)
        reg_form.addRow("Команда", self.reg_team)
        reg_form.addRow("Город", self.reg_city)
        register_layout.addLayout(reg_form)

        note = QLabel(
            "После регистрации можно управлять составом и подавать заявки "
            "на открытые соревнования."
        )
        note.setObjectName("AuthSubtitle")
        note.setWordWrap(True)
        register_layout.addWidget(note)
        register_button = make_button(
            "Зарегистрировать команду", self.do_register, "primary"
        )
        register_button.setMinimumHeight(42)
        register_layout.addWidget(register_button)
        register_layout.addStretch(1)
        tabs.addTab(register_tab, "Регистрация")

        panel_layout.addWidget(tabs, 1)
        shell_layout.addWidget(hero, 1)
        shell_layout.addWidget(panel, 0)
        root.addWidget(shell, 1)
        self.login_edit.setFocus()

    def do_login(self):
        user = self.app.db.login(
            self.login_edit.text().strip(), self.password_edit.text()
        )
        if user is None:
            self.login_error.setText("Неверный логин или пароль. Проверьте введённые данные.")
            return
        self.login_error.setText("")
        self.app.login_ok(user)

    def do_register(self):
        try:
            self.app.db.register_coach(
                self.reg_login.text(), self.reg_password.text(),
                self.reg_name.text(), self.reg_team.text(), self.reg_city.text()
            )
        except (ValidationError, sqlite3.Error) as exc:
            warn(self, "Регистрация", str(exc))
            return
        info(self, "Регистрация", "Аккаунт тренера создан. Теперь войдите в систему.")
        self.login_edit.setText(self.reg_login.text().strip())
        self.password_edit.clear()


class FirstRunPage(QWidget):
    """Первичная настройка: пользователь самостоятельно создаёт организатора."""

    def __init__(self, app):
        super().__init__()
        self.app = app
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)

        panel = QFrame()
        panel.setObjectName("AuthPanel")
        panel.setMaximumWidth(580)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(30, 30, 30, 30)
        panel_layout.setSpacing(14)

        title = QLabel("Первоначальная настройка")
        title.setObjectName("AuthTitle")
        subtitle = QLabel(
            "Создай собственную учётную запись организатора. "
            "Логин и пароль задаёшь самостоятельно."
        )
        subtitle.setObjectName("AuthSubtitle")
        subtitle.setWordWrap(True)
        panel_layout.addWidget(title)
        panel_layout.addWidget(subtitle)

        form = QFormLayout()
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(12)
        self.full_name = QLineEdit()
        self.full_name.setPlaceholderText("Фамилия Имя Отчество")
        self.login = QLineEdit()
        self.login.setPlaceholderText("Придумай логин")
        self.password = QLineEdit()
        self.password.setPlaceholderText("Не менее 8 символов")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password = QLineEdit()
        self.confirm_password.setPlaceholderText("Повтори пароль")
        self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("ФИО", self.full_name)
        form.addRow("Логин", self.login)
        form.addRow("Пароль", self.password)
        form.addRow("Повтор пароля", self.confirm_password)
        panel_layout.addLayout(form)

        show_password = QCheckBox("Показать пароль")
        show_password.toggled.connect(
            lambda checked: (
                self.password.setEchoMode(
                    QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
                ),
                self.confirm_password.setEchoMode(
                    QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
                ),
            )
        )
        panel_layout.addWidget(show_password)

        self.error = QLabel("")
        self.error.setObjectName("FormError")
        self.error.setWordWrap(True)
        panel_layout.addWidget(self.error)

        create_button = make_button(
            "Создать учётную запись и войти", self.create_account, "primary"
        )
        create_button.setMinimumHeight(44)
        panel_layout.addWidget(create_button)
        root.addStretch(1)
        root.addWidget(panel, 0, Qt.AlignmentFlag.AlignHCenter)
        root.addStretch(1)
        self.full_name.setFocus()

    def create_account(self):
        password = self.password.text()
        if password != self.confirm_password.text():
            self.error.setText("Пароли не совпадают.")
            return
        try:
            user_id = self.app.db.create_organizer(
                self.login.text(), password, self.full_name.text()
            )
        except (ValidationError, sqlite3.Error) as exc:
            self.error.setText(str(exc))
            return
        self.app.login_ok(self.app.db.get_user(user_id))


class TournamentsTab(BaseTab):
    def __init__(self, app):
        super().__init__(app)
        self.title("Турниры", "Создавайте соревнования, принимайте заявки и формируйте турнирные сетки.")
        self.toolbar(
            make_button("Создать турнир", self.add, "primary"),
            make_button("Изменить", self.edit),
            make_button("Удалить", self.delete, "danger"),
            make_button("Сформировать сетку", self.generate),
            make_button("Сбросить сетку", self.reset)
        )
        self.table = DataTable(
            ["Название", "Вид спорта", "Система", "Даты", "Место",
             "Статус", "Команд", "Победитель"],
            widths=[220, 120, 205, 170, 150, 120, 70, 160]
        )
        self.table.cellDoubleClicked.connect(lambda *_: self.edit())
        self.layout.addWidget(self.table)
        self.layout.addWidget(QLabel(
            "Порядок работы: создайте турнир → тренеры подают заявки → одобрите заявки → "
            "сформируйте сетку → назначьте расписание и внесите результаты."
        ))

    def refresh(self):
        rows = []
        for t in self.db.list_tournaments():
            rows.append((t["id"], (
                t["name"], t["sport"], SYSTEM_NAMES[t["system"]],
                f"{fmt_date(t['start_date'])} – {fmt_date(t['end_date'])}",
                t["place"], TOURNAMENT_STATUS[t["status"]], t["teams_count"],
                self.db.tournament_winner(t["id"]) or "—"
            ), []))
        self.table.fill(rows)

    def fields(self):
        return [
            {"key": "name", "label": "Название"},
            {"key": "sport", "label": "Вид спорта"},
            {"key": "system", "label": "Система", "kind": "combo",
             "values": list(SYSTEM_NAMES.values())},
            {"key": "start", "label": "Дата начала (ДД.ММ.ГГГГ)"},
            {"key": "end", "label": "Дата окончания (ДД.ММ.ГГГГ)"},
            {"key": "place", "label": "Место проведения"}
        ]

    def add(self):
        today = datetime.date.today()
        initial = {
            "sport": "Волейбол", "system": SYSTEM_NAMES["olympic"],
            "start": fmt_date((today + datetime.timedelta(days=7)).isoformat()),
            "end": fmt_date((today + datetime.timedelta(days=14)).isoformat())
        }

        def submit(v):
            self.db.create_tournament(
                v["name"], v["sport"], SYSTEM_BY_LABEL.get(v["system"], ""),
                v["start"], v["end"], v["place"]
            )
        if show_form(self, "Новый турнир", self.fields(), submit, initial):
            self.app.notify("Турнир создан")
            self.app.refresh_all()

    def edit(self):
        tid = self.table.selected_id()
        if tid is None:
            info(self, "Изменение", "Выберите турнир в списке.")
            return
        t = self.db.get_tournament(tid)
        initial = {
            "name": t["name"], "sport": t["sport"],
            "system": SYSTEM_NAMES[t["system"]],
            "start": fmt_date(t["start_date"]), "end": fmt_date(t["end_date"]),
            "place": t["place"]
        }

        def submit(v):
            self.db.update_tournament(
                tid, v["name"], v["sport"], SYSTEM_BY_LABEL.get(v["system"], ""),
                v["start"], v["end"], v["place"]
            )
        if show_form(self, "Изменение турнира", self.fields(), submit, initial):
            self.app.notify("Изменения сохранены")
            self.app.refresh_all()

    def delete(self):
        tid = self.table.selected_id()
        if tid is None:
            info(self, "Удаление", "Выберите турнир в списке.")
            return
        t = self.db.get_tournament(tid)
        if confirm(self, "Удаление турнира",
                   f"Удалить турнир «{t['name']}» со всеми заявками и матчами?"):
            self.run(self.db.delete_tournament, tid, success="Турнир удалён")

    def generate(self):
        tid = self.table.selected_id()
        if tid is None:
            info(self, "Сетка", "Выберите турнир в списке.")
            return
        if self.db.match_count(tid) and not confirm(
            self, "Пересоздать сетку",
            "Сетка уже сформирована. Сформировать заново? Возможность зависит от наличия результатов."
        ):
            return
        if self.run(self.db.generate_bracket, tid, success="Сетка сформирована"):
            self.app.goto("Матчи и расписание")

    def reset(self):
        tid = self.table.selected_id()
        if tid is None:
            info(self, "Сетка", "Выберите турнир в списке.")
            return
        if not self.db.match_count(tid):
            info(self, "Сетка", "У этого турнира ещё нет сетки.")
            return
        if confirm(self, "Сброс сетки",
                   "Удалить сетку и расписание турнира и вернуться к приёму заявок?"):
            self.run(self.db.reset_bracket, tid, success="Сетка сброшена")



class ApplicationsTab(BaseTab):
    def __init__(self, app):
        super().__init__(app)
        self.title("Заявки команд", "Рассматривайте заявки на выбранный турнир.")
        self.selector = TournamentSelector(self.db)
        self.layout.addWidget(self.selector)
        self.toolbar(
            make_button("Одобрить", lambda: self.set_status("approved"), "primary"),
            make_button("Отклонить", lambda: self.set_status("rejected"), "danger"),
            make_button("Вернуть на рассмотрение", lambda: self.set_status("pending")),
            make_button("Одобрить все", self.approve_all)
        )
        self.table = DataTable(
            ["Команда", "Город", "Капитан", "Игроков", "Рейтинг", "Статус", "Подана"],
            widths=[210, 130, 180, 85, 90, 150, 150]
        )
        self.layout.addWidget(self.table)
        self.note = QLabel("")
        self.note.setObjectName("Muted")
        self.layout.addWidget(self.note)

    def refresh(self):
        self.selector.reload()
        self.fill()

    def fill(self):
        tid = self.selector.selected_id()
        rows = []
        self.note.setText("")
        if tid:
            tournament = self.db.get_tournament(tid)
            if tournament["status"] != "registration":
                self.note.setText(
                    "Турнир уже начался — заявки нельзя изменять. Сначала сбросьте сетку на вкладке «Турниры»."
                )
            else:
                self.note.setText("Приём заявок открыт. Одобренные команды попадут в сетку.")
            for a in self.db.list_applications(tid):
                tags = {"approved": "played", "rejected": "bad", "pending": "warn"}
                rows.append((a["id"], (
                    a["team_name"], a["city"], a["captain"], a["players_count"],
                    f"{a['rating']:.0f}", APP_STATUS[a["status"]], a["created_at"]
                ), [tags[a["status"]]]))
        self.table.fill(rows)

    def set_status(self, status):
        aid = self.table.selected_id()
        if aid is None:
            info(self, "Заявки", "Выберите заявку в списке.")
            return
        self.run(self.db.set_application_status, aid, status,
                 success="Статус заявки обновлён")

    def approve_all(self):
        tid = self.selector.selected_id()
        if tid is None:
            return

        def work():
            for application in self.db.list_applications(tid):
                if application["status"] == "pending":
                    self.db.set_application_status(application["id"], "approved")
        self.run(work, success="Все ожидающие заявки одобрены")


class TeamsTab(BaseTab):
    """Ручное ведение команд и составов без автозаполнения."""

    def __init__(self, app):
        super().__init__(app)
        self.title("Команды и составы", "Добавляй команды и заполняй составы игроков вручную.")
        self.toolbar(
            make_button("Добавить команду", self.add_team, "primary"),
            make_button("Изменить команду", self.edit_team),
            make_button("Удалить команду", self.delete_team, "danger"),
        )

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.teams = DataTable(
            ["Команда", "Город", "Капитан", "Игроков"],
            widths=[190, 130, 180, 70],
        )

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(9)

        self.selected_team_label = QLabel("Выбери команду слева")
        self.selected_team_label.setStyleSheet(
            "font-size: 12pt; font-weight: 600; color: #263449;"
        )
        right_layout.addWidget(self.selected_team_label)

        player_toolbar = QHBoxLayout()
        player_toolbar.addWidget(QLabel("Состав игроков"))
        player_toolbar.addStretch(1)
        player_toolbar.addWidget(make_button("Добавить игрока", self.add_player, "primary"))
        player_toolbar.addWidget(make_button("Изменить", self.edit_player))
        player_toolbar.addWidget(make_button("Удалить", self.delete_player, "danger"))
        right_layout.addLayout(player_toolbar)

        self.players = DataTable(
            ["№", "ФИО", "Амплуа", "Год рождения"],
            widths=[55, 220, 170, 110],
        )
        right_layout.addWidget(self.players, 1)

        splitter.addWidget(self.teams)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 4)
        self.layout.addWidget(splitter, 1)
        self.teams.itemSelectionChanged.connect(self.show_players)
        self.refresh()

    def selected_team(self):
        team_id = self.teams.selected_id()
        if team_id is None:
            info(self, "Команды", "Сначала выбери команду в списке.")
            return None
        return team_id

    def add_team(self):
        fields = [
            {"key": "name", "label": "Название команды"},
            {"key": "city", "label": "Город"},
            {"key": "captain", "label": "Капитан"},
        ]
        if show_form(
            self, "Новая команда", fields,
            lambda v: self.db.create_team(v["name"], v["city"], v["captain"]),
        ):
            self.refresh()
            self.app.notify("Команда добавлена")

    def edit_team(self):
        team_id = self.selected_team()
        if team_id is None:
            return
        team = self.db.get_team(team_id)
        fields = [
            {"key": "name", "label": "Название команды"},
            {"key": "city", "label": "Город"},
            {"key": "captain", "label": "Капитан"},
        ]
        initial = {
            "name": team["name"], "city": team["city"], "captain": team["captain"],
        }
        if show_form(
            self, "Изменение команды", fields,
            lambda v: self.db.update_team(team_id, v["name"], v["city"], v["captain"]),
            initial,
        ):
            self.refresh()
            self.app.notify("Данные команды обновлены")

    def delete_team(self):
        team_id = self.selected_team()
        if team_id is None:
            return
        team = self.db.get_team(team_id)
        if not confirm(
            self, "Удаление команды",
            f"Удалить команду «{team['name']}»? Её состав и заявки также будут удалены."
        ):
            return
        try:
            self.db.delete_team(team_id)
        except (ValidationError, sqlite3.Error) as exc:
            warn(self, "Удаление команды", str(exc))
            return
        self.refresh()
        self.app.notify("Команда удалена")

    def player_fields(self):
        return [
            {"key": "full_name", "label": "ФИО игрока"},
            {"key": "number", "label": "Игровой номер"},
            {"key": "position", "label": "Амплуа", "kind": "combo",
             "values": POSITION_OPTIONS},
            {"key": "birth_year", "label": "Год рождения"},
        ]

    def add_player(self):
        team_id = self.selected_team()
        if team_id is None:
            return
        fields = self.player_fields()

        def submit(values):
            position = selected_player_position(values["position"])
            self.db.add_player(
                team_id, values["full_name"], values["number"],
                position, values["birth_year"],
            )

        if show_form(
            self, "Новый игрок", fields, submit,
            {"position": POSITION_PLACEHOLDER},
        ):
            self.refresh()
            self.app.notify("Игрок добавлен")

    def edit_player(self):
        team_id = self.selected_team()
        player_id = self.players.selected_id()
        if team_id is None:
            return
        if player_id is None:
            info(self, "Игроки", "Выбери игрока в составе.")
            return
        player = next(
            (item for item in self.db.list_players(team_id) if item["id"] == player_id),
            None,
        )
        if player is None:
            info(self, "Игроки", "Игрок не найден.")
            return
        fields = self.player_fields()
        initial = {
            "full_name": player["full_name"], "number": player["number"],
            "position": player["position"] if player["position"] in POSITIONS
                        else POSITION_PLACEHOLDER,
            "birth_year": player["birth_year"],
        }

        def submit(values):
            position = selected_player_position(values["position"])
            self.db.update_player(
                player_id, values["full_name"], values["number"],
                position, values["birth_year"],
            )

        if show_form(self, "Изменение игрока", fields, submit, initial):
            self.refresh()
            self.app.notify("Карточка игрока обновлена")

    def delete_player(self):
        team_id = self.selected_team()
        player_id = self.players.selected_id()
        if team_id is None:
            return
        if player_id is None:
            info(self, "Игроки", "Выбери игрока в составе.")
            return
        if confirm(self, "Удаление игрока", "Удалить выбранную карточку игрока?"):
            self.db.delete_player(player_id)
            self.refresh()
            self.app.notify("Игрок удалён")

    def refresh(self):
        self.teams.fill([
            (
                team["id"],
                (
                    team["name"], team["city"] or "—",
                    team["captain"] or "—", team["players_count"],
                ),
                [],
            )
            for team in self.db.list_teams()
        ])
        self.show_players()

    def show_players(self):
        team_id = self.teams.selected_id()
        if team_id is None:
            self.selected_team_label.setText("Выбери команду слева")
            self.players.fill([])
            return
        team = self.db.get_team(team_id)
        self.selected_team_label.setText(
            f"{team['name']} · {team['city'] or 'город не указан'} · "
            f"Капитан: {team['captain'] or 'не назначен'}"
        )
        self.players.fill([
            (
                player["id"],
                (
                    player["number"], player["full_name"],
                    player["position"] or "—", player["birth_year"],
                ),
                [],
            )
            for player in self.db.list_players(team_id)
        ])

class MatchesTab(BaseTab):
    def __init__(self, app, readonly=False):
        super().__init__(app)
        self.readonly = readonly
        self.title("Расписание и матчи",
                   "Просмотр результатов, дат, времени и площадок. "
                   + ("Для тренера доступен просмотр матчей своей команды." if readonly else
                      "Организатор может назначать расписание и вносить результаты."))
        top = QHBoxLayout()
        self.selector = TournamentSelector(self.db, changed=self.fill)
        top.addWidget(self.selector)
        self.only_mine = QCheckBox("Только матчи моей команды")
        if readonly:
            self.only_mine.stateChanged.connect(self.fill)
            top.addWidget(self.only_mine)
        else:
            top.addStretch(1)
            self.layout.addLayout(top)
            self.toolbar(
                make_button("Ввести результат", self.result, "primary"),
                make_button("Очистить результат", self.clear, "danger"),
                make_button("Назначить время и место", self.schedule),
                make_button("Авто-расписание", self.auto),
                make_button("Экспорт протокола", self.export_match)
            )
            top = None
        if top is not None:
            self.layout.addLayout(top)
        self.table = DataTable(
            ["Тур / стадия", "№", "Команда 1", "Команда 2", "Счёт / партии",
             "Дата", "Время", "Площадка", "Статус"],
            widths=[135, 45, 170, 170, 220, 95, 65, 130, 120]
        )
        if not readonly:
            self.table.cellDoubleClicked.connect(lambda *_: self.result())
        self.layout.addWidget(self.table)
        self.note = QLabel("")
        self.note.setObjectName("Muted")
        self.layout.addWidget(self.note)

    def refresh(self):
        self.selector.reload()
        self.fill()

    def fill(self):
        tid = self.selector.selected_id()
        mine = self.app.team_id() if self.readonly else None
        rows = []
        self.note.setText("")
        if tid:
            matches = self.db.list_matches(tid)
            if not matches:
                self.note.setText("Сетка ещё не сформирована.")
            for m in matches:
                is_mine = mine is not None and mine in (m["team1_id"], m["team2_id"])
                if self.readonly and self.only_mine.isChecked() and not is_mine:
                    continue
                tags = []
                if is_mine:
                    tags.append("mine")
                if m["status"] == "played":
                    tags.append("played")
                elif m["status"] == "bye":
                    tags.append("muted")
                rows.append((m["id"], (
                    m["round_name"], m["position"], m["team1_name"] or "—",
                    m["team2_name"] or "—", self.db.score_text(m),
                    fmt_date(m["match_date"]), m["match_time"] or "",
                    m["venue"], MATCH_STATUS[m["status"]]
                ), tags))
        self.table.fill(rows)

    def selected_match(self):
        mid = self.table.selected_id()
        if mid is None:
            info(self, "Матчи", "Выберите матч в списке.")
            return None
        return self.db.get_match(mid)

    def result(self):
        if self.readonly:
            return
        match = self.selected_match()
        if match is None:
            return
        if match["status"] == "bye":
            info(self, "Матч", "Это автопроход — результат не вводится.")
            return
        if not match["team1_id"] or not match["team2_id"]:
            info(self, "Матч", "Соперники ещё не определены.")
            return
        if self.db.is_volleyball_tournament(match["tournament_id"]):
            initial_sets = [
                (row["team1_points"], row["team2_points"])
                for row in self.db.get_match_sets(match["id"])
            ]
            dialog = VolleyballResultDialog(
                self,
                match["team1_name"],
                match["team2_name"],
                lambda scores: self.db.record_volleyball_result(match["id"], scores),
                initial_sets
            )
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.app.notify("Результат матча сохранён, рейтинг пересчитан")
                self.app.refresh_all()
            return

        initial = {}
        if match["status"] == "played":
            initial = {"s1": match["score1"], "s2": match["score2"]}
        fields = [
            {"key": "s1", "label": f"Выиграно сетов: {match['team1_name']}"},
            {"key": "s2", "label": f"Выиграно сетов: {match['team2_name']}"}
        ]

        def submit(v):
            self.db.record_result(match["id"], v["s1"], v["s2"])
        if show_form(self, "Результат матча", fields, submit, initial,
                     "В олимпийской системе ничья невозможна."):
            self.app.notify("Результат сохранён, рейтинг пересчитан")
            self.app.refresh_all()

    def clear(self):
        if self.readonly:
            return
        match = self.selected_match()
        if match is None:
            return
        if match["status"] != "played":
            info(self, "Матч", "У этого матча нет результата.")
            return
        if confirm(self, "Очистка результата", "Очистить результат выбранного матча?"):
            self.run(self.db.clear_result, match["id"], success="Результат очищен")

    def schedule(self):
        if self.readonly:
            return
        match = self.selected_match()
        if match is None:
            return
        if match["status"] == "bye":
            info(self, "Матч", "Для автопрохода расписание не назначается.")
            return
        initial = {
            "date": fmt_date(match["match_date"]),
            "time": match["match_time"] or "",
            "venue": match["venue"]
        }
        fields = [
            {"key": "date", "label": "Дата (ДД.ММ.ГГГГ)"},
            {"key": "time", "label": "Время (ЧЧ:ММ)"},
            {"key": "venue", "label": "Площадка"}
        ]

        def submit(v):
            self.db.set_match_schedule(match["id"], v["date"], v["time"], v["venue"])
        if show_form(self, "Время и место матча", fields, submit, initial,
                     "Чтобы сбросить расписание, очистите дату и время."):
            self.app.notify("Расписание матча обновлено")
            self.app.refresh_all()

    def export_match(self):
        if self.readonly:
            return
        match = self.selected_match()
        if match is None:
            return
        if match["status"] != "played":
            info(self, "Экспорт протокола", "Сначала внесите результат матча.")
            return
        try:
            title, headers, rows = self.db.export_rows(
                "match_report", match_id=match["id"]
            )
        except ValidationError as exc:
            warn(self, "Экспорт протокола", str(exc))
            return
        default_name = f"Протокол_матча_{match['id']}_{datetime.date.today().isoformat()}.xlsx"
        path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Сохранить протокол матча",
            default_name,
            "Excel (*.xlsx);;CSV (*.csv)"
        )
        if not path:
            return
        extension = ".csv" if selected_filter.startswith("CSV") else ".xlsx"
        if not path.lower().endswith(extension):
            path = os.path.splitext(path)[0] + extension
        try:
            dbm.export_to_file(path, title, headers, rows)
        except (ValidationError, OSError) as exc:
            warn(self, "Экспорт протокола", str(exc))
            return
        self.app.notify(f"Протокол сохранён: {path}")
        info(self, "Экспорт протокола", f"Файл сохранён:
{path}")

    def auto(self):
        if self.readonly:
            return
        tid = self.selector.selected_id()
        if tid is None:
            info(self, "Расписание", "Сначала выберите турнир.")
            return
        fields = [
            {"key": "venues", "label": "Площадки (через запятую)"},
            {"key": "per_day", "label": "Матчей в день на площадке", "default": "4"},
            {"key": "start", "label": "Начало первого матча", "default": "10:00"},
            {"key": "minutes", "label": "Длительность слота (мин)", "default": "120"}
        ]
        initial = {"venues": "Зал 1, Зал 2", "per_day": "4",
                   "start": "10:00", "minutes": "120"}

        def submit(v):
            self.db.auto_schedule(
                tid, [venue.strip() for venue in v["venues"].split(",") if venue.strip()],
                v["per_day"], v["start"], v["minutes"]
            )
        if show_form(self, "Автоматическое расписание", fields, submit, initial,
                     "Система распределит матчи без пересечений команд и площадок."):
            self.app.notify("Автоматическое расписание создано")
            self.app.refresh_all()


class BracketTab(BaseTab):
    def __init__(self, app):
        super().__init__(app)
        self.title("Турнирная сетка", "Олимпийская сетка или матрица результатов кругового турнира.")
        self.selector = TournamentSelector(self.db, changed=self.fill)
        self.layout.addWidget(self.selector)
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setMinimumHeight(430)
        self.view.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        self.view.setBackgroundBrush(QColor("#f4f6f9"))
        self.view.setStyleSheet(
            "border: 1px solid #e3e8ef; border-radius: 9px; background: #f4f6f9;"
        )
        self.layout.addWidget(self.view)

    def refresh(self):
        self.selector.reload()
        self.fill()

    def fill(self):
        self.scene.clear()
        tid = self.selector.selected_id()
        if tid is None:
            self.scene.addText("Нет турниров.").setDefaultTextColor(QColor("#64748b"))
            return
        tournament = self.db.get_tournament(tid)
        matches = self.db.list_matches(tid)
        if not matches:
            self.scene.addText("Сетка ещё не сформирована.").setDefaultTextColor(QColor("#64748b"))
            return
        winner = self.db.tournament_winner(tid)
        if winner:
            title = self.scene.addText(f"Победитель турнира: {winner}")
            title.setDefaultTextColor(QColor("#15803d"))
            title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            title.setPos(15, 8)
        if tournament["system"] == "olympic":
            self.draw_olympic(matches, top=42 if winner else 15)
        else:
            self.draw_matrix(tid, matches)

    def draw_olympic(self, matches, top=15):
        rounds = {}
        for match in matches:
            rounds.setdefault(match["round"], []).append(match)
        box_w, box_h, gap_x, gap_y = 220, 66, 65, 34
        centers = {}
        mine = self.app.team_id()
        for rnd in sorted(rounds):
            current = sorted(rounds[rnd], key=lambda m: m["position"])
            x = 18 + (rnd - 1) * (box_w + gap_x)
            header = self.scene.addText(current[0]["round_name"])
            header.setDefaultTextColor(QColor("#2563eb"))
            header.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            header.setPos(x, top)
            for i, match in enumerate(current):
                if rnd == 1:
                    center_y = top + 65 + i * (box_h + gap_y) + box_h / 2
                else:
                    left = centers.get((rnd - 1, 2 * i), top + 80)
                    right = centers.get((rnd - 1, 2 * i + 1), left + box_h + gap_y)
                    center_y = (left + right) / 2
                centers[(rnd, i)] = center_y
                y = center_y - box_h / 2
                self.draw_match_box(x, y, box_w, box_h, match, mine)
                if rnd > 1:
                    for previous in (2 * i, 2 * i + 1):
                        py = centers.get((rnd - 1, previous), center_y)
                        x1 = x - gap_x
                        self.scene.addLine(
                            x1, py, x1 + gap_x / 2, py,
                            QPen(QColor("#94a3b8"))
                        )
                        self.scene.addLine(
                            x1 + gap_x / 2, py, x1 + gap_x / 2, center_y,
                            QPen(QColor("#94a3b8"))
                        )
                    self.scene.addLine(
                        x - gap_x / 2, center_y, x, center_y,
                        QPen(QColor("#94a3b8"))
                    )
        rect = self.scene.itemsBoundingRect()
        self.scene.setSceneRect(rect.adjusted(-20, -10, 30, 25))

    def draw_match_box(self, x, y, width, height, match, mine):
        own = mine is not None and mine in (match["team1_id"], match["team2_id"])
        border = QColor("#e6a23c") if own else QColor("#cbd5e1")
        self.scene.addRect(
            x, y, width, height, QPen(border, 1.4),
            QBrush(QColor("#fffaf0" if own else "#ffffff"))
        )
        self.scene.addLine(
            x, y + 30, x + width, y + 30, QPen(QColor("#e8edf3"))
        )
        self.scene.addLine(
            x, y + 60, x + width, y + 60, QPen(QColor("#e8edf3"))
        )
        for index, (name, score, team_id) in enumerate((
            (match["team1_name"], match["score1"], match["team1_id"]),
            (match["team2_name"], match["score2"], match["team2_id"])
        )):
            text = name or "Ожидается соперник"
            if len(text) > 24:
                text = text[:23] + "…"
            is_winner = match["winner_id"] is not None and match["winner_id"] == team_id
            if is_winner:
                text = "★ " + text
            label = self.scene.addText(text)
            label.setFont(QFont(
                "Segoe UI", 9,
                QFont.Weight.Bold if is_winner else QFont.Weight.Normal
            ))
            label.setDefaultTextColor(
                QColor("#172033" if name else "#94a3b8")
            )
            label.setPos(x + 9, y + index * 30 + 5)
            if score is not None:
                score_item = self.scene.addText(str(score))
                score_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                score_item.setDefaultTextColor(QColor("#1d4ed8"))
                score_item.setPos(x + width - 28, y + index * 30 + 4)

        details = self.db.match_sets_text(match["id"])
        if details:
            details_item = self.scene.addText(details)
            details_item.setFont(QFont("Segoe UI", 7))
            details_item.setDefaultTextColor(QColor("#52647b"))
            details_item.setTextWidth(width - 16)
            details_item.setPos(x + 8, y + 63)
        when = "  ·  ".join(part for part in (
            fmt_date(match["match_date"]), match["match_time"] or "", match["venue"]
        ) if part)
        if when:
            small = self.scene.addText(when)
            small.setFont(QFont("Segoe UI", 7))
            small.setDefaultTextColor(QColor("#64748b"))
            small.setPos(x, y + height + 3)

    def draw_matrix(self, tid, matches):
        table_rows = self.db.standings(tid)
        teams = [row["team_id"] for row in table_rows]
        names = {row["team_id"]: row["name"] for row in table_rows}
        results = {}
        for match in matches:
            if match["status"] != "played":
                continue
            sets = self.db.get_match_sets(match["id"])
            details = self.db.match_sets_text(match["id"])
            reverse_details = self.db.match_sets_text(match["id"], reverse=True)
            results[(match["team1_id"], match["team2_id"])] = {
                "score": f"{match['score1']}:{match['score2']}",
                "sets": details,
                "date": fmt_date(match["match_date"])
            }
            results[(match["team2_id"], match["team1_id"])] = {
                "score": f"{match['score2']}:{match['score1']}",
                "sets": reverse_details,
                "date": fmt_date(match["match_date"])
            }

        left = 18
        top = 18
        name_width = 220
        cell_width = 178
        points_width = 104
        header_height = 54
        row_height = 72
        total_width = left + name_width + len(teams) * cell_width + points_width + 18

        title = self.scene.addText("РЕЗУЛЬТАТЫ ВСТРЕЧ")
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title.setDefaultTextColor(QColor("#20334d"))
        title.setPos(left, top)

        header_y = top + 32
        self.scene.addRect(
            left, header_y, name_width, header_height,
            QPen(QColor("#233a59")), QBrush(QColor("#233a59"))
        )
        header_label = self.scene.addText("КОМАНДА")
        header_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        header_label.setDefaultTextColor(QColor("#ffffff"))
        header_label.setPos(left + 12, header_y + 18)

        for column, team_id in enumerate(teams):
            x = left + name_width + column * cell_width
            self.scene.addRect(
                x, header_y, cell_width, header_height,
                QPen(QColor("#314b6d")), QBrush(QColor("#314b6d"))
            )
            label = self.scene.addText(names[team_id])
            label.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            label.setDefaultTextColor(QColor("#ffffff"))
            label.setTextWidth(cell_width - 14)
            label.setPos(x + 8, header_y + 12)

        points_x = left + name_width + len(teams) * cell_width
        self.scene.addRect(
            points_x, header_y, points_width, header_height,
            QPen(QColor("#233a59")), QBrush(QColor("#233a59"))
        )
        points_header = self.scene.addText("ОЧКИ")
        points_header.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        points_header.setDefaultTextColor(QColor("#ffffff"))
        points_header.setPos(points_x + 14, header_y + 18)

        for row_index, row in enumerate(table_rows):
            team_id = row["team_id"]
            y = header_y + header_height + row_index * row_height
            base = QColor("#ffffff" if row_index % 2 == 0 else "#f8fafc")
            self.scene.addRect(
                left, y, name_width, row_height,
                QPen(QColor("#e2e8f0")), QBrush(QColor("#eef3f9"))
            )
            team_label = self.scene.addText(f"{row['place']}.  {names[team_id]}")
            team_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            team_label.setDefaultTextColor(QColor("#20334d"))
            team_label.setTextWidth(name_width - 18)
            team_label.setPos(left + 9, y + 24)

            for column, opponent_id in enumerate(teams):
                x = left + name_width + column * cell_width
                if team_id == opponent_id:
                    fill = QColor("#e9eef5")
                    value = "—"
                    color = QColor("#7b8797")
                    weight = QFont.Weight.Normal
                elif (team_id, opponent_id) in results:
                    result = results[(team_id, opponent_id)]
                    fill = QColor("#eaf6ee")
                    value = result["score"]
                    if result["sets"]:
                        value += "\n" + result["sets"]
                    color = QColor("#166534")
                    weight = QFont.Weight.Bold
                else:
                    fill = base
                    value = "Матч не сыгран"
                    color = QColor("#8a96a7")
                    weight = QFont.Weight.Normal
                self.scene.addRect(
                    x, y, cell_width, row_height,
                    QPen(QColor("#e2e8f0")), QBrush(fill)
                )
                cell_text = self.scene.addText(value)
                cell_text.setFont(QFont(
                    "Segoe UI", 8, weight
                ))
                cell_text.setDefaultTextColor(color)
                cell_text.setTextWidth(cell_width - 14)
                cell_text.setPos(x + 8, y + 11)
                if (team_id, opponent_id) in results and team_id != opponent_id:
                    date_text = results[(team_id, opponent_id)]["date"]
                    if date_text:
                        cell_text.setToolTip(f"Сыгран: {date_text}")

            self.scene.addRect(
                points_x, y, points_width, row_height,
                QPen(QColor("#e2e8f0")), QBrush(QColor("#f1f5f9"))
            )
            points_text = self.scene.addText(f"{row['points']} очк.")
            points_text.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            points_text.setDefaultTextColor(QColor("#1d4ed8"))
            points_text.setPos(points_x + 15, y + 26)

        footer_y = header_y + header_height + len(teams) * row_height + 10
        legend = self.scene.addText(
            "В ячейке: итог по партиям и счёт отдельных партий. "
            "Волейбол: 3 очка за 3:0 / 3:1, 2 — за 3:2, 1 — за 2:3."
        )
        legend.setFont(QFont("Segoe UI", 8))
        legend.setDefaultTextColor(QColor("#64748b"))
        legend.setPos(left, footer_y)
        total_height = footer_y + 32
        self.scene.setSceneRect(0, 0, total_width, total_height)


class StatsTab(BaseTab):
    def __init__(self, app):
        super().__init__(app)
        self.title("Турнирная таблица", "Положение команд рассчитывается по результатам сыгранных матчей.")
        self.selector = TournamentSelector(self.db)
        self.layout.addWidget(self.selector)
        self.table = DataTable(
            ["Место", "Команда", "И", "В", "Н", "П", "Сеты +", "Сеты −",
             "Разница", "Очки", "Рейтинг"],
            widths=[60, 220, 45, 45, 45, 45, 75, 75, 75, 70, 85]
        )
        self.layout.addWidget(self.table)
        self.note = QLabel("")
        self.note.setObjectName("Muted")
        self.layout.addWidget(self.note)

    def refresh(self):
        self.selector.reload()
        tid = self.selector.selected_id()
        rows = []
        self.note.setText("")
        if tid:
            tournament = self.db.get_tournament(tid)
            mine = self.app.team_id()
            for r in self.db.standings(tid):
                tags = ["mine"] if r["team_id"] == mine else []
                rows.append((r["team_id"], (
                    r["place"], r["name"], r["played"], r["wins"], r["draws"],
                    r["losses"], r["gf"], r["ga"],
                    f"{r['diff']:+d}" if r["diff"] else "0",
                    r["points"], f"{r['rating']:.0f}"
                ), tags))
            if tournament["system"] == "olympic":
                self.note.setText(
                    "Олимпийская система: места сортируются по числу побед, затем по разнице сетов."
                )
            else:
                self.note.setText("Круговая система: победа — 3 очка, ничья — 1, поражение — 0.")
        self.table.fill(rows)


class RatingTab(BaseTab):
    def __init__(self, app):
        super().__init__(app)
        self.title("Рейтинг команд", "Автоматический рейтинг по системе Эло: старт 1000 очков, коэффициент K = 32.")
        self.toolbar(make_button("Пересчитать рейтинг", self.recalc, "primary"))
        self.table = DataTable(
            ["Место", "Команда", "Город", "Рейтинг", "Игры",
             "Победы", "Ничьи", "Поражения"],
            widths=[65, 230, 150, 100, 75, 90, 80, 100]
        )
        self.layout.addWidget(self.table)

    def refresh(self):
        mine = self.app.team_id()
        self.table.fill([
            (r["team_id"], (
                r["place"], r["name"], r["city"], f"{r['rating']:.1f}",
                r["played"], r["wins"], r["draws"], r["losses"]
            ), ["mine"] if r["team_id"] == mine else [])
            for r in self.db.ratings_table()
        ])

    def recalc(self):
        self.run(self.db.recalc_ratings, success="Рейтинг пересчитан")


class ExportTab(BaseTab):
    KINDS = [
        ("standings", "Турнирная таблица"),
        ("schedule", "Расписание и результаты матчей"),
        ("matches_by_date", "Сыгранные матчи за дату"),
        ("applications", "Заявки команд"),
        ("roster", "Составы команд"),
        ("ratings", "Рейтинг команд")
    ]

    def __init__(self, app):
        super().__init__(app)
        self.title("Экспорт данных", "Сохранение турнирных таблиц, расписания, заявок и составов в Excel или CSV.")
        self.selector = TournamentSelector(self.db)
        self.layout.addWidget(self.selector)
        panel = QFrame()
        panel.setObjectName("Surface")
        form = QFormLayout(panel)
        form.setContentsMargins(18, 18, 18, 18)
        self.kind = QComboBox()
        for key, label in self.KINDS:
            self.kind.addItem(label, key)
        self.all_rosters = QCheckBox("Выгрузить составы всех команд, а не только участников турнира")
        self.match_date_label = QLabel("Дата сыгранных матчей (ДД.ММ.ГГГГ)")
        self.match_date = QLineEdit(datetime.date.today().strftime("%d.%m.%Y"))
        self.match_date.setPlaceholderText("Например, 18.11.2026")
        self.format = QComboBox()
        self.format.addItem("Excel (.xlsx)", "xlsx")
        self.format.addItem("CSV (.csv)", "csv")
        form.addRow("Что выгрузить", self.kind)
        form.addRow("", self.all_rosters)
        form.addRow(self.match_date_label, self.match_date)
        form.addRow("Формат файла", self.format)
        self.kind.currentIndexChanged.connect(self._sync_export_fields)
        self._sync_export_fields()
        self.layout.addWidget(panel)
        self.layout.addWidget(make_button("Экспортировать…", self.export, "primary"))
        self.layout.addStretch(1)

    def _sync_export_fields(self):
        is_roster = self.kind.currentData() == "roster"
        is_date = self.kind.currentData() == "matches_by_date"
        self.all_rosters.setVisible(is_roster)
        self.match_date_label.setVisible(is_date)
        self.match_date.setVisible(is_date)

    def refresh(self):
        self.selector.reload()

    def export(self):
        kind = self.kind.currentData()
        tid = self.selector.selected_id()
        if kind == "roster" and self.all_rosters.isChecked():
            tid = None
        elif kind == "roster" and tid is None:
            info(self, "Экспорт", "Выберите турнир или отметьте выгрузку всех команд.")
            return
        try:
            title, headers, rows = self.db.export_rows(
                kind,
                tid,
                match_date=self.match_date.text().strip()
                if kind == "matches_by_date" else None
            )
        except ValidationError as exc:
            warn(self, "Экспорт", str(exc))
            return
        if not rows:
            info(self, "Экспорт", "Нет данных для выгрузки.")
            return
        extension = self.format.currentData()
        file_filter = "Excel (*.xlsx)" if extension == "xlsx" else "CSV (*.csv)"
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить файл",
            f"{title}_{datetime.date.today().isoformat()}.{extension}",
            file_filter
        )
        if not path:
            return
        try:
            dbm.export_to_file(path, title, headers, rows)
        except (ValidationError, OSError) as exc:
            warn(self, "Экспорт", str(exc))
            return
        self.app.notify(f"Файл сохранён: {path}")
        info(self, "Экспорт", f"Готово! Выгружено строк: {len(rows)}.\n{path}")


class MyTeamTab(BaseTab):
    def __init__(self, app):
        super().__init__(app)
        self.title("Моя команда", "Редактируйте информацию о команде и её составе.")
        panel = QFrame()
        panel.setObjectName("Surface")
        form = QFormLayout(panel)
        form.setContentsMargins(16, 14, 16, 14)
        self.team_name = QLineEdit()
        self.city = QLineEdit()
        self.captain = QLineEdit()
        form.addRow("Название", self.team_name)
        form.addRow("Город", self.city)
        form.addRow("Капитан / тренер", self.captain)
        form.addRow("", make_button("Сохранить данные команды", self.save_team, "primary"))
        self.layout.addWidget(panel)
        self.layout.addWidget(QLabel("Состав команды"))
        self.toolbar(
            make_button("Добавить игрока", self.add, "primary"),
            make_button("Изменить", self.edit),
            make_button("Удалить", self.delete, "danger")
        )
        self.table = DataTable(["№", "ФИО", "Амплуа", "Год рождения"],
                               widths=[60, 280, 180, 120])
        self.layout.addWidget(self.table)
        self.count = QLabel("")
        self.count.setObjectName("Muted")
        self.layout.addWidget(self.count)
        self._loaded = None

    def refresh(self):
        team = self.db.get_team(self.app.team_id())
        if team is None:
            return
        loaded = {
            "name": team["name"], "city": team["city"], "captain": team["captain"]
        }
        if self._loaded is None or all(
            widget.text() == self._loaded[key]
            for key, widget in (("name", self.team_name), ("city", self.city),
                                ("captain", self.captain))
        ):
            self.team_name.setText(loaded["name"])
            self.city.setText(loaded["city"])
            self.captain.setText(loaded["captain"])
        self._loaded = loaded
        players = self.db.list_players(team["id"])
        self.count.setText(
            f"Игроков: {len(players)} (для заявки нужно не меньше {dbm.MIN_ROSTER}, "
            f"максимум {dbm.MAX_ROSTER})"
        )
        self.table.fill([
            (p["id"], (p["number"], p["full_name"], p["position"], p["birth_year"]), [])
            for p in players
        ])

    def save_team(self):
        self.run(
            self.db.update_team, self.app.team_id(), self.team_name.text(),
            self.city.text(), self.captain.text(), success="Данные команды сохранены"
        )

    def player_fields(self):
        return [
            {"key": "name", "label": "ФИО игрока"},
            {"key": "number", "label": "Номер (0–99)"},
            {"key": "pos", "label": "Амплуа", "kind": "combo",
             "values": POSITION_OPTIONS},
            {"key": "year", "label": "Год рождения"}
        ]

    def add(self):
        team_id = self.app.team_id()

        def submit(v):
            position = selected_player_position(v["pos"])
            self.db.add_player(
                team_id, v["name"], v["number"], position, v["year"]
            )
        if show_form(self, "Новый игрок", self.player_fields(), submit, {"year": "2004"}):
            self.app.notify("Игрок добавлен")
            self.app.refresh_all()

    def edit(self):
        player_id = self.table.selected_id()
        if player_id is None:
            info(self, "Состав", "Выберите игрока в списке.")
            return
        player = next(
            p for p in self.db.list_players(self.app.team_id()) if p["id"] == player_id
        )
        initial = {
            "name": player["full_name"], "number": player["number"],
            "pos": player["position"] if player["position"] in POSITIONS
                   else POSITION_PLACEHOLDER,
            "year": player["birth_year"]
        }

        def submit(v):
            position = selected_player_position(v["pos"])
            self.db.update_player(
                player_id, v["name"], v["number"], position, v["year"]
            )
        if show_form(self, "Изменение игрока", self.player_fields(), submit, initial):
            self.app.notify("Данные игрока сохранены")
            self.app.refresh_all()

    def delete(self):
        player_id = self.table.selected_id()
        if player_id is None:
            info(self, "Состав", "Выберите игрока в списке.")
            return
        if confirm(self, "Удаление", "Удалить игрока из состава?"):
            self.run(self.db.delete_player, player_id, success="Игрок удалён")


class MyApplicationsTab(BaseTab):
    def __init__(self, app):
        super().__init__(app)
        self.title("Заявки на турниры", "Выберите соревнование с открытым приёмом заявок или отзовите свою заявку.")
        self.toolbar(make_button("Подать заявку", self.submit, "primary"))
        self.open_table = DataTable(
            ["Турнир", "Вид спорта", "Система", "Даты", "Место"],
            widths=[230, 130, 200, 180, 160], height=170
        )
        self.layout.addWidget(QLabel("Турниры с открытым приёмом заявок"))
        self.layout.addWidget(self.open_table)
        self.layout.addWidget(QLabel("Мои заявки"))
        self.toolbar(make_button("Отозвать заявку", self.withdraw, "danger"))
        self.my_table = DataTable(
            ["Турнир", "Статус заявки", "Статус турнира", "Подана"],
            widths=[240, 160, 150, 160], height=170
        )
        self.layout.addWidget(self.my_table)

    def refresh(self):
        self.open_table.fill([
            (t["id"], (
                t["name"], t["sport"], SYSTEM_NAMES[t["system"]],
                f"{fmt_date(t['start_date'])} – {fmt_date(t['end_date'])}", t["place"]
            ), [])
            for t in self.db.list_tournaments("registration")
        ])
        tags = {"approved": "played", "rejected": "bad", "pending": "warn"}
        self.my_table.fill([
            (a["id"], (
                a["tournament_name"], APP_STATUS[a["status"]],
                TOURNAMENT_STATUS[a["tournament_status"]], a["created_at"]
            ), [tags[a["status"]]])
            for a in self.db.list_applications(team_id=self.app.team_id())
        ])

    def submit(self):
        tid = self.open_table.selected_id()
        if tid is None:
            info(self, "Заявка", "Выберите турнир в верхнем списке.")
            return
        self.run(self.db.submit_application, tid, self.app.team_id(),
                 success="Заявка подана и ожидает решения организатора")

    def withdraw(self):
        aid = self.my_table.selected_id()
        if aid is None:
            info(self, "Заявка", "Выберите заявку в нижнем списке.")
            return
        if confirm(self, "Отзыв заявки", "Отозвать выбранную заявку?"):
            self.run(self.db.withdraw_application, aid, success="Заявка отозвана")


class MyStatsTab(BaseTab):
    def __init__(self, app):
        super().__init__(app)
        self.title("Моя статистика", "Личные показатели команды и история матчей.")
        self.cards = QGridLayout()
        self.values = {}
        labels = [
            ("rating", "Рейтинг"), ("place", "Место в рейтинге"),
            ("played", "Матчей"), ("wld", "Победы / ничьи / поражения"),
            ("goals", "Сеты выиграно / проиграно"), ("points", "Очки")
        ]
        for index, (key, label) in enumerate(labels):
            card = QFrame()
            card.setObjectName("Surface")
            card_layout = QVBoxLayout(card)
            value = QLabel("—")
            value.setStyleSheet("font-size: 18pt; font-weight: 700; color: #2563eb;")
            caption = QLabel(label)
            caption.setObjectName("Muted")
            card_layout.addWidget(value)
            card_layout.addWidget(caption)
            self.cards.addWidget(card, index // 3, index % 3)
            self.values[key] = value
        self.layout.addLayout(self.cards)
        self.layout.addWidget(QLabel("История матчей"))
        self.table = DataTable(
            ["Турнир", "Тур / стадия", "Соперник", "Счёт", "Итог", "Дата", "Время"],
            widths=[200, 125, 190, 80, 105, 100, 70]
        )
        self.layout.addWidget(self.table)

    def refresh(self):
        team_id = self.app.team_id()
        stats = self.db.team_stats(team_id)
        team = self.db.get_team(team_id)
        place = next(
            (r["place"] for r in self.db.ratings_table() if r["team_id"] == team_id), "—"
        )
        self.values["rating"].setText(f"{team['rating']:.0f}")
        self.values["place"].setText(str(place))
        self.values["played"].setText(str(stats["played"]))
        self.values["wld"].setText(
            f"{stats['wins']} / {stats['draws']} / {stats['losses']}"
        )
        self.values["goals"].setText(f"{stats['gf']} / {stats['ga']}")
        self.values["points"].setText(str(stats["points"]))
        tags = {"Победа": "played", "Поражение": "bad",
                "Ничья": "warn", "Впереди": "muted"}
        history = self.db.team_history(team_id)
        self.table.fill([
            (index, (
                item["tournament"], item["round"], item["opponent"],
                item["score"], item["outcome"], item["date"], item["time"]
            ), [tags[item["outcome"]]])
            for index, item in enumerate(history)
        ])



class DashboardTab(BaseTab):
    """Главная страница с обзором системы и быстрыми переходами."""

    def __init__(self, app):
        super().__init__(app)
        intro = QHBoxLayout()
        welcome = QVBoxLayout()
        self.welcome_title = QLabel("Обзор спортивных соревнований")
        self.welcome_title.setObjectName("PageTitle")
        self.welcome_subtitle = QLabel("Ключевые показатели и быстрый доступ к рабочим разделам.")
        self.welcome_subtitle.setObjectName("Muted")
        welcome.addWidget(self.welcome_title)
        welcome.addWidget(self.welcome_subtitle)
        intro.addLayout(welcome)
        intro.addStretch(1)
        self.layout.addLayout(intro)

        metrics = QGridLayout()
        metrics.setHorizontalSpacing(12)
        metrics.setVerticalSpacing(12)
        self.metric_values = {}
        definitions = [
            ("tournaments", "Турниров", "Всего соревнований"),
            ("teams", "Команд", "Зарегистрировано в системе"),
            ("pending", "Заявок ожидают", "Требуют решения организатора"),
            ("matches", "Сыграно матчей", "Результаты уже внесены")
        ]
        for index, (key, title, hint) in enumerate(definitions):
            card = QFrame()
            card.setObjectName("MetricCard")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(17, 14, 17, 14)
            layout.setSpacing(3)
            value = QLabel("—")
            value.setObjectName("MetricValue")
            caption = QLabel(title)
            caption.setObjectName("MetricTitle")
            note = QLabel(hint)
            note.setObjectName("MetricHint")
            layout.addWidget(value)
            layout.addWidget(caption)
            layout.addWidget(note)
            metrics.addWidget(card, 0, index)
            self.metric_values[key] = value
        self.layout.addLayout(metrics)

        lower = QHBoxLayout()
        lower.setSpacing(14)

        recent_panel = QFrame()
        recent_panel.setObjectName("Surface")
        recent_layout = QVBoxLayout(recent_panel)
        recent_layout.setContentsMargins(16, 14, 16, 14)
        recent_heading = QLabel("Последние турниры")
        recent_heading.setStyleSheet("font-size: 12pt; font-weight: 700;")
        recent_layout.addWidget(recent_heading)
        self.recent_table = DataTable(
            ["Турнир", "Система", "Статус", "Команд"],
            widths=[230, 190, 130, 75]
        )
        self.recent_table.setMinimumHeight(275)
        recent_layout.addWidget(self.recent_table)

        quick_panel = QFrame()
        quick_panel.setObjectName("Surface")
        quick_layout = QVBoxLayout(quick_panel)
        quick_layout.setContentsMargins(16, 14, 16, 14)
        quick_heading = QLabel("Быстрые действия")
        quick_heading.setStyleSheet("font-size: 12pt; font-weight: 700;")
        quick_layout.addWidget(quick_heading)
        quick_hint = QLabel("Переход к часто используемым разделам.")
        quick_hint.setObjectName("Muted")
        quick_layout.addWidget(quick_hint)
        self.quick_buttons = []
        if app.user["role"] == ROLE_ORG:
            self.quick_target = [
                ("Создать / открыть турниры", "Турниры"),
                ("Рассмотреть заявки", "Заявки"),
                ("Открыть расписание матчей", "Матчи и расписание"),
                ("Посмотреть турнирную таблицу", "Таблица")
            ]
        else:
            self.quick_target = [
                ("Открыть мою команду", "Моя команда"),
                ("Подать заявку на турнир", "Заявки на турниры"),
                ("Посмотреть расписание", "Расписание"),
                ("Открыть мою статистику", "Моя статистика")
            ]
        for text, target in self.quick_target:
            button = QPushButton("›   " + text)
            button.setObjectName("NavButton")
            button.setStyleSheet(
                "QPushButton { text-align: left; background: #f5f8fc; "
                "border: 1px solid #e8edf4; padding: 13px; color: #26364f; } "
                "QPushButton:hover { background: #eaf2ff; color: #1d4ed8; }"
            )
            button.clicked.connect(lambda checked=False, name=target: self.app.goto(name))
            quick_layout.addWidget(button)
            self.quick_buttons.append(button)
        quick_layout.addStretch(1)
        footnote = QLabel("Подсказка: нажмите F5 или «Обновить», чтобы перечитать данные.")
        footnote.setWordWrap(True)
        footnote.setObjectName("Muted")
        quick_layout.addWidget(footnote)

        lower.addWidget(recent_panel, 3)
        lower.addWidget(quick_panel, 2)
        self.layout.addLayout(lower, 1)

    def refresh(self):
        tournaments = self.db.list_tournaments()
        teams = self.db.list_teams()
        team_id = self.app.team_id()
        applications = (
            self.db.list_applications(team_id=team_id)
            if team_id is not None else self.db.list_applications()
        )
        pending = sum(1 for item in applications if item["status"] == "pending")
        played = 0
        for tournament in tournaments:
            played += sum(
                1 for match in self.db.list_matches(tournament["id"])
                if match["status"] == "played"
                and (team_id is None or team_id in (match["team1_id"], match["team2_id"]))
            )

        self.metric_values["tournaments"].setText(str(len(tournaments)))
        self.metric_values["teams"].setText(str(len(teams)))
        self.metric_values["pending"].setText(str(pending))
        self.metric_values["matches"].setText(str(played))

        rows = []
        for tournament in tournaments[:8]:
            rows.append((tournament["id"], (
                tournament["name"], SYSTEM_NAMES[tournament["system"]],
                TOURNAMENT_STATUS[tournament["status"]], tournament["teams_count"]
            ), []))
        self.recent_table.fill(rows)


class MainWindow(QMainWindow):
    PAGE_DESCRIPTIONS = {
        "Главная": "Общая картина системы, показатели и быстрые действия.",
        "Турниры": "Создание соревнований, управление статусами и формирование сеток.",
        "Заявки": "Проверка заявок команд и управление допуском к турнирам.",
        "Команды": "Справочник команд и зарегистрированных игроков.",
        "Матчи и расписание": "Результаты матчей, даты, время, площадки и автоматическое расписание.",
        "Расписание": "Календарь матчей и результаты выступлений команды.",
        "Сетка": "Ход соревнований: олимпийская сетка или круговая таблица.",
        "Таблица": "Турнирное положение и статистика команд.",
        "Турнирная таблица": "Положение команд по результатам сыгранных матчей.",
        "Рейтинг": "Рейтинг команд, рассчитанный по системе Эло.",
        "Экспорт": "Выгрузка данных в форматы Excel и CSV.",
        "Моя команда": "Данные команды и управление составом игроков.",
        "Заявки на турниры": "Доступные соревнования и поданные заявки.",
        "Моя статистика": "Показатели команды и история сыгранных матчей."
    }

    def __init__(self, db_path=None):
        super().__init__()
        self.setWindowTitle("АРМ «Спортивный организатор»")
        self.resize(1440, 900)
        self.setMinimumSize(1120, 720)
        self.db = dbm.Database(db_path or DB_FILE)
        self.user = None
        self.tabs = []
        self.pages = {}
        self.nav_buttons = {}
        self.setStyleSheet(APP_STYLE)
        self.refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        self.refresh_shortcut.activated.connect(self.refresh_all)
        self.show_login()

    def notify(self, message):
        self.statusBar().showMessage(message, 7000)

    def show_login(self):
        self.user = None
        self.tabs = []
        self.pages = {}
        self.nav_buttons = {}
        self.statusBar().hide()
        if self.db.has_organizer():
            self.setCentralWidget(LoginPage(self))
        else:
            self.setCentralWidget(FirstRunPage(self))

    def login_ok(self, user):
        self.user = user
        self.show_dashboard()

    def team_id(self):
        if self.user is None or self.user["role"] != ROLE_COACH:
            return None
        row = self.db.get_user(self.user["id"])
        return row["team_id"] if row else None

    def _add_sidebar_heading(self, layout, text):
        label = QLabel(text)
        label.setObjectName("SidebarSection")
        layout.addWidget(label)

    def _add_nav_button(self, layout, title, page):
        button = QPushButton(title)
        button.setObjectName("NavButton")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setMinimumHeight(42)
        button.clicked.connect(
            lambda checked=False, name=title: self.goto(name)
        )
        layout.addWidget(button)
        self.nav_buttons[title] = button
        self.pages[title] = page
        self.tabs.append((title, page))

    def show_dashboard(self):
        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(252)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 20, 16, 16)
        sidebar_layout.setSpacing(5)

        brand_row = QHBoxLayout()
        brand_mark = QLabel("SO")
        brand_mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_mark.setFixedSize(42, 42)
        brand_mark.setStyleSheet(
            "background: #2563eb; color: white; border-radius: 11px; "
            "font-size: 14pt; font-weight: 600;"
        )
        brand_text = QVBoxLayout()
        brand = QLabel("SPORT ARM")
        brand.setObjectName("SidebarBrand")
        sub_brand = QLabel("СПОРТИВНЫЙ ОРГАНИЗАТОР")
        sub_brand.setObjectName("SidebarSub")
        brand_text.addWidget(brand)
        brand_text.addWidget(sub_brand)
        brand_row.addWidget(brand_mark)
        brand_row.addLayout(brand_text, 1)
        sidebar_layout.addLayout(brand_row)
        sidebar_layout.addSpacing(16)

        # Навигация прокручивается отдельно: профиль и выход всегда остаются видимыми.
        nav_scroll = QScrollArea()
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setFrameShape(QFrame.Shape.NoFrame)
        nav_scroll.setStyleSheet("background: transparent;")
        nav_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        nav_content = QWidget()
        nav_content.setStyleSheet("background: transparent;")
        nav_layout = QVBoxLayout(nav_content)
        nav_layout.setContentsMargins(0, 0, 3, 0)
        nav_layout.setSpacing(3)
        nav_scroll.setWidget(nav_content)
        sidebar_layout.addWidget(nav_scroll, 1)

        self._add_sidebar_heading(nav_layout, "ОБЗОР")
        self._add_nav_button(nav_layout, "Главная", DashboardTab(self))

        if self.user["role"] == ROLE_ORG:
            self._add_sidebar_heading(nav_layout, "УПРАВЛЕНИЕ")
            for title, factory in [
                ("Турниры", TournamentsTab),
                ("Заявки", ApplicationsTab),
                ("Команды", TeamsTab),
                ("Матчи и расписание", MatchesTab),
                ("Сетка", BracketTab)
            ]:
                self._add_nav_button(nav_layout, title, factory(self))

            self._add_sidebar_heading(nav_layout, "АНАЛИТИКА И ОТЧЁТЫ")
            for title, factory in [
                ("Таблица", StatsTab),
                ("Рейтинг", RatingTab),
                ("Экспорт", ExportTab)
            ]:
                self._add_nav_button(nav_layout, title, factory(self))
        else:
            self._add_sidebar_heading(nav_layout, "МОЯ КОМАНДА")
            self._add_nav_button(nav_layout, "Моя команда", MyTeamTab(self))
            self._add_nav_button(nav_layout, "Заявки на турниры", MyApplicationsTab(self))
            self._add_sidebar_heading(nav_layout, "СОРЕВНОВАНИЯ")
            self._add_nav_button(
                sidebar_layout, "Расписание", MatchesTab(self, readonly=True)
            )
            self._add_nav_button(nav_layout, "Сетка", BracketTab(self))
            self._add_nav_button(nav_layout, "Таблица", StatsTab(self))
            self._add_nav_button(nav_layout, "Моя статистика", MyStatsTab(self))
            self._add_nav_button(nav_layout, "Рейтинг", RatingTab(self))

        nav_layout.addStretch(1)

        profile = QFrame()
        profile.setObjectName("ProfileCard")
        profile_layout = QVBoxLayout(profile)
        profile_layout.setContentsMargins(12, 11, 12, 11)
        profile_name = QLabel(self.user["full_name"] or self.user["login"])
        profile_name.setObjectName("ProfileName")
        profile_name.setWordWrap(True)
        role = "Организатор" if self.user["role"] == ROLE_ORG else "Тренер / капитан"
        profile_role = QLabel(role)
        profile_role.setObjectName("ProfileRole")
        logout = QPushButton("Выйти из системы")
        logout.setStyleSheet(
            "QPushButton { background: #253751; color: #dbe6f5; "
            "border: 0; text-align: left; padding: 8px 9px; } "
            "QPushButton:hover { background: #334967; color: white; }"
        )
        logout.clicked.connect(self.show_login)
        profile_layout.addWidget(profile_name)
        profile_layout.addWidget(profile_role)
        profile_layout.addSpacing(5)
        profile_layout.addWidget(logout)
        sidebar_layout.addWidget(profile)

        workspace = QFrame()
        workspace.setObjectName("Workspace")
        workspace_layout = QVBoxLayout(workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)

        topbar = QFrame()
        topbar.setObjectName("Topbar")
        topbar.setMinimumHeight(86)
        topbar_layout = QHBoxLayout(topbar)
        topbar_layout.setContentsMargins(28, 14, 28, 14)
        heading_layout = QVBoxLayout()
        self.page_heading = QLabel("Главная")
        self.page_heading.setObjectName("PageTitle")
        self.page_caption = QLabel(self.PAGE_DESCRIPTIONS["Главная"])
        self.page_caption.setObjectName("PageSubtitle")
        heading_layout.addWidget(self.page_heading)
        heading_layout.addWidget(self.page_caption)
        topbar_layout.addLayout(heading_layout)
        topbar_layout.addStretch(1)

        role_chip = QLabel("ОРГАНИЗАТОР" if self.user["role"] == ROLE_ORG else "ТРЕНЕР")
        role_chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        role_chip.setStyleSheet(
            "background: #eff6ff; color: #1d4ed8; border-radius: 8px; "
            "padding: 8px 11px; font-size: 8pt; font-weight: 600;"
        )
        topbar_layout.addWidget(role_chip)
        refresh = QPushButton("Обновить  ·  F5")
        refresh.setObjectName("Primary")
        refresh.clicked.connect(self.refresh_all)
        topbar_layout.addWidget(refresh)
        workspace_layout.addWidget(topbar)

        self.stack = QStackedWidget()
        self.stack.setContentsMargins(0, 0, 0, 0)
        for title, page in self.tabs:
            self.stack.addWidget(page)
        workspace_layout.addWidget(self.stack, 1)

        root_layout.addWidget(sidebar)
        root_layout.addWidget(workspace, 1)
        self.setCentralWidget(root)
        self.statusBar().show()
        self.statusBar().showMessage("Готово")
        self.refresh_all()
        self.goto("Главная")

    def refresh_all(self):
        for _, page in self.tabs:
            page.refresh()

    def goto(self, title):
        page = self.pages.get(title)
        if page is None:
            return
        self.stack.setCurrentWidget(page)
        self.page_heading.setText(title)
        self.page_caption.setText(
            self.PAGE_DESCRIPTIONS.get(title, "Рабочий раздел программы.")
        )
        for name, button in self.nav_buttons.items():
            button.setObjectName("NavActive" if name == title else "NavButton")
            button.style().unpolish(button)
            button.style().polish(button)
        self.notify(f"Открыт раздел: {title}")

    def closeEvent(self, event):
        try:
            self.db.close()
        finally:
            event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("АРМ «Спортивный организатор»")
    app.setWindowIcon(QIcon(ICON_FILE))
    font = QFont("Segoe UI", 10)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
