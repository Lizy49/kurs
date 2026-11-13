"""
database.py — логика и хранение данных АРМ «Спортивный организатор».

Модуль не зависит от tkinter, поэтому его можно тестировать отдельно
(см. tests/test_logic.py).

Возможности:
  * пользователи (организатор / тренер-капитан), пароли хранятся в виде хеша;
  * команды и составы игроков;
  * турниры (олимпийская и круговая системы);
  * заявки команд на участие;
  * генерация турнирных сеток, расписание матчей, ввод результатов;
  * автоматический расчёт рейтинга команд (система Эло);
  * статистика, турнирные таблицы;
  * экспорт данных в CSV и XLSX.
"""

import csv
import datetime
import hashlib
import secrets
import sqlite3

ROLE_ORG = "organizer"
ROLE_COACH = "coach"

SYSTEM_NAMES = {
    "olympic": "Олимпийская (на выбывание)",
    "round_robin": "Круговая",
}
TOURNAMENT_STATUS = {
    "registration": "Приём заявок",
    "running": "Идёт",
    "finished": "Завершён",
}
APP_STATUS = {
    "pending": "На рассмотрении",
    "approved": "Одобрена",
    "rejected": "Отклонена",
}
MATCH_STATUS = {
    "scheduled": "Запланирован",
    "played": "Сыгран",
    "bye": "Автопроход",
}

START_RATING = 1000.0
ELO_K = 32
MIN_ROSTER = 5      # минимальный состав для подачи заявки
MAX_ROSTER = 30     # максимальный состав команды


class ValidationError(Exception):
    """Ошибка проверки данных — текст показывается пользователю."""


# ---------------------------------------------------------------- утилиты

def parse_date(text):
    """Принимает ДД.ММ.ГГГГ или ГГГГ-ММ-ДД, возвращает строку ISO."""
    text = (text or "").strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            pass
    raise ValidationError("Дата должна быть в формате ДД.ММ.ГГГГ (например, 25.05.2026).")


def fmt_date(iso):
    if not iso:
        return ""
    try:
        return datetime.date.fromisoformat(iso).strftime("%d.%m.%Y")
    except ValueError:
        return iso


def parse_time(text):
    text = (text or "").strip()
    try:
        return datetime.datetime.strptime(text, "%H:%M").strftime("%H:%M")
    except ValueError:
        raise ValidationError("Время должно быть в формате ЧЧ:ММ (например, 14:30).")


def parse_int(text, label, lo=None, hi=None):
    try:
        value = int(str(text).strip())
    except (TypeError, ValueError):
        raise ValidationError(f"Поле «{label}» должно быть целым числом.")
    if lo is not None and value < lo:
        raise ValidationError(f"Поле «{label}» не может быть меньше {lo}.")
    if hi is not None and value > hi:
        raise ValidationError(f"Поле «{label}» не может быть больше {hi}.")
    return value


def need_text(text, label, max_len=80):
    text = (text or "").strip()
    if not text:
        raise ValidationError(f"Поле «{label}» обязательно для заполнения.")
    if len(text) > max_len:
        raise ValidationError(f"Поле «{label}» слишком длинное (максимум {max_len} символов).")
    return text


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                                 salt.encode("utf-8"), 50_000).hex()
    return f"{salt}${digest}"


def check_password(password, stored):
    salt, _ = stored.split("$", 1)
    return secrets.compare_digest(hash_password(password, salt), stored)


def _collate_nocase(a, b):
    a, b = a.casefold(), b.casefold()
    return (a > b) - (a < b)


def seed_order(size):
    """Порядок посева для сетки на выбывание: 1-й сильнейший встречается с последним."""
    order = [1]
    while len(order) < size:
        n = len(order) * 2
        order = [x for s in order for x in (s, n + 1 - s)]
    return order


def round_title(matches_in_round):
    return {1: "Финал", 2: "Полуфинал", 4: "Четвертьфинал"}.get(
        matches_in_round, f"1/{matches_in_round} финала")


SCHEMA = """
CREATE TABLE IF NOT EXISTS teams(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE COLLATE RUNOCASE,
    city TEXT NOT NULL DEFAULT '',
    captain TEXT NOT NULL DEFAULT '',
    rating REAL NOT NULL DEFAULT 1000
);
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    login TEXT NOT NULL UNIQUE COLLATE RUNOCASE,
    pass_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    full_name TEXT NOT NULL DEFAULT '',
    team_id INTEGER REFERENCES teams(id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS players(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    number INTEGER NOT NULL,
    position TEXT NOT NULL DEFAULT '',
    birth_year INTEGER NOT NULL,
    UNIQUE(team_id, number)
);
CREATE TABLE IF NOT EXISTS tournaments(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE COLLATE RUNOCASE,
    sport TEXT NOT NULL DEFAULT '',
    system TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    place TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'registration'
);
CREATE TABLE IF NOT EXISTS applications(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id INTEGER NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    UNIQUE(tournament_id, team_id)
);
CREATE TABLE IF NOT EXISTS matches(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id INTEGER NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
    round INTEGER NOT NULL,
    position INTEGER NOT NULL,
    round_name TEXT NOT NULL DEFAULT '',
    team1_id INTEGER REFERENCES teams(id),
    team2_id INTEGER REFERENCES teams(id),
    score1 INTEGER,
    score2 INTEGER,
    winner_id INTEGER REFERENCES teams(id),
    match_date TEXT,
    match_time TEXT,
    venue TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'scheduled',
    next_match_id INTEGER,
    next_slot INTEGER
);
"""


class Database:
    def __init__(self, path="sport_arm.db"):
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        # встроенный NOCASE не понимает кириллицу — регистрируем свою сортировку
        self.conn.create_collation("RUNOCASE", _collate_nocase)
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.executescript(SCHEMA)
        self.conn.commit()
        self._seed_admin()

    def close(self):
        self.conn.close()

    def _seed_admin(self):
        row = self.conn.execute("SELECT 1 FROM users WHERE role=?", (ROLE_ORG,)).fetchone()
        if row is None:
            self.conn.execute(
                "INSERT INTO users(login, pass_hash, role, full_name) VALUES(?,?,?,?)",
                ("admin", hash_password("admin"), ROLE_ORG, "Главный организатор"))
            self.conn.commit()

    # ------------------------------------------------------- пользователи

    def login(self, login, password):
        row = self.conn.execute("SELECT * FROM users WHERE login=?",
                                ((login or "").strip(),)).fetchone()
        if row and check_password(password or "", row["pass_hash"]):
            return row
        return None

    def get_user(self, user_id):
        return self.conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()

    def register_coach(self, login, password, full_name, team_name, city=""):
        login = need_text(login, "Логин", 30)
        if len(login) < 3:
            raise ValidationError("Логин должен содержать минимум 3 символа.")
        if len(password or "") < 4:
            raise ValidationError("Пароль должен содержать минимум 4 символа.")
        full_name = need_text(full_name, "ФИО")
        team_name = need_text(team_name, "Название команды")
        city = (city or "").strip()
        if self.conn.execute("SELECT 1 FROM users WHERE login=?", (login,)).fetchone():
            raise ValidationError("Пользователь с таким логином уже существует.")
        if self.conn.execute("SELECT 1 FROM teams WHERE name=?", (team_name,)).fetchone():
            raise ValidationError("Команда с таким названием уже существует.")
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO teams(name, city, captain) VALUES(?,?,?)",
                (team_name, city, full_name))
            team_id = cur.lastrowid
            cur = self.conn.execute(
                "INSERT INTO users(login, pass_hash, role, full_name, team_id) VALUES(?,?,?,?,?)",
                (login, hash_password(password), ROLE_COACH, full_name, team_id))
        return cur.lastrowid

    # ------------------------------------------------------------ команды

    def list_teams(self):
        return self.conn.execute(
            "SELECT t.*, (SELECT COUNT(*) FROM players p WHERE p.team_id=t.id) AS players_count "
            "FROM teams t ORDER BY t.name").fetchall()

    def get_team(self, team_id):
        return self.conn.execute(
            "SELECT t.*, (SELECT COUNT(*) FROM players p WHERE p.team_id=t.id) AS players_count "
            "FROM teams t WHERE t.id=?", (team_id,)).fetchone()

    def update_team(self, team_id, name, city, captain):
        name = need_text(name, "Название команды")
        city = (city or "").strip()
        captain = (captain or "").strip()
        dup = self.conn.execute("SELECT 1 FROM teams WHERE name=? AND id<>?",
                                (name, team_id)).fetchone()
        if dup:
            raise ValidationError("Команда с таким названием уже существует.")
        with self.conn:
            self.conn.execute("UPDATE teams SET name=?, city=?, captain=? WHERE id=?",
                              (name, city, captain, team_id))

    # ------------------------------------------------------------ игроки

    def list_players(self, team_id):
        return self.conn.execute(
            "SELECT * FROM players WHERE team_id=? ORDER BY number", (team_id,)).fetchall()

    def _check_player(self, team_id, full_name, number, position, birth_year, player_id=None):
        full_name = need_text(full_name, "ФИО игрока")
        number = parse_int(number, "Номер", 0, 99)
        year_now = datetime.date.today().year
        birth_year = parse_int(birth_year, "Год рождения", 1950, year_now - 5)
        position = (position or "").strip()
        dup = self.conn.execute(
            "SELECT 1 FROM players WHERE team_id=? AND number=? AND id<>?",
            (team_id, number, player_id or -1)).fetchone()
        if dup:
            raise ValidationError(f"В команде уже есть игрок с номером {number}.")
        return full_name, number, position, birth_year

    def add_player(self, team_id, full_name, number, position, birth_year):
        count = self.conn.execute("SELECT COUNT(*) FROM players WHERE team_id=?",
                                  (team_id,)).fetchone()[0]
        if count >= MAX_ROSTER:
            raise ValidationError(f"В составе не может быть больше {MAX_ROSTER} игроков.")
        full_name, number, position, birth_year = self._check_player(
            team_id, full_name, number, position, birth_year)
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO players(team_id, full_name, number, position, birth_year) "
                "VALUES(?,?,?,?,?)", (team_id, full_name, number, position, birth_year))
        return cur.lastrowid

    def update_player(self, player_id, full_name, number, position, birth_year):
        row = self.conn.execute("SELECT team_id FROM players WHERE id=?", (player_id,)).fetchone()
        if row is None:
            raise ValidationError("Игрок не найден.")
        full_name, number, position, birth_year = self._check_player(
            row["team_id"], full_name, number, position, birth_year, player_id)
        with self.conn:
            self.conn.execute(
                "UPDATE players SET full_name=?, number=?, position=?, birth_year=? WHERE id=?",
                (full_name, number, position, birth_year, player_id))

    def delete_player(self, player_id):
        with self.conn:
            self.conn.execute("DELETE FROM players WHERE id=?", (player_id,))

    # ------------------------------------------------------------ турниры

    def _check_tournament(self, name, sport, system, start, end, place, tid=None):
        name = need_text(name, "Название турнира")
        sport = need_text(sport, "Вид спорта", 40)
        if system not in SYSTEM_NAMES:
            raise ValidationError("Выберите систему проведения турнира.")
        start_iso = parse_date(start)
        end_iso = parse_date(end)
        if end_iso < start_iso:
            raise ValidationError("Дата окончания не может быть раньше даты начала.")
        place = (place or "").strip()
        dup = self.conn.execute("SELECT 1 FROM tournaments WHERE name=? AND id<>?",
                                (name, tid or -1)).fetchone()
        if dup:
            raise ValidationError("Турнир с таким названием уже существует.")
        return name, sport, system, start_iso, end_iso, place

    def create_tournament(self, name, sport, system, start, end, place=""):
        values = self._check_tournament(name, sport, system, start, end, place)
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO tournaments(name, sport, system, start_date, end_date, place) "
                "VALUES(?,?,?,?,?,?)", values)
        return cur.lastrowid

    def update_tournament(self, tid, name, sport, system, start, end, place=""):
        t = self.get_tournament(tid)
        if t is None:
            raise ValidationError("Турнир не найден.")
        if system != t["system"] and self.match_count(tid):
            raise ValidationError("Нельзя менять систему турнира после формирования сетки. "
                                  "Сначала сбросьте сетку.")
        values = self._check_tournament(name, sport, system, start, end, place, tid)
        with self.conn:
            self.conn.execute(
                "UPDATE tournaments SET name=?, sport=?, system=?, start_date=?, end_date=?, "
                "place=? WHERE id=?", values + (tid,))

    def delete_tournament(self, tid):
        with self.conn:
            self.conn.execute("DELETE FROM tournaments WHERE id=?", (tid,))
        self.recalc_ratings()

    def get_tournament(self, tid):
        return self.conn.execute("SELECT * FROM tournaments WHERE id=?", (tid,)).fetchone()

    def list_tournaments(self, status=None):
        sql = ("SELECT t.*, (SELECT COUNT(*) FROM applications a "
               "WHERE a.tournament_id=t.id AND a.status='approved') AS teams_count "
               "FROM tournaments t")
        args = ()
        if status:
            sql += " WHERE t.status=?"
            args = (status,)
        sql += " ORDER BY t.start_date DESC, t.id DESC"
        return self.conn.execute(sql, args).fetchall()

    def match_count(self, tid):
        return self.conn.execute("SELECT COUNT(*) FROM matches WHERE tournament_id=?",
                                 (tid,)).fetchone()[0]

    def tournament_winner(self, tid):
        t = self.get_tournament(tid)
        if t is None or t["status"] != "finished":
            return None
        if t["system"] == "olympic":
            row = self.conn.execute(
                "SELECT winner_id FROM matches WHERE tournament_id=? ORDER BY round DESC LIMIT 1",
                (tid,)).fetchone()
            if row and row["winner_id"]:
                return self.get_team(row["winner_id"])["name"]
            return None
        table = self.standings(tid)
        return table[0]["name"] if table else None

    # -------------------------------------------------------------- заявки

    def submit_application(self, tournament_id, team_id):
        t = self.get_tournament(tournament_id)
        if t is None:
            raise ValidationError("Турнир не найден.")
        if t["status"] != "registration":
            raise ValidationError("Приём заявок на этот турнир закрыт.")
        team = self.get_team(team_id)
        if team is None:
            raise ValidationError("Команда не найдена.")
        if team["players_count"] < MIN_ROSTER:
            raise ValidationError(
                f"Для подачи заявки в составе должно быть минимум {MIN_ROSTER} игроков "
                f"(сейчас {team['players_count']}).")
        if self.conn.execute("SELECT 1 FROM applications WHERE tournament_id=? AND team_id=?",
                             (tournament_id, team_id)).fetchone():
            raise ValidationError("Заявка на этот турнир уже подана.")
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO applications(tournament_id, team_id, created_at) VALUES(?,?,?)",
                (tournament_id, team_id,
                 datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        return cur.lastrowid

    def withdraw_application(self, app_id):
        app = self.conn.execute("SELECT * FROM applications WHERE id=?", (app_id,)).fetchone()
        if app is None:
            raise ValidationError("Заявка не найдена.")
        t = self.get_tournament(app["tournament_id"])
        if t["status"] != "registration":
            raise ValidationError("Турнир уже начался — отозвать заявку нельзя.")
        with self.conn:
            self.conn.execute("DELETE FROM applications WHERE id=?", (app_id,))

    def set_application_status(self, app_id, status):
        if status not in APP_STATUS:
            raise ValidationError("Неизвестный статус заявки.")
        app = self.conn.execute("SELECT * FROM applications WHERE id=?", (app_id,)).fetchone()
        if app is None:
            raise ValidationError("Заявка не найдена.")
        t = self.get_tournament(app["tournament_id"])
        if t["status"] != "registration":
            raise ValidationError("Нельзя менять заявки: турнир уже начался. "
                                  "Сначала сбросьте сетку, если результатов ещё нет.")
        with self.conn:
            self.conn.execute("UPDATE applications SET status=? WHERE id=?", (status, app_id))

    def list_applications(self, tournament_id=None, team_id=None):
        sql = ("SELECT a.*, t.name AS team_name, t.city, t.captain, t.rating, "
               "(SELECT COUNT(*) FROM players p WHERE p.team_id=t.id) AS players_count, "
               "tr.name AS tournament_name, tr.status AS tournament_status "
               "FROM applications a JOIN teams t ON t.id=a.team_id "
               "JOIN tournaments tr ON tr.id=a.tournament_id WHERE 1=1")
        args = []
        if tournament_id is not None:
            sql += " AND a.tournament_id=?"
            args.append(tournament_id)
        if team_id is not None:
            sql += " AND a.team_id=?"
            args.append(team_id)
        sql += " ORDER BY a.created_at, a.id"
        return self.conn.execute(sql, args).fetchall()

    def approved_teams(self, tid):
        return self.conn.execute(
            "SELECT t.* FROM applications a JOIN teams t ON t.id=a.team_id "
            "WHERE a.tournament_id=? AND a.status='approved' "
            "ORDER BY t.rating DESC, t.name", (tid,)).fetchall()

    # -------------------------------------------------- сетка и расписание

    def generate_bracket(self, tid):
        """Формирует матчи турнира по его системе (удаляя прежнюю сетку без результатов)."""
        t = self.get_tournament(tid)
        if t is None:
            raise ValidationError("Турнир не найден.")
        played = self.conn.execute(
            "SELECT COUNT(*) FROM matches WHERE tournament_id=? AND status='played'",
            (tid,)).fetchone()[0]
        if played:
            raise ValidationError("Нельзя пересоздать сетку: уже внесены результаты матчей.")
        teams = self.approved_teams(tid)
        if len(teams) < 2:
            raise ValidationError("Для формирования сетки нужно минимум 2 одобренные заявки.")
        with self.conn:
            self.conn.execute("DELETE FROM matches WHERE tournament_id=?", (tid,))
            if t["system"] == "olympic":
                self._gen_olympic(tid, teams)
            else:
                self._gen_round_robin(tid, teams)
            self.conn.execute("UPDATE tournaments SET status='running' WHERE id=?", (tid,))

    def _insert_match(self, tid, rnd, pos, name, t1=None, t2=None):
        cur = self.conn.execute(
            "INSERT INTO matches(tournament_id, round, position, round_name, team1_id, team2_id) "
            "VALUES(?,?,?,?,?,?)", (tid, rnd, pos, name, t1, t2))
        return cur.lastrowid

    def _gen_olympic(self, tid, teams):
        n = len(teams)
        size = 1
        while size < n:
            size *= 2
        rounds = size.bit_length() - 1
        slots = [teams[s - 1]["id"] if s <= n else None for s in seed_order(size)]
        ids = {}
        for r in range(1, rounds + 1):
            count = size >> r
            for p in range(count):
                t1 = slots[2 * p] if r == 1 else None
                t2 = slots[2 * p + 1] if r == 1 else None
                ids[(r, p)] = self._insert_match(tid, r, p + 1, round_title(count), t1, t2)
        for r in range(1, rounds):
            for p in range(size >> r):
                self.conn.execute("UPDATE matches SET next_match_id=?, next_slot=? WHERE id=?",
                                  (ids[(r + 1, p // 2)], p % 2 + 1, ids[(r, p)]))
        # автопроходы: команды без соперника в первом круге
        for p in range(size // 2):
            a, b = slots[2 * p], slots[2 * p + 1]
            if (a is None) != (b is None):
                winner = a or b
                mid = ids[(1, p)]
                self.conn.execute("UPDATE matches SET status='bye', winner_id=? WHERE id=?",
                                  (winner, mid))
                if rounds > 1:
                    col = "team1_id" if p % 2 == 0 else "team2_id"
                    self.conn.execute(f"UPDATE matches SET {col}=? WHERE id=?",
                                      (winner, ids[(2, p // 2)]))

    def _gen_round_robin(self, tid, teams):
        ids = [t["id"] for t in teams]
        if len(ids) % 2:
            ids.append(None)
        n = len(ids)
        rot = ids[:]
        for r in range(n - 1):
            pairs = []
            for i in range(n // 2):
                a, b = rot[i], rot[n - 1 - i]
                if a is None or b is None:
                    continue
                if i == 0 and r % 2 == 1:
                    a, b = b, a
                pairs.append((a, b))
            for k, (a, b) in enumerate(pairs):
                self._insert_match(tid, r + 1, k + 1, f"Тур {r + 1}", a, b)
            rot = [rot[0]] + [rot[-1]] + rot[1:-1]

    def reset_bracket(self, tid):
        t = self.get_tournament(tid)
        if t is None:
            raise ValidationError("Турнир не найден.")
        if self.conn.execute("SELECT COUNT(*) FROM matches WHERE tournament_id=? "
                             "AND status='played'", (tid,)).fetchone()[0]:
            raise ValidationError("Нельзя сбросить сетку: уже внесены результаты матчей.")
        with self.conn:
            self.conn.execute("DELETE FROM matches WHERE tournament_id=?", (tid,))
            self.conn.execute("UPDATE tournaments SET status='registration' WHERE id=?", (tid,))

    def list_matches(self, tid):
        rows = self.conn.execute(
            "SELECT m.*, a.name AS team1_name, b.name AS team2_name, w.name AS winner_name "
            "FROM matches m LEFT JOIN teams a ON a.id=m.team1_id "
            "LEFT JOIN teams b ON b.id=m.team2_id LEFT JOIN teams w ON w.id=m.winner_id "
            "WHERE m.tournament_id=? ORDER BY m.round, m.position", (tid,)).fetchall()
        return rows

    def get_match(self, match_id):
        return self.conn.execute(
            "SELECT m.*, a.name AS team1_name, b.name AS team2_name "
            "FROM matches m LEFT JOIN teams a ON a.id=m.team1_id "
            "LEFT JOIN teams b ON b.id=m.team2_id WHERE m.id=?", (match_id,)).fetchone()

    @staticmethod
    def score_text(m):
        if m["status"] == "bye":
            return "автопроход"
        if m["score1"] is None or m["score2"] is None:
            return "—"
        return f"{m['score1']} : {m['score2']}"

    def set_match_schedule(self, match_id, date_text, time_text, venue):
        m = self.get_match(match_id)
        if m is None:
            raise ValidationError("Матч не найден.")
        if m["status"] == "bye":
            raise ValidationError("Для автопрохода расписание не назначается.")
        venue = (venue or "").strip()
        if not (date_text or "").strip() and not (time_text or "").strip():
            date_iso = time_iso = None
        else:
            date_iso = parse_date(date_text)
            time_iso = parse_time(time_text)
            t = self.get_tournament(m["tournament_id"])
            if not (t["start_date"] <= date_iso <= t["end_date"]):
                raise ValidationError(
                    f"Дата матча должна быть в пределах турнира: "
                    f"{fmt_date(t['start_date'])} – {fmt_date(t['end_date'])}.")
            self._check_conflicts(m, date_iso, time_iso, venue)
        with self.conn:
            self.conn.execute(
                "UPDATE matches SET match_date=?, match_time=?, venue=? WHERE id=?",
                (date_iso, time_iso, venue, match_id))

    def _check_conflicts(self, m, date_iso, time_iso, venue):
        others = self.conn.execute(
            "SELECT * FROM matches WHERE id<>? AND match_date=? AND match_time=? "
            "AND status<>'bye'", (m["id"], date_iso, time_iso)).fetchall()
        mine = {x for x in (m["team1_id"], m["team2_id"]) if x}
        for o in others:
            if venue and o["venue"] and o["venue"].lower() == venue.lower():
                raise ValidationError(
                    f"Площадка «{venue}» уже занята в это время другим матчем.")
            theirs = {x for x in (o["team1_id"], o["team2_id"]) if x}
            if mine & theirs:
                raise ValidationError("Одна из команд уже играет в это время.")

    def auto_schedule(self, tid, venues, slots_per_day=4, start_time="10:00", slot_minutes=120):
        """Автоматически распределяет матчи по датам, времени и площадкам без накладок."""
        t = self.get_tournament(tid)
        if t is None:
            raise ValidationError("Турнир не найден.")
        venues = [v.strip() for v in venues if v and v.strip()]
        if not venues:
            raise ValidationError("Укажите хотя бы одну площадку.")
        slots_per_day = parse_int(slots_per_day, "Матчей в день на площадке", 1, 12)
        slot_minutes = parse_int(slot_minutes, "Длительность слота (мин)", 30, 480)
        start = datetime.datetime.strptime(parse_time(start_time), "%H:%M")
        last = start + datetime.timedelta(minutes=slot_minutes * (slots_per_day - 1))
        if last.date() != start.date():
            raise ValidationError("Слишком много матчей в день: расписание выходит за полночь.")
        matches = [m for m in self.list_matches(tid) if m["status"] != "bye"]
        if not matches:
            raise ValidationError("Сначала сформируйте сетку турнира.")
        day0 = datetime.date.fromisoformat(t["start_date"])
        day_end = datetime.date.fromisoformat(t["end_date"])
        plan = []
        slot = 0
        by_round = {}
        for m in matches:
            by_round.setdefault(m["round"], []).append(m)
        for rnd in sorted(by_round):
            row = by_round[rnd]
            for i in range(0, len(row), len(venues)):
                chunk = row[i:i + len(venues)]
                day = day0 + datetime.timedelta(days=slot // slots_per_day)
                if day > day_end:
                    raise ValidationError(
                        "Матчи не помещаются в даты турнира. Увеличьте число матчей в день, "
                        "добавьте площадки или продлите турнир.")
                clock = start + datetime.timedelta(minutes=slot_minutes * (slot % slots_per_day))
                for j, m in enumerate(chunk):
                    plan.append((day.isoformat(), clock.strftime("%H:%M"), venues[j], m["id"]))
                slot += 1
        with self.conn:
            for d, tm, v, mid in plan:
                self.conn.execute(
                    "UPDATE matches SET match_date=?, match_time=?, venue=? WHERE id=?",
                    (d, tm, v, mid))
        return len(plan)

    # ----------------------------------------------------------- результаты

    def record_result(self, match_id, score1, score2):
        m = self.get_match(match_id)
        if m is None:
            raise ValidationError("Матч не найден.")
        if m["status"] == "bye":
            raise ValidationError("Для автопрохода результат не вводится.")
        if not m["team1_id"] or not m["team2_id"]:
            raise ValidationError("Соперники ещё не определены — сначала сыграйте предыдущие матчи.")
        s1 = parse_int(score1, "Счёт 1-й команды", 0, 999)
        s2 = parse_int(score2, "Счёт 2-й команды", 0, 999)
        t = self.get_tournament(m["tournament_id"])
        olympic = t["system"] == "olympic"
        if olympic and s1 == s2:
            raise ValidationError("В олимпийской системе ничья невозможна — укажите победителя.")
        if olympic:
            self._ensure_next_not_played(m)
        winner = None
        if s1 > s2:
            winner = m["team1_id"]
        elif s2 > s1:
            winner = m["team2_id"]
        with self.conn:
            self.conn.execute(
                "UPDATE matches SET score1=?, score2=?, winner_id=?, status='played' WHERE id=?",
                (s1, s2, winner, match_id))
            if olympic:
                self._put_in_next(m, winner)
        self._after_results_changed(m["tournament_id"])

    def clear_result(self, match_id):
        m = self.get_match(match_id)
        if m is None:
            raise ValidationError("Матч не найден.")
        if m["status"] != "played":
            raise ValidationError("У этого матча нет результата.")
        t = self.get_tournament(m["tournament_id"])
        olympic = t["system"] == "olympic"
        if olympic:
            self._ensure_next_not_played(m)
        with self.conn:
            self.conn.execute(
                "UPDATE matches SET score1=NULL, score2=NULL, winner_id=NULL, "
                "status='scheduled' WHERE id=?", (match_id,))
            if olympic:
                self._put_in_next(m, None)
        self._after_results_changed(m["tournament_id"])

    def _ensure_next_not_played(self, m):
        if m["next_match_id"]:
            nxt = self.conn.execute("SELECT status FROM matches WHERE id=?",
                                    (m["next_match_id"],)).fetchone()
            if nxt and nxt["status"] == "played":
                raise ValidationError("Следующий матч уже сыгран. Сначала очистите его результат.")

    def _put_in_next(self, m, team_id):
        if m["next_match_id"]:
            col = "team1_id" if m["next_slot"] == 1 else "team2_id"
            self.conn.execute(f"UPDATE matches SET {col}=? WHERE id=?",
                              (team_id, m["next_match_id"]))

    def _after_results_changed(self, tid):
        left = self.conn.execute(
            "SELECT COUNT(*) FROM matches WHERE tournament_id=? AND status='scheduled'",
            (tid,)).fetchone()[0]
        total = self.match_count(tid)
        with self.conn:
            status = "finished" if (total and left == 0) else "running"
            self.conn.execute("UPDATE tournaments SET status=? WHERE id=?", (status, tid))
        self.recalc_ratings()

    # --------------------------------------------------- рейтинг и статистика

    def recalc_ratings(self):
        """Полный пересчёт рейтинга Эло по всем сыгранным матчам в хронологическом порядке."""
        ratings = {r["id"]: START_RATING for r in
                   self.conn.execute("SELECT id FROM teams").fetchall()}
        rows = self.conn.execute(
            "SELECT m.* FROM matches m JOIN tournaments t ON t.id=m.tournament_id "
            "WHERE m.status='played' ORDER BY t.start_date, t.id, m.round, m.position").fetchall()
        for m in rows:
            a, b = m["team1_id"], m["team2_id"]
            if a not in ratings or b not in ratings:
                continue
            if m["score1"] > m["score2"]:
                sa = 1.0
            elif m["score1"] < m["score2"]:
                sa = 0.0
            else:
                sa = 0.5
            ea = 1 / (1 + 10 ** ((ratings[b] - ratings[a]) / 400))
            ratings[a] += ELO_K * (sa - ea)
            ratings[b] += ELO_K * ((1 - sa) - (1 - ea))
        with self.conn:
            for tid, value in ratings.items():
                self.conn.execute("UPDATE teams SET rating=? WHERE id=?", (round(value, 2), tid))

    @staticmethod
    def _blank_stat():
        return {"played": 0, "wins": 0, "draws": 0, "losses": 0,
                "gf": 0, "ga": 0, "diff": 0, "points": 0}

    @staticmethod
    def _apply(stat, gf, ga):
        stat["played"] += 1
        stat["gf"] += gf
        stat["ga"] += ga
        stat["diff"] = stat["gf"] - stat["ga"]
        if gf > ga:
            stat["wins"] += 1
            stat["points"] += 3
        elif gf == ga:
            stat["draws"] += 1
            stat["points"] += 1
        else:
            stat["losses"] += 1

    def team_stats(self, team_id, tid=None):
        stat = self._blank_stat()
        sql = "SELECT * FROM matches WHERE status='played' AND (team1_id=? OR team2_id=?)"
        args = [team_id, team_id]
        if tid is not None:
            sql += " AND tournament_id=?"
            args.append(tid)
        for m in self.conn.execute(sql, args).fetchall():
            if m["team1_id"] == team_id:
                self._apply(stat, m["score1"], m["score2"])
            else:
                self._apply(stat, m["score2"], m["score1"])
        return stat

    def standings(self, tid):
        t = self.get_tournament(tid)
        table = {}
        for team in self.approved_teams(tid):
            row = self._blank_stat()
            row.update(team_id=team["id"], name=team["name"], rating=team["rating"])
            table[team["id"]] = row
        for m in self.conn.execute(
                "SELECT * FROM matches WHERE tournament_id=? AND status='played'",
                (tid,)).fetchall():
            if m["team1_id"] in table:
                self._apply(table[m["team1_id"]], m["score1"], m["score2"])
            if m["team2_id"] in table:
                self._apply(table[m["team2_id"]], m["score2"], m["score1"])
        rows = list(table.values())
        if t is not None and t["system"] == "olympic":
            rows.sort(key=lambda r: (-r["wins"], -r["diff"], -r["gf"], r["name"]))
        else:
            rows.sort(key=lambda r: (-r["points"], -r["diff"], -r["gf"], r["name"]))
        for i, r in enumerate(rows, 1):
            r["place"] = i
        return rows

    def ratings_table(self):
        rows = []
        for team in self.conn.execute("SELECT * FROM teams ORDER BY rating DESC, name").fetchall():
            stat = self.team_stats(team["id"])
            rows.append({"team_id": team["id"], "name": team["name"], "city": team["city"],
                         "rating": team["rating"], **stat})
        for i, r in enumerate(rows, 1):
            r["place"] = i
        return rows

    def team_history(self, team_id):
        rows = self.conn.execute(
            "SELECT m.*, a.name AS team1_name, b.name AS team2_name, t.name AS tournament_name "
            "FROM matches m JOIN tournaments t ON t.id=m.tournament_id "
            "LEFT JOIN teams a ON a.id=m.team1_id LEFT JOIN teams b ON b.id=m.team2_id "
            "WHERE (m.team1_id=? OR m.team2_id=?) AND m.status<>'bye' "
            "ORDER BY t.start_date, t.id, m.round, m.position", (team_id, team_id)).fetchall()
        result = []
        for m in rows:
            home = m["team1_id"] == team_id
            opp = m["team2_name"] if home else m["team1_name"]
            if m["status"] == "played":
                gf, ga = (m["score1"], m["score2"]) if home else (m["score2"], m["score1"])
                outcome = "Победа" if gf > ga else ("Ничья" if gf == ga else "Поражение")
                score = f"{gf} : {ga}"
            else:
                outcome, score = "Впереди", "—"
            result.append({"tournament": m["tournament_name"], "round": m["round_name"],
                           "opponent": opp or "будет определён", "score": score,
                           "outcome": outcome, "date": fmt_date(m["match_date"]),
                           "time": m["match_time"] or ""})
        return result

    # --------------------------------------------------------------- экспорт

    def export_rows(self, kind, tid=None):
        """Возвращает (заголовок листа, список заголовков, список строк) для экспорта."""
        if kind == "standings":
            self._need_tournament(tid)
            headers = ["Место", "Команда", "Игры", "Победы", "Ничьи", "Поражения",
                       "Сеты выиграно", "Сеты проиграно", "Разница сетов", "Очки", "Рейтинг"]
            rows = [[r["place"], r["name"], r["played"], r["wins"], r["draws"], r["losses"],
                     r["gf"], r["ga"], r["diff"], r["points"], r["rating"]]
                    for r in self.standings(tid)]
            return "Таблица", headers, rows
        if kind == "schedule":
            self._need_tournament(tid)
            headers = ["Тур", "№", "Команда 1", "Команда 2", "Счёт", "Дата", "Время",
                       "Место", "Статус"]
            rows = [[m["round_name"], m["position"], m["team1_name"] or "—",
                     m["team2_name"] or "—", self.score_text(m), fmt_date(m["match_date"]),
                     m["match_time"] or "", m["venue"], MATCH_STATUS[m["status"]]]
                    for m in self.list_matches(tid)]
            return "Расписание", headers, rows
        if kind == "ratings":
            headers = ["Место", "Команда", "Город", "Рейтинг", "Игры", "Победы", "Ничьи",
                       "Поражения"]
            rows = [[r["place"], r["name"], r["city"], r["rating"], r["played"], r["wins"],
                     r["draws"], r["losses"]] for r in self.ratings_table()]
            return "Рейтинг", headers, rows
        if kind == "roster":
            headers = ["Команда", "№", "ФИО", "Амплуа", "Год рождения"]
            teams = self.approved_teams(tid) if tid else self.list_teams()
            rows = []
            for team in teams:
                for p in self.list_players(team["id"]):
                    rows.append([team["name"], p["number"], p["full_name"], p["position"],
                                 p["birth_year"]])
            return "Составы", headers, rows
        if kind == "applications":
            self._need_tournament(tid)
            headers = ["Команда", "Город", "Капитан", "Игроков", "Статус", "Подана"]
            rows = [[a["team_name"], a["city"], a["captain"], a["players_count"],
                     APP_STATUS[a["status"]], a["created_at"]]
                    for a in self.list_applications(tid)]
            return "Заявки", headers, rows
        raise ValidationError("Неизвестный вид отчёта.")

    def _need_tournament(self, tid):
        if tid is None or self.get_tournament(tid) is None:
            raise ValidationError("Выберите турнир.")


def write_csv(path, headers, rows):
    """CSV с разделителем «;» и BOM — корректно открывается в Excel."""
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(headers)
        writer.writerows(rows)


def write_xlsx(path, title, headers, rows):
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font, PatternFill
        from openpyxl.utils import get_column_letter
    except ImportError:
        raise ValidationError("Для экспорта в XLSX установите библиотеку openpyxl "
                              "(pip install openpyxl) или выберите формат CSV.")
    wb = Workbook()
    ws = wb.active
    ws.title = title[:31]
    ws.append(headers)
    for row in rows:
        ws.append(list(row))
    fill = PatternFill("solid", fgColor="1F4E79")
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
    for i, header in enumerate(headers, 1):
        width = max([len(str(header))] + [len(str(r[i - 1])) for r in rows]) + 3
        ws.column_dimensions[get_column_letter(i)].width = min(width, 45)
    ws.freeze_panes = "A2"
    wb.save(path)


def export_to_file(path, title, headers, rows):
    if path.lower().endswith(".xlsx"):
        write_xlsx(path, title, headers, rows)
    else:
        write_csv(path, headers, rows)


# ------------------------------------------------------------- демо-данные

DEMO_TEAMS = [
    ("Вымпел", "Магадан"), ("Северные волки", "Магадан"), ("Колыма", "Сусуман"),
    ("Авангард", "Ола"), ("Буревестник", "Палатка"), ("Динамо-Север", "Ягодное"),
    ("Золотой сет", "Омсукчан"), ("Полярная звезда", "Эвенск"),
]
DEMO_SURNAMES = ["Иванов", "Петров", "Сидоров", "Кузнецов", "Смирнов", "Попов", "Васильев",
                 "Соколов", "Михайлов", "Новиков", "Фёдоров", "Морозов", "Волков", "Алексеев"]
DEMO_NAMES = ["Алексей", "Дмитрий", "Максим", "Иван", "Сергей", "Андрей", "Никита", "Егор"]
DEMO_POSITIONS = ["Связующий", "Либеро", "Доигровщик", "Доигровщик",
                  "Центральный блокирующий", "Центральный блокирующий", "Диагональный"]


def load_demo(db):
    """Заполняет базу демонстрационными данными. Возвращает False, если команды уже есть."""
    if db.conn.execute("SELECT COUNT(*) FROM teams").fetchone()[0]:
        return False
    today = datetime.date.today()
    team_ids = []
    with db.conn:
        for ti, (name, city) in enumerate(DEMO_TEAMS):
            cur = db.conn.execute("INSERT INTO teams(name, city, captain) VALUES(?,?,?)",
                                  (name, city, f"{DEMO_SURNAMES[ti]} {DEMO_NAMES[ti]}"))
            team_ids.append(cur.lastrowid)
            for pi in range(7):
                db.conn.execute(
                    "INSERT INTO players(team_id, full_name, number, position, birth_year) "
                    "VALUES(?,?,?,?,?)",
                    (cur.lastrowid,
                     f"{DEMO_SURNAMES[(ti + pi) % len(DEMO_SURNAMES)]} "
                     f"{DEMO_NAMES[(ti * 3 + pi) % len(DEMO_NAMES)]}",
                     pi + 1, DEMO_POSITIONS[pi], 2002 + (ti + pi) % 5))
        db.conn.execute(
            "INSERT INTO users(login, pass_hash, role, full_name, team_id) VALUES(?,?,?,?,?)",
            ("coach", hash_password("coach"), ROLE_COACH, "Тренер Вымпела", team_ids[0]))
    t1 = db.create_tournament(
        "Кубок колледжа", "Волейбол", "olympic",
        (today + datetime.timedelta(days=3)).isoformat(),
        (today + datetime.timedelta(days=10)).isoformat(), "Спорткомплекс «Север»")
    t2 = db.create_tournament(
        "Чемпионат города", "Волейбол", "round_robin",
        (today + datetime.timedelta(days=14)).isoformat(),
        (today + datetime.timedelta(days=30)).isoformat(), "Дворец спорта")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with db.conn:
        for tid in team_ids[1:]:          # 7 команд — в сетке будет автопроход
            db.conn.execute(
                "INSERT INTO applications(tournament_id, team_id, status, created_at) "
                "VALUES(?,?,?,?)", (t1, tid, "approved", now))
        for tid in team_ids[2:7]:         # 5 команд — круговая система
            db.conn.execute(
                "INSERT INTO applications(tournament_id, team_id, status, created_at) "
                "VALUES(?,?,?,?)", (t2, tid, "approved", now))
        db.conn.execute(
            "INSERT INTO applications(tournament_id, team_id, status, created_at) "
            "VALUES(?,?,?,?)", (t2, team_ids[7], "pending", now))
    return True
