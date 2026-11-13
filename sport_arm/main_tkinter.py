"""
АРМ «Спортивный организатор» — курсовая работа, тема 7.

Запуск:  python main.py
Вход организатора: admin / admin.  Тренер регистрируется на вкладке «Регистрация».
Демо-данные загружаются кнопкой на вкладке «Турниры» (затем можно войти как coach / coach).
"""

import datetime
import os
import sqlite3
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import database as dbm
from database import (APP_STATUS, MATCH_STATUS, ROLE_COACH, ROLE_ORG, SYSTEM_NAMES,
                      TOURNAMENT_STATUS, ValidationError, fmt_date)

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sport_arm.db")

# --------------------------------------------------------------- оформление
BG = "#f1f5f9"
CARD = "#ffffff"
DARK = "#0f172a"
PRIMARY = "#2563eb"
PRIMARY_DARK = "#1d4ed8"
MUTED = "#64748b"
GREEN = "#15803d"
RED = "#b91c1c"
AMBER = "#b45309"
ZEBRA = "#f1f5fb"
MINE = "#fef3c7"
FONT = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_SMALL = ("Segoe UI", 8)

SYSTEM_BY_LABEL = {v: k for k, v in SYSTEM_NAMES.items()}
POSITIONS = ["Связующий", "Диагональный", "Доигровщик", "Центральный блокирующий", "Либеро"]


def apply_style(root):
    root.configure(bg=BG)
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure(".", font=FONT, background=BG, foreground=DARK)
    style.configure("TFrame", background=BG)
    style.configure("Card.TFrame", background=CARD)
    style.configure("TLabel", background=BG, foreground=DARK)
    style.configure("Card.TLabel", background=CARD)
    style.configure("Title.TLabel", font=FONT_TITLE, background=BG, foreground=DARK)
    style.configure("Heading.TLabel", font=("Segoe UI", 12, "bold"), background=BG)
    style.configure("Hint.TLabel", foreground=MUTED, background=BG)
    style.configure("Error.TLabel", foreground=RED, background=BG)
    style.configure("Big.TLabel", font=("Segoe UI", 16, "bold"), background=CARD,
                    foreground=PRIMARY)
    style.configure("TButton", padding=(12, 6), borderwidth=0, background="#e2e8f0",
                    foreground=DARK, focuscolor="none")
    style.map("TButton", background=[("active", "#cbd5e1"), ("disabled", "#eef2f6")])
    style.configure("Accent.TButton", background=PRIMARY, foreground="#ffffff")
    style.map("Accent.TButton", background=[("active", PRIMARY_DARK), ("disabled", "#93c5fd")],
              foreground=[("disabled", "#ffffff")])
    style.configure("Danger.TButton", background="#fee2e2", foreground=RED)
    style.map("Danger.TButton", background=[("active", "#fecaca")])
    style.configure("TEntry", padding=5, fieldbackground="#ffffff")
    style.configure("TCombobox", padding=5, fieldbackground="#ffffff")
    style.configure("TCheckbutton", background=BG)
    style.configure("TRadiobutton", background=BG)
    style.configure("TNotebook", background=BG, borderwidth=0, tabmargins=(0, 6, 0, 0))
    style.configure("TNotebook.Tab", padding=(16, 8), font=FONT_BOLD, background="#dbe3ee",
                    foreground=MUTED)
    style.map("TNotebook.Tab", background=[("selected", CARD)],
              foreground=[("selected", PRIMARY)])
    style.configure("Treeview", rowheight=28, font=FONT, background=CARD,
                    fieldbackground=CARD, borderwidth=0)
    style.configure("Treeview.Heading", font=FONT_BOLD, background="#e2e8f0",
                    foreground=DARK, padding=(6, 6), relief="flat")
    style.map("Treeview", background=[("selected", PRIMARY)],
              foreground=[("selected", "#ffffff")])
    # исправление известной ошибки Tk: цвета тегов Treeview не отображаются
    try:
        def fixed_map(option):
            return [e for e in style.map("Treeview", query_opt=option)
                    if e[:2] != ("!disabled", "!selected")]
        style.map("Treeview", foreground=fixed_map("foreground"),
                  background=fixed_map("background"))
    except Exception:
        pass
    return style


# ------------------------------------------------------------ общие виджеты

class DataTree(ttk.Frame):
    """Таблица (Treeview) с прокруткой, зеброй и сохранением выделения при обновлении."""

    def __init__(self, parent, columns, height=12, on_double=None, on_select=None):
        super().__init__(parent)
        self.keys = [c[0] for c in columns]
        self.tree = ttk.Treeview(self, columns=self.keys, show="headings", height=height,
                                 selectmode="browse")
        for col in columns:
            key, head, width = col[0], col[1], col[2]
            anchor = col[3] if len(col) > 3 else "w"
            self.tree.heading(key, text=head)
            self.tree.column(key, width=width, anchor=anchor, minwidth=40)
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.tree.tag_configure("even", background=CARD)
        self.tree.tag_configure("odd", background=ZEBRA)
        self.tree.tag_configure("mine", background=MINE)
        self.tree.tag_configure("ok", foreground=GREEN)
        self.tree.tag_configure("bad", foreground=RED)
        self.tree.tag_configure("warn", foreground=AMBER)
        self.tree.tag_configure("muted", foreground=MUTED)
        if on_double:
            self.tree.bind("<Double-1>", lambda e: on_double() if self.tree.identify_row(e.y) else None)
        if on_select:
            self.tree.bind("<<TreeviewSelect>>", lambda e: on_select())

    def fill(self, rows):
        """rows — список (iid, значения, [теги])."""
        keep = self.selected()
        self.tree.delete(*self.tree.get_children())
        for i, (iid, values, tags) in enumerate(rows):
            base = "mine" if "mine" in tags else ("odd" if i % 2 else "even")
            all_tags = (base,) + tuple(t for t in tags if t != "mine")
            self.tree.insert("", "end", iid=str(iid), values=values, tags=all_tags)
        if keep is not None and self.tree.exists(keep):
            self.tree.selection_set(keep)

    def selected(self):
        sel = self.tree.selection()
        return sel[0] if sel else None

    def selected_int(self):
        sel = self.selected()
        return int(sel) if sel is not None else None


class FormDialog(tk.Toplevel):
    """Универсальное модальное окно с полями. submit(values) бросает ValidationError при ошибке."""

    def __init__(self, parent, title, fields, submit, initial=None, ok_text="Сохранить",
                 hint=None):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.submit = submit
        self.vars = {}
        self.result = None
        initial = initial or {}
        body = ttk.Frame(self, padding=20)
        body.pack(fill="both", expand=True)
        row = 0
        if hint:
            ttk.Label(body, text=hint, style="Hint.TLabel", wraplength=400,
                      justify="left").grid(row=0, column=0, columnspan=2, sticky="w",
                                           pady=(0, 10))
            row = 1
        first = None
        for f in fields:
            ttk.Label(body, text=f["label"]).grid(row=row, column=0, sticky="w", pady=5,
                                                  padx=(0, 14))
            var = tk.StringVar(value=str(initial.get(f["key"], f.get("default", ""))))
            kind = f.get("kind", "entry")
            if kind == "combo":
                widget = ttk.Combobox(body, textvariable=var, values=f["values"],
                                      state="readonly", width=f.get("width", 32))
            elif kind == "combo_free":
                widget = ttk.Combobox(body, textvariable=var, values=f["values"],
                                      width=f.get("width", 32))
            else:
                widget = ttk.Entry(body, textvariable=var, width=f.get("width", 34),
                                   show=f.get("show", ""))
            widget.grid(row=row, column=1, sticky="ew", pady=5)
            first = first or widget
            self.vars[f["key"]] = var
            row += 1
        self.error = tk.StringVar()
        ttk.Label(body, textvariable=self.error, style="Error.TLabel", wraplength=400,
                  justify="left").grid(row=row, column=0, columnspan=2, sticky="w", pady=(6, 0))
        row += 1
        buttons = ttk.Frame(body)
        buttons.grid(row=row, column=0, columnspan=2, sticky="e", pady=(14, 0))
        ttk.Button(buttons, text="Отмена", command=self.destroy).pack(side="right")
        ttk.Button(buttons, text=ok_text, style="Accent.TButton",
                   command=self._ok).pack(side="right", padx=(0, 8))
        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self.destroy())
        self.update_idletasks()
        root = parent.winfo_toplevel()
        x = root.winfo_rootx() + (root.winfo_width() - self.winfo_reqwidth()) // 2
        y = root.winfo_rooty() + (root.winfo_height() - self.winfo_reqheight()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        if first is not None:
            first.focus_set()
        try:
            self.wait_visibility()
            self.grab_set()
        except tk.TclError:
            pass
        self.wait_window(self)

    def _ok(self):
        values = {k: v.get() for k, v in self.vars.items()}
        try:
            self.submit(values)
        except ValidationError as exc:
            self.error.set(str(exc))
            return
        self.result = values
        self.destroy()


class TournamentBox(ttk.Frame):
    """Выпадающий список турниров."""

    def __init__(self, parent, db, on_change, label="Турнир:"):
        super().__init__(parent)
        self.db = db
        self.on_change = on_change
        self.ids = {}
        ttk.Label(self, text=label, font=FONT_BOLD).pack(side="left", padx=(0, 8))
        self.var = tk.StringVar()
        self.combo = ttk.Combobox(self, textvariable=self.var, state="readonly", width=48)
        self.combo.pack(side="left")
        self.combo.bind("<<ComboboxSelected>>", lambda e: self.on_change())

    def reload(self):
        current = self.var.get()
        rows = self.db.list_tournaments()
        self.ids = {r["name"]: r["id"] for r in rows}
        names = list(self.ids)
        self.combo.configure(values=names)
        if current in self.ids:
            self.var.set(current)
        else:
            self.var.set(names[0] if names else "")

    def selected_id(self):
        return self.ids.get(self.var.get())


class Tab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=14)
        self.app = app
        self.db = app.db

    def run(self, func, *args, refresh=True):
        """Выполняет действие, показывая ошибки валидации пользователю."""
        try:
            func(*args)
        except ValidationError as exc:
            messagebox.showerror("Ошибка", str(exc), parent=self)
            return False
        except sqlite3.Error as exc:
            messagebox.showerror("Ошибка базы данных", str(exc), parent=self)
            return False
        if refresh:
            self.app.refresh_all()
        return True

    def toolbar(self):
        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=(0, 10))
        return bar

    def button(self, bar, text, command, style="TButton", side="left"):
        btn = ttk.Button(bar, text=text, command=command, style=style)
        btn.pack(side=side, padx=(0, 8) if side == "left" else (8, 0))
        return btn

    def refresh(self):
        pass


# ---------------------------------------------------------------- вход в систему

class LoginFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        card = ttk.Frame(self, style="Card.TFrame", padding=30)
        card.place(relx=0.5, rely=0.46, anchor="center")
        ttk.Label(card, text="Спортивный организатор", font=FONT_TITLE, style="Card.TLabel",
                  foreground=PRIMARY).pack()
        ttk.Label(card, text="Автоматизированное рабочее место", style="Card.TLabel",
                  foreground=MUTED).pack(pady=(0, 14))
        nb = ttk.Notebook(card)
        nb.pack(fill="both", expand=True)
        # --- вход
        login_tab = ttk.Frame(nb, padding=16)
        nb.add(login_tab, text="Вход")
        self.login_var, self.pass_var = tk.StringVar(), tk.StringVar()
        ttk.Label(login_tab, text="Логин").grid(row=0, column=0, sticky="w", pady=5)
        self.login_entry = ttk.Entry(login_tab, textvariable=self.login_var, width=30)
        self.login_entry.grid(row=0, column=1, pady=5, padx=(12, 0))
        ttk.Label(login_tab, text="Пароль").grid(row=1, column=0, sticky="w", pady=5)
        pass_entry = ttk.Entry(login_tab, textvariable=self.pass_var, show="•", width=30)
        pass_entry.grid(row=1, column=1, pady=5, padx=(12, 0))
        self.login_error = tk.StringVar()
        ttk.Label(login_tab, textvariable=self.login_error, style="Error.TLabel").grid(
            row=2, column=0, columnspan=2, sticky="w")
        ttk.Button(login_tab, text="Войти", style="Accent.TButton",
                   command=self.do_login).grid(row=3, column=0, columnspan=2, sticky="ew",
                                               pady=(10, 6))
        ttk.Label(login_tab, text="Организатор: admin / admin\nДемо-тренер: coach / coach "
                  "(после загрузки демо-данных)", style="Hint.TLabel",
                  justify="left").grid(row=4, column=0, columnspan=2, sticky="w")
        pass_entry.bind("<Return>", lambda e: self.do_login())
        self.login_entry.bind("<Return>", lambda e: self.do_login())
        # --- регистрация тренера
        reg_tab = ttk.Frame(nb, padding=16)
        nb.add(reg_tab, text="Регистрация тренера")
        self.reg = {k: tk.StringVar() for k in ("login", "password", "name", "team", "city")}
        labels = [("login", "Логин"), ("password", "Пароль"), ("name", "ФИО тренера/капитана"),
                  ("team", "Название команды"), ("city", "Город")]
        for i, (key, label) in enumerate(labels):
            ttk.Label(reg_tab, text=label).grid(row=i, column=0, sticky="w", pady=4)
            ttk.Entry(reg_tab, textvariable=self.reg[key], width=30,
                      show="•" if key == "password" else "").grid(row=i, column=1, pady=4,
                                                                  padx=(12, 0))
        self.reg_error = tk.StringVar()
        ttk.Label(reg_tab, textvariable=self.reg_error, style="Error.TLabel",
                  wraplength=330).grid(row=5, column=0, columnspan=2, sticky="w")
        ttk.Button(reg_tab, text="Зарегистрироваться", style="Accent.TButton",
                   command=self.do_register).grid(row=6, column=0, columnspan=2, sticky="ew",
                                                  pady=(8, 0))
        self.login_entry.focus_set()

    def do_login(self):
        user = self.app.db.login(self.login_var.get(), self.pass_var.get())
        if user is None:
            self.login_error.set("Неверный логин или пароль.")
            return
        self.login_error.set("")
        self.app.login_ok(user)

    def do_register(self):
        r = self.reg
        try:
            self.app.db.register_coach(r["login"].get(), r["password"].get(), r["name"].get(),
                                       r["team"].get(), r["city"].get())
        except ValidationError as exc:
            self.reg_error.set(str(exc))
            return
        self.reg_error.set("")
        user = self.app.db.login(r["login"].get(), r["password"].get())
        self.app.login_ok(user)


# ------------------------------------------------------ вкладки организатора

class TournamentsTab(Tab):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        bar = self.toolbar()
        self.button(bar, "Создать турнир", self.add, "Accent.TButton")
        self.button(bar, "Изменить", self.edit)
        self.button(bar, "Удалить", self.delete, "Danger.TButton")
        self.button(bar, "Сформировать сетку", self.generate)
        self.button(bar, "Сбросить сетку", self.reset)
        self.button(bar, "Загрузить демо-данные", self.demo, side="right")
        self.table = DataTree(self, [
            ("name", "Название", 220), ("sport", "Вид спорта", 110),
            ("system", "Система", 180), ("dates", "Даты", 180), ("place", "Место", 150),
            ("status", "Статус", 110), ("teams", "Команд", 70, "center"),
            ("winner", "Победитель", 140)], on_double=self.edit)
        self.table.pack(fill="both", expand=True)
        ttk.Label(self, text="Порядок работы: создайте турнир → тренеры подают заявки → "
                  "одобрите заявки → «Сформировать сетку» → введите результаты матчей.",
                  style="Hint.TLabel").pack(anchor="w", pady=(10, 0))

    def refresh(self):
        rows = []
        for t in self.db.list_tournaments():
            rows.append((t["id"], (
                t["name"], t["sport"], SYSTEM_NAMES[t["system"]],
                f"{fmt_date(t['start_date'])} – {fmt_date(t['end_date'])}", t["place"],
                TOURNAMENT_STATUS[t["status"]], t["teams_count"],
                self.db.tournament_winner(t["id"]) or "—"), []))
        self.table.fill(rows)

    def _fields(self):
        return [
            {"key": "name", "label": "Название"},
            {"key": "sport", "label": "Вид спорта"},
            {"key": "system", "label": "Система", "kind": "combo",
             "values": list(SYSTEM_NAMES.values())},
            {"key": "start", "label": "Дата начала (ДД.ММ.ГГГГ)"},
            {"key": "end", "label": "Дата окончания (ДД.ММ.ГГГГ)"},
            {"key": "place", "label": "Место проведения"},
        ]

    def add(self):
        today = datetime.date.today()
        initial = {"sport": "Волейбол", "system": SYSTEM_NAMES["olympic"],
                   "start": fmt_date((today + datetime.timedelta(days=7)).isoformat()),
                   "end": fmt_date((today + datetime.timedelta(days=14)).isoformat())}

        def submit(v):
            dbm_system = SYSTEM_BY_LABEL.get(v["system"], "")
            self.db.create_tournament(v["name"], v["sport"], dbm_system, v["start"], v["end"],
                                      v["place"])
        dlg = FormDialog(self, "Новый турнир", self._fields(), submit, initial)
        if dlg.result:
            self.app.notify("Турнир создан")
            self.app.refresh_all()

    def edit(self):
        tid = self.table.selected_int()
        if tid is None:
            messagebox.showinfo("Изменение", "Выберите турнир в списке.", parent=self)
            return
        t = self.db.get_tournament(tid)
        initial = {"name": t["name"], "sport": t["sport"], "system": SYSTEM_NAMES[t["system"]],
                   "start": fmt_date(t["start_date"]), "end": fmt_date(t["end_date"]),
                   "place": t["place"]}

        def submit(v):
            self.db.update_tournament(tid, v["name"], v["sport"],
                                      SYSTEM_BY_LABEL.get(v["system"], ""), v["start"], v["end"],
                                      v["place"])
        dlg = FormDialog(self, "Изменение турнира", self._fields(), submit, initial)
        if dlg.result:
            self.app.notify("Изменения сохранены")
            self.app.refresh_all()

    def delete(self):
        tid = self.table.selected_int()
        if tid is None:
            messagebox.showinfo("Удаление", "Выберите турнир в списке.", parent=self)
            return
        t = self.db.get_tournament(tid)
        if messagebox.askyesno("Удаление турнира",
                               f"Удалить турнир «{t['name']}» со всеми заявками и матчами?\n"
                               "Рейтинг команд будет пересчитан.", parent=self):
            if self.run(self.db.delete_tournament, tid):
                self.app.notify("Турнир удалён")

    def generate(self):
        tid = self.table.selected_int()
        if tid is None:
            messagebox.showinfo("Сетка", "Выберите турнир в списке.", parent=self)
            return
        if self.db.match_count(tid) and not messagebox.askyesno(
                "Пересоздать сетку", "Сетка уже сформирована. Сформировать заново?\n"
                "(Возможно, только если результатов ещё нет.)", parent=self):
            return
        if self.run(self.db.generate_bracket, tid):
            self.app.notify("Сетка сформирована")
            self.app.goto("Матчи и расписание")

    def reset(self):
        tid = self.table.selected_int()
        if tid is None:
            messagebox.showinfo("Сетка", "Выберите турнир в списке.", parent=self)
            return
        if not self.db.match_count(tid):
            messagebox.showinfo("Сетка", "У этого турнира ещё нет сетки.", parent=self)
            return
        if messagebox.askyesno("Сброс сетки", "Удалить сетку и расписание турнира и вернуться "
                               "к приёму заявок?", parent=self):
            if self.run(self.db.reset_bracket, tid):
                self.app.notify("Сетка сброшена, турнир снова принимает заявки")

    def demo(self):
        if dbm.load_demo(self.db):
            self.app.notify("Демо-данные загружены")
            self.app.refresh_all()
            messagebox.showinfo("Демо-данные", "Загружены 8 команд и 2 турнира.\n"
                                "Тренер для проверки: логин coach, пароль coach.", parent=self)
        else:
            messagebox.showinfo("Демо-данные", "В базе уже есть команды — демо-данные "
                                "загружаются только в пустую базу.", parent=self)


class ApplicationsTab(Tab):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.box = TournamentBox(self, self.db, self.fill)
        self.box.pack(anchor="w", pady=(0, 10))
        bar = self.toolbar()
        self.button(bar, "Одобрить", lambda: self.set_status("approved"), "Accent.TButton")
        self.button(bar, "Отклонить", lambda: self.set_status("rejected"), "Danger.TButton")
        self.button(bar, "Вернуть на рассмотрение", lambda: self.set_status("pending"))
        self.button(bar, "Одобрить все", self.approve_all)
        self.table = DataTree(self, [
            ("team", "Команда", 210), ("city", "Город", 130), ("captain", "Капитан", 170),
            ("players", "Игроков", 80, "center"), ("rating", "Рейтинг", 80, "center"),
            ("status", "Статус", 140), ("created", "Подана", 140)])
        self.table.pack(fill="both", expand=True)
        self.info = tk.StringVar()
        ttk.Label(self, textvariable=self.info, style="Hint.TLabel").pack(anchor="w", pady=(10, 0))

    def refresh(self):
        self.box.reload()
        self.fill()

    def fill(self):
        tid = self.box.selected_id()
        rows = []
        self.info.set("")
        if tid:
            t = self.db.get_tournament(tid)
            if t["status"] != "registration":
                self.info.set("Турнир уже начался — заявки изменять нельзя "
                              "(сначала «Сбросить сетку» на вкладке «Турниры»).")
            else:
                self.info.set("Приём заявок открыт. Одобренные команды попадут в сетку.")
            tags = {"approved": "ok", "rejected": "bad", "pending": "warn"}
            for a in self.db.list_applications(tid):
                rows.append((a["id"], (a["team_name"], a["city"], a["captain"],
                                       a["players_count"], f"{a['rating']:.0f}",
                                       APP_STATUS[a["status"]], a["created_at"]),
                             [tags[a["status"]]]))
        self.table.fill(rows)

    def set_status(self, status):
        app_id = self.table.selected_int()
        if app_id is None:
            messagebox.showinfo("Заявки", "Выберите заявку в списке.", parent=self)
            return
        if self.run(self.db.set_application_status, app_id, status):
            self.app.notify("Статус заявки обновлён")

    def approve_all(self):
        tid = self.box.selected_id()
        if tid is None:
            return

        def work():
            for a in self.db.list_applications(tid):
                if a["status"] == "pending":
                    self.db.set_application_status(a["id"], "approved")
        if self.run(work):
            self.app.notify("Все заявки одобрены")


class TeamsTab(Tab):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        ttk.Label(self, text="Команды и составы", style="Heading.TLabel").pack(anchor="w",
                                                                              pady=(0, 8))
        panes = ttk.Frame(self)
        panes.pack(fill="both", expand=True)
        panes.columnconfigure(0, weight=3)
        panes.columnconfigure(1, weight=2)
        panes.rowconfigure(0, weight=1)
        self.teams = DataTree(panes, [
            ("name", "Команда", 190), ("city", "Город", 110), ("captain", "Капитан", 150),
            ("players", "Игроков", 70, "center"), ("rating", "Рейтинг", 70, "center")],
            on_select=self.show_players)
        self.teams.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.players = DataTree(panes, [
            ("number", "№", 45, "center"), ("name", "ФИО", 200), ("pos", "Амплуа", 110),
            ("year", "Год", 60, "center")])
        self.players.grid(row=0, column=1, sticky="nsew")

    def refresh(self):
        self.teams.fill([(t["id"], (t["name"], t["city"], t["captain"], t["players_count"],
                                    f"{t['rating']:.0f}"), []) for t in self.db.list_teams()])
        self.show_players()

    def show_players(self):
        tid = self.teams.selected_int()
        rows = []
        if tid is not None:
            rows = [(p["id"], (p["number"], p["full_name"], p["position"], p["birth_year"]), [])
                    for p in self.db.list_players(tid)]
        self.players.fill(rows)


class MatchesTab(Tab):
    """Матчи и расписание. Для тренера — только просмотр."""

    def __init__(self, parent, app, readonly=False):
        super().__init__(parent, app)
        self.readonly = readonly
        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, 10))
        self.box = TournamentBox(top, self.db, self.fill)
        self.box.pack(side="left")
        self.only_mine = tk.BooleanVar(value=False)
        if readonly:
            ttk.Checkbutton(top, text="Только матчи моей команды", variable=self.only_mine,
                            command=self.fill).pack(side="left", padx=20)
        else:
            bar = self.toolbar()
            self.button(bar, "Ввести результат", self.result, "Accent.TButton")
            self.button(bar, "Очистить результат", self.clear, "Danger.TButton")
            self.button(bar, "Назначить время и место", self.schedule)
            self.button(bar, "Авто-расписание", self.auto)
        self.table = DataTree(self, [
            ("round", "Тур / стадия", 130), ("no", "№", 40, "center"),
            ("t1", "Команда 1", 190), ("t2", "Команда 2", 190),
            ("score", "Счёт", 90, "center"), ("date", "Дата", 90, "center"),
            ("time", "Время", 60, "center"), ("venue", "Площадка", 120),
            ("status", "Статус", 110)], on_double=None if readonly else self.result)
        self.table.pack(fill="both", expand=True)
        self.info = tk.StringVar()
        ttk.Label(self, textvariable=self.info, style="Hint.TLabel").pack(anchor="w", pady=(10, 0))

    def refresh(self):
        self.box.reload()
        self.fill()

    def fill(self):
        tid = self.box.selected_id()
        mine = self.app.team_id() if self.readonly else None
        rows = []
        self.info.set("")
        if tid:
            matches = self.db.list_matches(tid)
            if not matches:
                self.info.set("Сетка ещё не сформирована.")
            for m in matches:
                is_mine = mine is not None and mine in (m["team1_id"], m["team2_id"])
                if self.readonly and self.only_mine.get() and not is_mine:
                    continue
                tags = []
                if is_mine:
                    tags.append("mine")
                if m["status"] == "played":
                    tags.append("ok")
                elif m["status"] == "bye":
                    tags.append("muted")
                rows.append((m["id"], (
                    m["round_name"], m["position"], m["team1_name"] or "—",
                    m["team2_name"] or "—", self.db.score_text(m), fmt_date(m["match_date"]),
                    m["match_time"] or "", m["venue"], MATCH_STATUS[m["status"]]), tags))
        self.table.fill(rows)

    def _selected_match(self):
        mid = self.table.selected_int()
        if mid is None:
            messagebox.showinfo("Матчи", "Выберите матч в списке.", parent=self)
            return None
        return self.db.get_match(mid)

    def result(self):
        m = self._selected_match()
        if m is None:
            return
        if m["status"] == "bye":
            messagebox.showinfo("Матч", "Это автопроход — результат не вводится.", parent=self)
            return
        if not m["team1_id"] or not m["team2_id"]:
            messagebox.showinfo("Матч", "Соперники ещё не определены.", parent=self)
            return
        initial = {}
        if m["status"] == "played":
            initial = {"s1": m["score1"], "s2": m["score2"]}
        fields = [{"key": "s1", "label": f"Выиграно сетов: {m['team1_name']}", "width": 12},
                  {"key": "s2", "label": f"Выиграно сетов: {m['team2_name']}", "width": 12}]

        def submit(v):
            self.db.record_result(m["id"], v["s1"], v["s2"])
        dlg = FormDialog(self, f"{m['team1_name']} — {m['team2_name']}", fields, submit, initial,
                         hint="В олимпийской системе ничья невозможна.")
        if dlg.result:
            self.app.notify("Результат сохранён, рейтинг пересчитан")
            self.app.refresh_all()

    def clear(self):
        m = self._selected_match()
        if m is None:
            return
        if m["status"] != "played":
            messagebox.showinfo("Матч", "У этого матча нет результата.", parent=self)
            return
        if messagebox.askyesno("Очистка результата", "Очистить результат матча?", parent=self):
            if self.run(self.db.clear_result, m["id"]):
                self.app.notify("Результат очищен")

    def schedule(self):
        m = self._selected_match()
        if m is None:
            return
        if m["status"] == "bye":
            messagebox.showinfo("Матч", "Для автопрохода расписание не назначается.", parent=self)
            return
        initial = {"date": fmt_date(m["match_date"]), "time": m["match_time"] or "",
                   "venue": m["venue"]}
        fields = [{"key": "date", "label": "Дата (ДД.ММ.ГГГГ)", "width": 20},
                  {"key": "time", "label": "Время (ЧЧ:ММ)", "width": 20},
                  {"key": "venue", "label": "Площадка", "width": 30}]

        def submit(v):
            self.db.set_match_schedule(m["id"], v["date"], v["time"], v["venue"])
        dlg = FormDialog(self, "Время и место матча", fields, submit, initial,
                         hint="Чтобы сбросить расписание, очистите дату и время.")
        if dlg.result:
            self.app.notify("Расписание матча обновлено")
            self.app.refresh_all()

    def auto(self):
        tid = self.box.selected_id()
        if tid is None:
            messagebox.showinfo("Расписание", "Сначала создайте турнир.", parent=self)
            return
        fields = [{"key": "venues", "label": "Площадки (через запятую)", "width": 34},
                  {"key": "per_day", "label": "Матчей в день на площадке", "width": 10},
                  {"key": "start", "label": "Начало первого матча", "width": 10},
                  {"key": "minutes", "label": "Длительность слота (мин)", "width": 10}]
        initial = {"venues": "Зал 1, Зал 2", "per_day": "4", "start": "10:00", "minutes": "120"}

        def submit(v):
            self.db.auto_schedule(tid, v["venues"].split(","), v["per_day"], v["start"],
                                  v["minutes"])
        dlg = FormDialog(self, "Автоматическое расписание", fields, submit, initial,
                         ok_text="Составить",
                         hint="Матчи распределяются по датам турнира без накладок команд и "
                              "площадок. Прежнее расписание будет заменено.")
        if dlg.result:
            self.app.notify("Расписание составлено")
            self.app.refresh_all()


class BracketTab(Tab):
    """Турнирная сетка: схема для олимпийской системы и таблица встреч для круговой."""
    BW, BH, GX, GY = 200, 54, 60, 26

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.box = TournamentBox(self, self.db, self.fill)
        self.box.pack(anchor="w", pady=(0, 10))
        self.area = ttk.Frame(self)
        self.area.pack(fill="both", expand=True)

    def refresh(self):
        self.box.reload()
        self.fill()

    def _clear(self):
        for w in self.area.winfo_children():
            w.destroy()

    def _message(self, text):
        ttk.Label(self.area, text=text, style="Hint.TLabel").pack(pady=40)

    def fill(self):
        self._clear()
        tid = self.box.selected_id()
        if tid is None:
            self._message("Нет турниров.")
            return
        t = self.db.get_tournament(tid)
        matches = self.db.list_matches(tid)
        if not matches:
            self._message("Сетка ещё не сформирована.")
            return
        winner = self.db.tournament_winner(tid)
        if winner:
            ttk.Label(self.area, text=f"Победитель турнира: {winner}", font=FONT_BOLD,
                      foreground=GREEN).pack(anchor="w", pady=(0, 6))
        if t["system"] == "olympic":
            self._draw_olympic(matches)
        else:
            self._draw_matrix(tid, matches)

    def _short(self, name, limit=22):
        if not name:
            return "—"
        return name if len(name) <= limit else name[:limit - 1] + "…"

    def _draw_olympic(self, matches):
        holder = ttk.Frame(self.area)
        holder.pack(fill="both", expand=True)
        canvas = tk.Canvas(holder, bg=CARD, highlightthickness=0)
        sy = ttk.Scrollbar(holder, orient="vertical", command=canvas.yview)
        sx = ttk.Scrollbar(holder, orient="horizontal", command=canvas.xview)
        canvas.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        sy.grid(row=0, column=1, sticky="ns")
        sx.grid(row=1, column=0, sticky="ew")
        holder.rowconfigure(0, weight=1)
        holder.columnconfigure(0, weight=1)
        mine = self.app.team_id()
        bw, bh, gx, gy = self.BW, self.BH, self.GX, self.GY
        rounds = {}
        for m in matches:
            rounds.setdefault(m["round"], []).append(m)
        centers = {}
        for r in sorted(rounds):
            ms = sorted(rounds[r], key=lambda m: m["position"])
            x = 20 + (r - 1) * (bw + gx)
            canvas.create_text(x + bw / 2, 20, text=ms[0]["round_name"], font=FONT_BOLD,
                               fill=PRIMARY)
            for i, m in enumerate(ms):
                if r == 1:
                    yc = 44 + i * (bh + gy) + bh / 2
                else:
                    yc = (centers[(r - 1, 2 * i)] + centers[(r - 1, 2 * i + 1)]) / 2
                centers[(r, i)] = yc
                self._box(canvas, x, yc - bh / 2, m, mine)
                if r > 1:
                    px = x - gx - bw + bw
                    for j in (2 * i, 2 * i + 1):
                        py = centers[(r - 1, j)]
                        canvas.create_line(px, py, px + gx / 2, py, px + gx / 2, yc, x, yc,
                                           fill="#94a3b8", width=2)
        box = canvas.bbox("all")
        if box:
            canvas.configure(scrollregion=(0, 0, box[2] + 30, box[3] + 30))

    def _box(self, canvas, x, y, m, mine):
        bw, bh = self.BW, self.BH
        is_mine = mine is not None and mine in (m["team1_id"], m["team2_id"])
        canvas.create_rectangle(x, y, x + bw, y + bh, fill="#ffffff",
                                outline="#f59e0b" if is_mine else "#94a3b8",
                                width=3 if is_mine else 1)
        canvas.create_line(x, y + bh / 2, x + bw, y + bh / 2, fill="#e2e8f0")
        for idx, (name, score, team_id) in enumerate((
                (m["team1_name"], m["score1"], m["team1_id"]),
                (m["team2_name"], m["score2"], m["team2_id"]))):
            ry = y + idx * bh / 2
            won = m["winner_id"] is not None and m["winner_id"] == team_id
            if won:
                canvas.create_rectangle(x + 1, ry + 1, x + bw - 1, ry + bh / 2 - 1,
                                        fill="#dcfce7", outline="")
            canvas.create_text(x + 8, ry + bh / 4, text=self._short(name), anchor="w",
                               font=FONT_BOLD if won else FONT,
                               fill=DARK if name else MUTED)
            if score is not None:
                canvas.create_text(x + bw - 10, ry + bh / 4, text=str(score), anchor="e",
                                   font=FONT_BOLD)
        if m["status"] == "bye":
            canvas.create_text(x + bw - 8, y + bh / 4 + (bh / 2 if not m["team2_id"] else 0),
                               text="автопроход", anchor="e", font=FONT_SMALL, fill=MUTED)
        when = " ".join(x for x in (fmt_date(m["match_date"]), m["match_time"] or "",
                                    m["venue"]) if x)
        if when:
            canvas.create_text(x, y + bh + 3, text=when, anchor="nw", font=FONT_SMALL,
                               fill=MUTED)

    def _draw_matrix(self, tid, matches):
        table = self.db.standings(tid)
        order = [r["team_id"] for r in table]
        names = {r["team_id"]: r["name"] for r in table}
        results = {}
        for m in matches:
            if m["status"] == "played":
                results[(m["team1_id"], m["team2_id"])] = (m["score1"], m["score2"])
                results[(m["team2_id"], m["team1_id"])] = (m["score2"], m["score1"])
        cols = ["team"] + [f"c{i}" for i in range(len(order))] + ["pts"]
        holder = ttk.Frame(self.area)
        holder.pack(fill="both", expand=True)
        tree = ttk.Treeview(holder, columns=cols, show="headings", selectmode="none")
        tree.heading("team", text="Команда")
        tree.column("team", width=210, anchor="w")
        for i in range(len(order)):
            tree.heading(f"c{i}", text=str(i + 1))
            tree.column(f"c{i}", width=64, anchor="center", minwidth=40)
        tree.heading("pts", text="Очки")
        tree.column("pts", width=70, anchor="center")
        tree.tag_configure("odd", background=ZEBRA)
        tree.tag_configure("mine", background=MINE)
        mine = self.app.team_id()
        for i, a in enumerate(order):
            cells = [f"{i + 1}. {names[a]}"]
            for b in order:
                if a == b:
                    cells.append("■")
                elif (a, b) in results:
                    s = results[(a, b)]
                    cells.append(f"{s[0]}:{s[1]}")
                else:
                    cells.append("·")
            cells.append(table[i]["points"])
            tag = "mine" if a == mine else ("odd" if i % 2 else "even")
            tree.insert("", "end", values=cells, tags=(tag,))
        tree.pack(fill="both", expand=True)
        ttk.Label(holder, text="Строка — команда, столбец — соперник. «·» — матч ещё не сыгран.",
                  style="Hint.TLabel").pack(anchor="w", pady=(8, 0))


class StatsTab(Tab):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.box = TournamentBox(self, self.db, self.fill)
        self.box.pack(anchor="w", pady=(0, 10))
        self.table = DataTree(self, [
            ("place", "Место", 60, "center"), ("name", "Команда", 220),
            ("played", "И", 50, "center"), ("wins", "В", 50, "center"),
            ("draws", "Н", 50, "center"), ("losses", "П", 50, "center"),
            ("gf", "Сеты +", 70, "center"), ("ga", "Сеты −", 70, "center"),
            ("diff", "Разница", 80, "center"), ("points", "Очки", 70, "center"),
            ("rating", "Рейтинг", 80, "center")])
        self.table.pack(fill="both", expand=True)
        self.info = tk.StringVar()
        ttk.Label(self, textvariable=self.info, style="Hint.TLabel").pack(anchor="w", pady=(10, 0))

    def refresh(self):
        self.box.reload()
        self.fill()

    def fill(self):
        tid = self.box.selected_id()
        rows = []
        self.info.set("")
        if tid:
            t = self.db.get_tournament(tid)
            mine = self.app.team_id()
            for r in self.db.standings(tid):
                rows.append((r["team_id"], (
                    r["place"], r["name"], r["played"], r["wins"], r["draws"], r["losses"],
                    r["gf"], r["ga"], f"{r['diff']:+d}" if r["diff"] else "0", r["points"],
                    f"{r['rating']:.0f}"), ["mine"] if r["team_id"] == mine else []))
            if t["system"] == "olympic":
                self.info.set("Олимпийская система: места сортируются по числу побед, "
                              "затем по разнице сетов.")
            else:
                self.info.set("Круговая система: победа — 3 очка, ничья — 1, поражение — 0.")
        self.table.fill(rows)


class RatingTab(Tab):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        bar = self.toolbar()
        self.button(bar, "Пересчитать рейтинг", self.recalc, "Accent.TButton")
        ttk.Label(bar, text="Рейтинг считается автоматически по системе Эло: старт 1000 очков, "
                  "коэффициент K = 32.", style="Hint.TLabel").pack(side="left", padx=10)
        self.table = DataTree(self, [
            ("place", "Место", 60, "center"), ("name", "Команда", 220), ("city", "Город", 140),
            ("rating", "Рейтинг", 90, "center"), ("played", "Игры", 70, "center"),
            ("wins", "Победы", 80, "center"), ("draws", "Ничьи", 80, "center"),
            ("losses", "Поражения", 90, "center")])
        self.table.pack(fill="both", expand=True)

    def refresh(self):
        mine = self.app.team_id()
        self.table.fill([(r["team_id"], (
            r["place"], r["name"], r["city"], f"{r['rating']:.1f}", r["played"], r["wins"],
            r["draws"], r["losses"]), ["mine"] if r["team_id"] == mine else [])
            for r in self.db.ratings_table()])

    def recalc(self):
        if self.run(self.db.recalc_ratings):
            self.app.notify("Рейтинг пересчитан")


class ExportTab(Tab):
    KINDS = [("standings", "Турнирная таблица (выбранный турнир)"),
             ("schedule", "Расписание и результаты матчей (выбранный турнир)"),
             ("applications", "Заявки команд (выбранный турнир)"),
             ("roster", "Составы команд"),
             ("ratings", "Рейтинг команд")]

    def __init__(self, parent, app):
        super().__init__(parent, app)
        ttk.Label(self, text="Экспорт данных в табличные форматы", style="Heading.TLabel").pack(
            anchor="w", pady=(0, 10))
        self.box = TournamentBox(self, self.db, lambda: None)
        self.box.pack(anchor="w", pady=(0, 12))
        self.kind = tk.StringVar(value="standings")
        for key, label in self.KINDS:
            ttk.Radiobutton(self, text=label, value=key, variable=self.kind).pack(anchor="w",
                                                                                  pady=2)
        self.all_rosters = tk.BooleanVar(value=False)
        ttk.Checkbutton(self, text="Составы: выгрузить все команды (а не только участников "
                        "выбранного турнира)", variable=self.all_rosters).pack(anchor="w",
                                                                              pady=(8, 0))
        fmt = ttk.Frame(self)
        fmt.pack(anchor="w", pady=14)
        ttk.Label(fmt, text="Формат файла:", font=FONT_BOLD).pack(side="left", padx=(0, 10))
        self.fmt = tk.StringVar(value="xlsx")
        ttk.Radiobutton(fmt, text="Excel (.xlsx)", value="xlsx", variable=self.fmt).pack(
            side="left", padx=(0, 10))
        ttk.Radiobutton(fmt, text="CSV (.csv)", value="csv", variable=self.fmt).pack(side="left")
        ttk.Button(self, text="Экспортировать…", style="Accent.TButton",
                   command=self.export).pack(anchor="w")

    def refresh(self):
        self.box.reload()

    def export(self):
        kind = self.kind.get()
        tid = self.box.selected_id()
        if kind == "roster" and self.all_rosters.get():
            tid = None
        elif kind == "roster" and tid is None:
            messagebox.showinfo("Экспорт", "Выберите турнир или отметьте «все команды».",
                                parent=self)
            return
        try:
            title, headers, rows = self.db.export_rows(kind, tid)
        except ValidationError as exc:
            messagebox.showerror("Экспорт", str(exc), parent=self)
            return
        if not rows:
            messagebox.showinfo("Экспорт", "Нет данных для выгрузки.", parent=self)
            return
        ext = self.fmt.get()
        path = filedialog.asksaveasfilename(
            parent=self, title="Сохранить файл", defaultextension=f".{ext}",
            initialfile=f"{title}_{datetime.date.today().isoformat()}.{ext}",
            filetypes=[("Excel", "*.xlsx")] if ext == "xlsx" else [("CSV", "*.csv")])
        if not path:
            return
        try:
            dbm.export_to_file(path, title, headers, rows)
        except ValidationError as exc:
            messagebox.showerror("Экспорт", str(exc), parent=self)
            return
        except OSError as exc:
            messagebox.showerror("Экспорт", f"Не удалось сохранить файл:\n{exc}\n"
                                 "Возможно, он открыт в другой программе.", parent=self)
            return
        self.app.notify(f"Файл сохранён: {path}")
        messagebox.showinfo("Экспорт", f"Готово! Выгружено строк: {len(rows)}.\n{path}",
                            parent=self)


# --------------------------------------------------------- вкладки тренера

class MyTeamTab(Tab):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._loaded = None
        ttk.Label(self, text="Моя команда", style="Heading.TLabel").pack(anchor="w")
        form = ttk.Frame(self)
        form.pack(fill="x", pady=10)
        self.vars = {k: tk.StringVar() for k in ("name", "city", "captain")}
        for i, (key, label, width) in enumerate([("name", "Название", 28), ("city", "Город", 18),
                                                  ("captain", "Капитан / тренер", 26)]):
            ttk.Label(form, text=label).grid(row=0, column=i * 2, sticky="w", padx=(0, 6))
            ttk.Entry(form, textvariable=self.vars[key], width=width).grid(
                row=0, column=i * 2 + 1, padx=(0, 16))
        ttk.Button(form, text="Сохранить", style="Accent.TButton",
                   command=self.save_team).grid(row=0, column=6)
        ttk.Label(self, text="Состав команды", style="Heading.TLabel").pack(anchor="w",
                                                                           pady=(8, 6))
        bar = self.toolbar()
        self.button(bar, "Добавить игрока", self.add, "Accent.TButton")
        self.button(bar, "Изменить", self.edit)
        self.button(bar, "Удалить", self.delete, "Danger.TButton")
        self.count = tk.StringVar()
        ttk.Label(bar, textvariable=self.count, style="Hint.TLabel").pack(side="right")
        self.table = DataTree(self, [
            ("number", "№", 60, "center"), ("name", "ФИО", 280), ("pos", "Амплуа", 160),
            ("year", "Год рождения", 120, "center")], on_double=self.edit)
        self.table.pack(fill="both", expand=True)

    def refresh(self):
        team = self.db.get_team(self.app.team_id())
        if team is None:
            return
        # поля перезаполняем только если пользователь их не редактировал
        loaded = {"name": team["name"], "city": team["city"], "captain": team["captain"]}
        if self._loaded is None or all(
                self.vars[k].get() == self._loaded[k] for k in loaded):
            for k, val in loaded.items():
                self.vars[k].set(val)
        self._loaded = loaded
        players = self.db.list_players(team["id"])
        self.count.set(f"Игроков: {len(players)} (для заявки нужно не меньше "
                       f"{dbm.MIN_ROSTER}, максимум {dbm.MAX_ROSTER})")
        self.table.fill([(p["id"], (p["number"], p["full_name"], p["position"],
                                    p["birth_year"]), []) for p in players])

    def save_team(self):
        v = self.vars
        if self.run(self.db.update_team, self.app.team_id(), v["name"].get(), v["city"].get(),
                    v["captain"].get()):
            self.app.notify("Данные команды сохранены")

    def _fields(self):
        return [{"key": "name", "label": "ФИО игрока"},
                {"key": "number", "label": "Номер (0–99)", "width": 10},
                {"key": "pos", "label": "Амплуа", "kind": "combo_free", "values": POSITIONS},
                {"key": "year", "label": "Год рождения", "width": 10}]

    def add(self):
        team_id = self.app.team_id()

        def submit(v):
            self.db.add_player(team_id, v["name"], v["number"], v["pos"], v["year"])
        dlg = FormDialog(self, "Новый игрок", self._fields(), submit, {"year": "2004"})
        if dlg.result:
            self.app.notify("Игрок добавлен")
            self.app.refresh_all()

    def edit(self):
        pid = self.table.selected_int()
        if pid is None:
            messagebox.showinfo("Состав", "Выберите игрока в списке.", parent=self)
            return
        p = next(x for x in self.db.list_players(self.app.team_id()) if x["id"] == pid)
        initial = {"name": p["full_name"], "number": p["number"], "pos": p["position"],
                   "year": p["birth_year"]}

        def submit(v):
            self.db.update_player(pid, v["name"], v["number"], v["pos"], v["year"])
        dlg = FormDialog(self, "Изменение игрока", self._fields(), submit, initial)
        if dlg.result:
            self.app.notify("Данные игрока сохранены")
            self.app.refresh_all()

    def delete(self):
        pid = self.table.selected_int()
        if pid is None:
            messagebox.showinfo("Состав", "Выберите игрока в списке.", parent=self)
            return
        if messagebox.askyesno("Удаление", "Удалить игрока из состава?", parent=self):
            if self.run(self.db.delete_player, pid):
                self.app.notify("Игрок удалён")


class MyApplicationsTab(Tab):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        ttk.Label(self, text="Турниры с открытым приёмом заявок",
                  style="Heading.TLabel").pack(anchor="w")
        bar = self.toolbar()
        self.button(bar, "Подать заявку", self.submit, "Accent.TButton")
        self.open_table = DataTree(self, [
            ("name", "Турнир", 240), ("sport", "Вид спорта", 120), ("system", "Система", 190),
            ("dates", "Даты", 190), ("place", "Место", 160)], height=6, on_double=self.submit)
        self.open_table.pack(fill="both", expand=True)
        ttk.Label(self, text="Мои заявки", style="Heading.TLabel").pack(anchor="w", pady=(14, 0))
        bar2 = self.toolbar()
        self.button(bar2, "Отозвать заявку", self.withdraw, "Danger.TButton")
        self.my_table = DataTree(self, [
            ("name", "Турнир", 240), ("status", "Статус заявки", 150),
            ("tstatus", "Статус турнира", 140), ("created", "Подана", 150)], height=6)
        self.my_table.pack(fill="both", expand=True)

    def refresh(self):
        self.open_table.fill([(t["id"], (
            t["name"], t["sport"], SYSTEM_NAMES[t["system"]],
            f"{fmt_date(t['start_date'])} – {fmt_date(t['end_date'])}", t["place"]), [])
            for t in self.db.list_tournaments("registration")])
        tags = {"approved": "ok", "rejected": "bad", "pending": "warn"}
        self.my_table.fill([(a["id"], (
            a["tournament_name"], APP_STATUS[a["status"]],
            TOURNAMENT_STATUS[a["tournament_status"]], a["created_at"]), [tags[a["status"]]])
            for a in self.db.list_applications(team_id=self.app.team_id())])

    def submit(self):
        tid = self.open_table.selected_int()
        if tid is None:
            messagebox.showinfo("Заявка", "Выберите турнир в верхнем списке.", parent=self)
            return
        if self.run(self.db.submit_application, tid, self.app.team_id()):
            self.app.notify("Заявка подана и ждёт решения организатора")

    def withdraw(self):
        aid = self.my_table.selected_int()
        if aid is None:
            messagebox.showinfo("Заявка", "Выберите заявку в нижнем списке.", parent=self)
            return
        if messagebox.askyesno("Отзыв заявки", "Отозвать выбранную заявку?", parent=self):
            if self.run(self.db.withdraw_application, aid):
                self.app.notify("Заявка отозвана")


class MyStatsTab(Tab):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        ttk.Label(self, text="Статистика выступлений", style="Heading.TLabel").pack(anchor="w")
        cards = ttk.Frame(self)
        cards.pack(fill="x", pady=10)
        self.values = {}
        for i, (key, label) in enumerate([
                ("rating", "Рейтинг"), ("place", "Место в рейтинге"), ("played", "Матчей"),
                ("wld", "Победы / ничьи / поражения"), ("goals", "Сеты выиграно / проиграно"),
                ("points", "Очки")]):
            card = ttk.Frame(cards, style="Card.TFrame", padding=(14, 10))
            card.grid(row=0, column=i, padx=(0, 10), sticky="nsew")
            var = tk.StringVar(value="—")
            ttk.Label(card, textvariable=var, style="Big.TLabel").pack(anchor="w")
            ttk.Label(card, text=label, style="Card.TLabel", foreground=MUTED).pack(anchor="w")
            self.values[key] = var
        ttk.Label(self, text="История матчей", style="Heading.TLabel").pack(anchor="w",
                                                                           pady=(8, 6))
        self.table = DataTree(self, [
            ("tournament", "Турнир", 200), ("round", "Тур / стадия", 120),
            ("opponent", "Соперник", 190), ("score", "Счёт", 80, "center"),
            ("outcome", "Итог", 100), ("date", "Дата", 90, "center"),
            ("time", "Время", 60, "center")])
        self.table.pack(fill="both", expand=True)

    def refresh(self):
        team_id = self.app.team_id()
        s = self.db.team_stats(team_id)
        team = self.db.get_team(team_id)
        place = next((r["place"] for r in self.db.ratings_table() if r["team_id"] == team_id), "—")
        self.values["rating"].set(f"{team['rating']:.0f}")
        self.values["place"].set(str(place))
        self.values["played"].set(str(s["played"]))
        self.values["wld"].set(f"{s['wins']} / {s['draws']} / {s['losses']}")
        self.values["goals"].set(f"{s['gf']} / {s['ga']}")
        self.values["points"].set(str(s["points"]))
        tags = {"Победа": "ok", "Поражение": "bad", "Ничья": "warn", "Впереди": "muted"}
        self.table.fill([(i, (h["tournament"], h["round"], h["opponent"], h["score"],
                              h["outcome"], h["date"], h["time"]), [tags[h["outcome"]]])
                         for i, h in enumerate(self.db.team_history(team_id))])


# ------------------------------------------------------------ главное окно

class App(tk.Tk):
    def __init__(self, db_path=None):
        super().__init__()
        self.title("АРМ «Спортивный организатор»")
        self.geometry("1200x740")
        self.minsize(1000, 640)
        self.db = dbm.Database(db_path or DB_FILE)
        self.user = None
        self.tabs = []
        self.notebook = None
        self.status = tk.StringVar()
        apply_style(self)
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<F5>", lambda e: self.refresh_all())
        self.show_login()

    def report_callback_exception(self, exc, val, tb):
        messagebox.showerror("Непредвиденная ошибка", f"{exc.__name__}: {val}")

    def on_close(self):
        try:
            self.db.close()
        finally:
            self.destroy()

    def _clear(self):
        for w in self.container.winfo_children():
            w.destroy()
        self.tabs = []
        self.notebook = None

    def show_login(self):
        self.user = None
        self._clear()
        LoginFrame(self.container, self).pack(fill="both", expand=True)

    def login_ok(self, user):
        self.user = user
        self.show_main()

    def team_id(self):
        if self.user is None or self.user["role"] != ROLE_COACH:
            return None
        row = self.db.get_user(self.user["id"])
        return row["team_id"] if row else None

    def show_main(self):
        self._clear()
        header = tk.Frame(self.container, bg=DARK)
        header.pack(fill="x")
        tk.Label(header, text="Спортивный организатор", bg=DARK, fg="#ffffff",
                 font=("Segoe UI", 14, "bold")).pack(side="left", padx=18, pady=12)
        role = "организатор" if self.user["role"] == ROLE_ORG else "тренер"
        tk.Label(header, text=f"{self.user['full_name']} · {role}", bg=DARK, fg="#cbd5e1",
                 font=FONT).pack(side="left", padx=10)
        ttk.Button(header, text="Выйти", command=self.show_login).pack(side="right", padx=18)
        ttk.Button(header, text="Обновить (F5)", command=self.refresh_all).pack(side="right")
        tk.Label(self.container, textvariable=self.status, anchor="w", bg="#e2e8f0", fg=MUTED,
                 font=FONT, padx=14, pady=4).pack(side="bottom", fill="x")
        self.notebook = ttk.Notebook(self.container)
        self.notebook.pack(fill="both", expand=True, padx=14, pady=(8, 10))
        if self.user["role"] == ROLE_ORG:
            spec = [("Турниры", TournamentsTab), ("Заявки", ApplicationsTab),
                    ("Команды", TeamsTab), ("Матчи и расписание", MatchesTab),
                    ("Сетка", BracketTab), ("Таблица", StatsTab), ("Рейтинг", RatingTab),
                    ("Экспорт", ExportTab)]
        else:
            spec = [("Моя команда", MyTeamTab), ("Заявки на турниры", MyApplicationsTab),
                    ("Расписание", lambda p, a: MatchesTab(p, a, readonly=True)),
                    ("Сетка", BracketTab), ("Таблица", StatsTab),
                    ("Моя статистика", MyStatsTab), ("Рейтинг", RatingTab)]
        for title, factory in spec:
            tab = factory(self.notebook, self)
            self.notebook.add(tab, text=title)
            self.tabs.append((title, tab))
        self.status.set("Готово")
        self.refresh_all()

    def refresh_all(self):
        for _, tab in self.tabs:
            tab.refresh()

    def goto(self, title):
        for name, tab in self.tabs:
            if name == title:
                self.notebook.select(tab)
                return

    def notify(self, text):
        self.status.set(text)


def main():
    App().mainloop()


if __name__ == "__main__":
    main()
