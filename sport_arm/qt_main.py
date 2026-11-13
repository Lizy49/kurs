"""
PyQt6-интерфейс АРМ «Спортивный организатор».
Бизнес-правила и хранение данных остаются в database.py.
"""

import datetime
import os
import sqlite3
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush, QFont, QPainter, QPen, QKeySequence, QShortcut
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


DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sport_arm.db")
POSITIONS = [
    "Связующий", "Диагональный", "Доигровщик",
    "Центральный блокирующий", "Либеро"
]
SYSTEM_BY_LABEL = {value: key for key, value in SYSTEM_NAMES.items()}


APP_STYLE = """
QWidget {
    background: #f4f6fb;
    color: #182338;
    font-family: "Segoe UI", "Arial";
    font-size: 10pt;
}
QMainWindow { background: #f4f6fb; }
QFrame#Sidebar {
    background: #111b2e;
    border: none;
}
QLabel#SidebarBrand {
    color: #ffffff;
    font-size: 17pt;
    font-weight: 800;
}
QLabel#SidebarSub {
    color: #8fa1bb;
    font-size: 9pt;
}
QLabel#SidebarSection {
    color: #71829d;
    font-size: 8pt;
    font-weight: 800;
    padding: 14px 10px 5px 10px;
}
QPushButton#NavButton {
    background: transparent;
    color: #c4cede;
    text-align: left;
    border: none;
    border-radius: 8px;
    padding: 11px 13px;
    font-weight: 600;
}
QPushButton#NavButton:hover {
    background: #1c2a42;
    color: #ffffff;
}
QPushButton#NavActive {
    background: #253b5d;
    color: #ffffff;
    text-align: left;
    border: none;
    border-left: 3px solid #60a5fa;
    border-radius: 8px;
    padding: 11px 13px;
    font-weight: 700;
}
QFrame#ProfileCard {
    background: #1a2941;
    border: 1px solid #2a3b57;
    border-radius: 10px;
}
QLabel#ProfileName { color: white; font-weight: 700; }
QLabel#ProfileRole { color: #9fb0c8; font-size: 8pt; }
QFrame#Workspace { background: #f4f6fb; border: none; }
QFrame#Topbar {
    background: #ffffff;
    border: none;
    border-bottom: 1px solid #e6ebf2;
}
QLabel#PageTitle {
    color: #17243a;
    font-size: 19pt;
    font-weight: 750;
}
QLabel#PageSubtitle { color: #728097; font-size: 9pt; }
QLabel#Muted { color: #718097; }
QFrame#Surface, QFrame#MetricCard, QGroupBox {
    background: #ffffff;
    border: 1px solid #e5eaf2;
    border-radius: 13px;
}
QFrame#MetricCard { min-height: 108px; }
QLabel#MetricValue {
    color: #15233a;
    font-size: 23pt;
    font-weight: 800;
}
QLabel#MetricTitle { color: #64748b; font-size: 9pt; font-weight: 600; }
QLabel#MetricHint { color: #94a3b8; font-size: 8pt; }
QGroupBox {
    margin-top: 12px;
    padding: 14px 10px 10px 10px;
    font-weight: 700;
    color: #334155;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 5px;
    color: #475569;
}
QPushButton {
    background: #e9eef6;
    color: #26364f;
    border: 1px solid #e0e7f0;
    border-radius: 8px;
    padding: 9px 14px;
    font-weight: 600;
}
QPushButton:hover { background: #dfe7f2; }
QPushButton:pressed { background: #d2deed; }
QPushButton#Primary {
    background: #2563eb;
    color: #ffffff;
    border: 1px solid #2563eb;
}
QPushButton#Primary:hover { background: #1d4ed8; }
QPushButton#Danger {
    background: #fff1f2;
    color: #be123c;
    border: 1px solid #ffe4e6;
}
QPushButton#Danger:hover { background: #ffe4e6; }
QLineEdit, QComboBox {
    background: #ffffff;
    border: 1px solid #dbe3ee;
    border-radius: 8px;
    padding: 9px 10px;
    selection-background-color: #2563eb;
}
QLineEdit:focus, QComboBox:focus { border: 1px solid #60a5fa; }
QTabWidget::pane {
    background: #ffffff;
    border: 1px solid #e1e8f1;
    border-radius: 10px;
    top: -1px;
}
QTabBar::tab {
    background: #e8edf5;
    color: #526078;
    padding: 10px 16px;
    margin-right: 4px;
    border-top-left-radius: 7px;
    border-top-right-radius: 7px;
    font-weight: 600;
}
QTabBar::tab:selected { background: #ffffff; color: #1d4ed8; }
QTableWidget {
    background: #ffffff;
    alternate-background-color: #f8fafd;
    border: 1px solid #e6ebf2;
    border-radius: 9px;
    gridline-color: transparent;
    selection-background-color: #e5efff;
    selection-color: #172033;
}
QHeaderView::section {
    background: #f0f4f9;
    color: #53627a;
    padding: 11px 8px;
    border: none;
    border-bottom: 1px solid #e2e8f0;
    font-weight: 700;
}
QTableWidget::item { padding: 7px; border: none; }
QCheckBox, QRadioButton { spacing: 7px; }
QGraphicsView {
    background: #ffffff;
    border: 1px solid #e5eaf2;
    border-radius: 10px;
}
QStatusBar {
    background: #ffffff;
    color: #68778e;
    border-top: 1px solid #e6ebf2;
}
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
    def __init__(self, app):
        super().__init__()
        self.app = app
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 30, 30, 30)
        root.addStretch(1)

        card = QFrame()
        card.setObjectName("Surface")
        card.setMaximumWidth(570)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 28, 30, 28)
        card_layout.setSpacing(14)

        brand = QLabel("Спортивный организатор")
        brand.setObjectName("PageTitle")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(brand)
        subtitle = QLabel("Автоматизированное рабочее место")
        subtitle.setObjectName("Muted")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(subtitle)

        tabs = QTabWidget()
        login_tab = QWidget()
        login_layout = QVBoxLayout(login_tab)
        login_form = QFormLayout()
        self.login_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.returnPressed.connect(self.do_login)
        login_form.addRow("Логин", self.login_edit)
        login_form.addRow("Пароль", self.password_edit)
        login_layout.addLayout(login_form)
        self.login_error = QLabel("")
        self.login_error.setStyleSheet("color: #b91c1c;")
        login_layout.addWidget(self.login_error)
        login_layout.addWidget(make_button("Войти", self.do_login, "primary"))
        tip = QLabel("Организатор: admin / admin\nДемо-тренер: coach / coach")
        tip.setObjectName("Muted")
        tip.setWordWrap(True)
        login_layout.addWidget(tip)
        tabs.addTab(login_tab, "Вход")

        register_tab = QWidget()
        register_layout = QVBoxLayout(register_tab)
        reg_form = QFormLayout()
        self.reg_login = QLineEdit()
        self.reg_password = QLineEdit()
        self.reg_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.reg_name = QLineEdit()
        self.reg_team = QLineEdit()
        self.reg_city = QLineEdit()
        reg_form.addRow("Логин", self.reg_login)
        reg_form.addRow("Пароль", self.reg_password)
        reg_form.addRow("ФИО тренера / капитана", self.reg_name)
        reg_form.addRow("Название команды", self.reg_team)
        reg_form.addRow("Город", self.reg_city)
        register_layout.addLayout(reg_form)
        register_layout.addWidget(make_button(
            "Зарегистрироваться", self.do_register, "primary"
        ))
        tabs.addTab(register_tab, "Регистрация тренера")
        card_layout.addWidget(tabs)

        centered = QHBoxLayout()
        centered.addStretch(1)
        centered.addWidget(card)
        centered.addStretch(1)
        root.addLayout(centered)
        root.addStretch(1)
        self.login_edit.setFocus()

    def do_login(self):
        user = self.app.db.login(
            self.login_edit.text().strip(), self.password_edit.text()
        )
        if user is None:
            self.login_error.setText("Неверный логин или пароль.")
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


class TournamentsTab(BaseTab):
    def __init__(self, app):
        super().__init__(app)
        self.title("Турниры", "Создавайте соревнования, принимайте заявки и формируйте турнирные сетки.")
        self.toolbar(
            make_button("Создать турнир", self.add, "primary"),
            make_button("Изменить", self.edit),
            make_button("Удалить", self.delete, "danger"),
            make_button("Сформировать сетку", self.generate),
            make_button("Сбросить сетку", self.reset),
            make_button("Загрузить демо-данные", self.demo)
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

    def demo(self):
        try:
            loaded = dbm.load_demo(self.db)
        except (ValidationError, sqlite3.Error) as exc:
            warn(self, "Демо-данные", str(exc))
            return
        if loaded:
            self.app.refresh_all()
            self.app.notify("Демо-данные загружены")
            info(self, "Демо-данные",
                 "Загружены 8 команд и 2 турнира.\nТренер для проверки: coach / coach.")
        else:
            info(self, "Демо-данные",
                 "В базе уже есть команды — демо-данные загружаются только в пустую базу.")


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
    def __init__(self, app):
        super().__init__(app)
        self.title("Команды и составы", "Просмотр зарегистрированных команд и их игроков.")
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.teams = DataTable(
            ["Команда", "Город", "Капитан", "Игроков", "Рейтинг"],
            widths=[190, 120, 175, 85, 85]
        )
        self.players = DataTable(
            ["№", "ФИО", "Амплуа", "Год рождения"],
            widths=[50, 210, 150, 100]
        )
        splitter.addWidget(self.teams)
        splitter.addWidget(self.players)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        self.layout.addWidget(splitter)
        self.teams.itemSelectionChanged.connect(self.show_players)

    def refresh(self):
        self.teams.fill([
            (t["id"], (t["name"], t["city"], t["captain"],
                       t["players_count"], f"{t['rating']:.0f}"), [])
            for t in self.db.list_teams()
        ])
        self.show_players()

    def show_players(self):
        tid = self.teams.selected_id()
        rows = []
        if tid is not None:
            rows = [
                (p["id"], (p["number"], p["full_name"], p["position"], p["birth_year"]), [])
                for p in self.db.list_players(tid)
            ]
        self.players.fill(rows)


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
                make_button("Авто-расписание", self.auto)
            )
            top = None
        if top is not None:
            self.layout.addLayout(top)
        self.table = DataTable(
            ["Тур / стадия", "№", "Команда 1", "Команда 2", "Счёт",
             "Дата", "Время", "Площадка", "Статус"],
            widths=[135, 45, 185, 185, 80, 95, 65, 130, 120]
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
        border = QColor("#f59e0b") if own else QColor("#94a3b8")
        self.scene.addRect(x, y, width, height, QPen(border), QBrush(QColor("#ffffff")))
        self.scene.addLine(x, y + height / 2, x + width, y + height / 2,
                           QPen(QColor("#e2e8f0")))
        for index, (name, score, team_id) in enumerate((
            (match["team1_name"], match["score1"], match["team1_id"]),
            (match["team2_name"], match["score2"], match["team2_id"])
        )):
            text = name or "—"
            if len(text) > 23:
                text = text[:22] + "…"
            if match["winner_id"] is not None and match["winner_id"] == team_id:
                text = "★ " + text
            label = self.scene.addText(text)
            label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold if
                                team_id is not None and match["winner_id"] == team_id else QFont.Weight.Normal))
            label.setDefaultTextColor(QColor("#172033" if name else "#94a3b8"))
            label.setPos(x + 8, y + index * height / 2 + 5)
            if score is not None:
                score_item = self.scene.addText(str(score))
                score_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                score_item.setPos(x + width - 27, y + index * height / 2 + 5)
        when = " ".join(part for part in (
            fmt_date(match["match_date"]), match["match_time"] or "", match["venue"]
        ) if part)
        if when:
            small = self.scene.addText(when)
            small.setFont(QFont("Segoe UI", 7))
            small.setDefaultTextColor(QColor("#64748b"))
            small.setPos(x, y + height + 2)

    def draw_matrix(self, tid, matches):
        table_rows = self.db.standings(tid)
        teams = [r["team_id"] for r in table_rows]
        names = {r["team_id"]: r["name"] for r in table_rows}
        results = {}
        for match in matches:
            if match["status"] == "played":
                results[(match["team1_id"], match["team2_id"])] = (
                    match["score1"], match["score2"]
                )
                results[(match["team2_id"], match["team1_id"])] = (
                    match["score2"], match["score1"]
                )
        cell_w, cell_h = 82, 38
        left = 12
        header = self.scene.addText("Команда / соперник")
        header.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        header.setPos(left, 10)
        for col, team_id in enumerate(teams):
            item = self.scene.addText(str(col + 1))
            item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            item.setPos(left + 230 + col * cell_w, 10)
        for row, team_id in enumerate(teams):
            y = 42 + row * cell_h
            item = self.scene.addText(f"{row + 1}. {names[team_id]}")
            item.setPos(left, y)
            for col, opponent in enumerate(teams):
                if team_id == opponent:
                    value = "■"
                elif (team_id, opponent) in results:
                    score = results[(team_id, opponent)]
                    value = f"{score[0]}:{score[1]}"
                else:
                    value = "·"
                cell = self.scene.addText(value)
                cell.setTextWidth(cell_w - 8)
                cell.setDefaultTextColor(QColor("#2563eb"))
                cell.setPos(left + 230 + col * cell_w, y)
            points = table_rows[row]["points"]
            pts = self.scene.addText(f"{points} очк.")
            pts.setPos(left + 230 + len(teams) * cell_w, y)
        rect = self.scene.itemsBoundingRect()
        self.scene.setSceneRect(rect.adjusted(-10, -10, 35, 20))


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
        self.format = QComboBox()
        self.format.addItem("Excel (.xlsx)", "xlsx")
        self.format.addItem("CSV (.csv)", "csv")
        form.addRow("Что выгрузить", self.kind)
        form.addRow("", self.all_rosters)
        form.addRow("Формат файла", self.format)
        self.layout.addWidget(panel)
        self.layout.addWidget(make_button("Экспортировать…", self.export, "primary"))
        self.layout.addStretch(1)

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
            title, headers, rows = self.db.export_rows(kind, tid)
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
            {"key": "pos", "label": "Амплуа", "kind": "combo_free", "values": POSITIONS},
            {"key": "year", "label": "Год рождения"}
        ]

    def add(self):
        team_id = self.app.team_id()

        def submit(v):
            self.db.add_player(team_id, v["name"], v["number"], v["pos"], v["year"])
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
            "pos": player["position"], "year": player["birth_year"]
        }

        def submit(v):
            self.db.update_player(
                player_id, v["name"], v["number"], v["pos"], v["year"]
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
        self.setCentralWidget(LoginPage(self))

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
            "font-size: 14pt; font-weight: 800;"
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
        sidebar_layout.addSpacing(22)

        self._add_sidebar_heading(sidebar_layout, "ОБЗОР")
        self._add_nav_button(sidebar_layout, "Главная", DashboardTab(self))

        if self.user["role"] == ROLE_ORG:
            self._add_sidebar_heading(sidebar_layout, "УПРАВЛЕНИЕ")
            for title, factory in [
                ("Турниры", TournamentsTab),
                ("Заявки", ApplicationsTab),
                ("Команды", TeamsTab),
                ("Матчи и расписание", MatchesTab),
                ("Сетка", BracketTab)
            ]:
                self._add_nav_button(sidebar_layout, title, factory(self))

            self._add_sidebar_heading(sidebar_layout, "АНАЛИТИКА И ОТЧЁТЫ")
            for title, factory in [
                ("Таблица", StatsTab),
                ("Рейтинг", RatingTab),
                ("Экспорт", ExportTab)
            ]:
                self._add_nav_button(sidebar_layout, title, factory(self))
        else:
            self._add_sidebar_heading(sidebar_layout, "МОЯ КОМАНДА")
            self._add_nav_button(sidebar_layout, "Моя команда", MyTeamTab(self))
            self._add_nav_button(sidebar_layout, "Заявки на турниры", MyApplicationsTab(self))
            self._add_sidebar_heading(sidebar_layout, "СОРЕВНОВАНИЯ")
            self._add_nav_button(
                sidebar_layout, "Расписание", MatchesTab(self, readonly=True)
            )
            self._add_nav_button(sidebar_layout, "Сетка", BracketTab(self))
            self._add_nav_button(sidebar_layout, "Таблица", StatsTab(self))
            self._add_nav_button(sidebar_layout, "Моя статистика", MyStatsTab(self))
            self._add_nav_button(sidebar_layout, "Рейтинг", RatingTab(self))

        sidebar_layout.addStretch(1)

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
            "padding: 8px 11px; font-size: 8pt; font-weight: 800;"
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
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
