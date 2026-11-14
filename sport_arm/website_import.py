"""Импорт составов, капитанов и таблиц ЛВЛ Магадана.

Снимок официальных страниц сезона 2026-2027, проверен 14.11.2026.
Предыдущий сезон оставлен только в общей таблице результатов; игроки
и аккаунты загружаются исключительно для ЛВЛ 2026-2027.

Статистика в порядке: приём, блок, эйс, защита, ошибки.
Позиции игроков не публиковались в таблице команд, поэтому здесь не угадываются.
Аккаунты создаются только внутри локального приложения, не на сайте Федерации.
"""

from database import ROLE_COACH, hash_password

SOURCE_DATE = "2026-11-14"
LEAGUE_NAME = "Любительская Волейбольная Лига"
CURRENT_SEASON = "2026-2027"
PREVIOUS_SEASON = "2025-2026"
DEFAULT_PASSWORD = "123123"

SOURCES = {
    "Рваный Кед": "https://volleyball-mgdn.ru/team/rvanyy-ked/",
    "ОрлАнс": "https://volleyball-mgdn.ru/team/orlans/",
    "МагаданЭнерго": "https://volleyball-mgdn.ru/team/magadanenergo/",
    "СШ №5": "https://volleyball-mgdn.ru/team/ssh-%25e2%2584%25965/",
    "Анаконда": "https://volleyball-mgdn.ru/team/anakonda/",
    "СВГУ": "https://volleyball-mgdn.ru/team/svgu/",
    "Корунд": "https://volleyball-mgdn.ru/team/korund/",
    "Импульс": "https://volleyball-mgdn.ru/team/impuls/",
    "Юность": "https://volleyball-mgdn.ru/team/yunost/",
    "УниKids": "https://volleyball-mgdn.ru/team/yunikids/",
    "Вихрь": "https://volleyball-mgdn.ru/team/vihr/",
}

# Официально указанное на странице команды ответственное лицо/капитан.
# Значения: ФИО, логин.
# Игрок, который выделяется по опубликованной статистике сезона 2026-2027.
# Это аналитическая отметка, не замена официальному капитану команды.
STANDOUTS = {
    "Рваный Кед": ("Новосад Кирилл", "приём 49, защита 63, всего 1 ошибка"),
    "ОрлАнс": ("Лысенко Евгений", "23 блока"),
    "МагаданЭнерго": ("Коксин Максим", "30 блоков и 16 эйсов"),
    "СШ №5": ("Вутын Алексей", "приём 61, защита 75"),
    "Анаконда": ("Доброконный Роман", "16 блоков, 8 эйсов, защита 57"),
    "СВГУ": ("Буга Никита", "приём 113, защита 127"),
    "Корунд": ("Высоцкий Иван", "приём 30, защита 52"),
    "Импульс": ("Пидвирный Александр", "приём 29, 9 блоков, 6 эйсов"),
    "Юность": ("Столинец Валерия", "приём 53, защита 42"),
    "УниKids": ("Хекилаева Элина", "приём 57, защита 71"),
    "Вихрь": ("Вебер Данила", "приём 50, защита 57"),
}

CAPTAINS = {
    "Рваный Кед": ("Петров Евгений", "petrov"),
    "ОрлАнс": ("Лысенко Сергей", "lysenko"),
    "МагаданЭнерго": ("Шулянов Евгений", "shulyanov"),
    "СШ №5": ("Карпенко Сергей", "karpenko"),
    "Анаконда": ("Доброконный Илья", "dobrokonny"),
    "СВГУ": ("Буга Никита", "buga"),
    "Корунд": ("Ляшук Алексей", "lyashuk"),
    "Импульс": ("Пидвирный Александр", "pidvirny"),
    "Юность": ("Ерохин Александр", "erokhin"),
    "УниKids": ("Зайцева Нина", "zaytseva"),
    "Вихрь": ("Харин Иван", "kharin"),
}

# place, team, points, matches, wins, losses, points_for, points_against,
# points_ratio, sets_won, sets_lost, sets_ratio
STANDINGS = {
    CURRENT_SEASON: [
        (1, "Рваный Кед", 21, 7, 7, 0, 631, 499, 1.265, 21, 5, 4.200),
        (2, "ОрлАнс", 18, 6, 6, 0, 501, 393, 1.275, 18, 2, 9.000),
        (3, "МагаданЭнерго", 18, 8, 6, 2, 620, 541, 1.146, 19, 8, 2.375),
        (4, "СШ №5", 16, 7, 6, 1, 582, 456, 1.276, 19, 7, 2.714),
        (5, "Анаконда", 13, 7, 4, 3, 616, 577, 1.068, 16, 11, 1.455),
        (6, "СВГУ", 12, 8, 4, 4, 572, 608, 0.941, 14, 14, 1.000),
        (7, "Корунд", 8, 8, 3, 5, 571, 621, 0.919, 10, 17, 0.588),
        (8, "Импульс", 4, 6, 2, 4, 461, 529, 0.871, 8, 15, 0.533),
        (9, "Юность", 4, 7, 1, 6, 590, 668, 0.883, 10, 19, 0.526),
        (10, "УниKids", 1, 7, 0, 7, 424, 546, 0.777, 2, 21, 0.095),
        (11, "Вихрь", 0, 7, 0, 7, 465, 595, 0.782, 3, 21, 0.143),
    ],
    PREVIOUS_SEASON: [
        (1, "Рваный Кед", 56, 20, 19, 1, 1665, 1273, 1.308, 57, 11, 5.182),
        (2, "ОрлАнс", 50, 20, 17, 3, 1716, 1386, 1.238, 54, 17, 3.176),
        (3, "МагаданЭнерго", 44, 20, 15, 5, 1651, 1468, 1.125, 48, 24, 2.000),
        (4, "Анаконда", 44, 20, 14, 6, 1631, 1494, 1.092, 51, 27, 1.889),
        (5, "СВГУ", 39, 20, 14, 6, 1659, 1508, 1.100, 46, 27, 1.704),
        (6, "Бей-Беги", 24, 20, 7, 13, 1556, 1574, 0.989, 34, 44, 0.773),
        (7, "Больные Колени", 23, 20, 7, 13, 1633, 1771, 0.922, 35, 46, 0.761),
        (8, "Корунд", 17, 20, 7, 13, 1643, 1775, 0.926, 27, 51, 0.529),
        (9, "Юность", 14, 20, 5, 15, 1492, 1756, 0.850, 24, 52, 0.462),
        (10, "Импульс", 12, 20, 4, 16, 1465, 1726, 0.849, 21, 54, 0.389),
        (11, "Искра", 6, 20, 1, 19, 1235, 1615, 0.765, 13, 57, 0.228),
    ],
}

# jersey number, name, reception, blocks, aces, defense, errors
ROSTERS = {
    "Рваный Кед": [
        (1, "Африна Анна", 0, 0, 0, 0, 0),
        (2, "Рогач Татьяна", 9, 0, 10, 24, 13),
        (4, "Озеров Данил", 18, 2, 3, 41, 19),
        (10, "Ковальчук Борис", 2, 8, 2, 17, 12),
        (11, "Новосад Кирилл", 49, 0, 0, 63, 1),
        (13, "Петров Евгений", 36, 9, 12, 39, 36),
        (16, "Вершада Денис", 2, 19, 6, 12, 32),
        (24, "Коксин Дмитрий", 42, 12, 13, 53, 28),
        (27, "Лысенко София", 2, 0, 2, 3, 8),
        (42, "Кононов Леонид", 4, 5, 1, 17, 16),
        (56, "Коксин Олег", 1, 1, 2, 2, 1),
    ],
    "ОрлАнс": [
        (1, "Строило Наталья", 0, 0, 0, 0, 0),
        (2, "Власова Виктория", 0, 0, 0, 0, 0),
        (3, "Коксина Светлана", 1, 0, 7, 18, 12),
        (5, "Василенко Константин", 0, 0, 0, 0, 0),
        (7, "Вереница Александр", 8, 8, 2, 11, 17),
        (8, "Лысенко Евгений", 30, 23, 9, 37, 38),
        (9, "Ухтин Антон", 2, 5, 7, 16, 6),
        (10, "Шешуков Максим", 23, 6, 11, 35, 20),
        (13, "Лысенко Сергей", 41, 3, 12, 40, 27),
        (14, "Ежов Дмитрий", 4, 12, 2, 17, 22),
        (15, "Марченко Леонид", 16, 0, 1, 20, 4),
    ],
    "МагаданЭнерго": [
        (1, "Азади Алина", 16, 0, 4, 17, 16),
        (2, "Матскевич Александр", 0, 1, 2, 5, 11),
        (3, "Кащенко Алексей", 15, 6, 3, 7, 4),
        (5, "Шулянов Евгений", 32, 14, 12, 31, 36),
        (7, "Плеша Артем", 6, 6, 5, 2, 26),
        (8, "Сальников Максим", 48, 1, 4, 60, 9),
        (9, "Володченко Сергей", 5, 4, 1, 13, 16),
        (10, "Коксин Максим", 9, 30, 16, 31, 36),
        (12, "Лебедев Иван", 47, 1, 14, 42, 45),
        (13, "Сергеев Владислав", 0, 0, 0, 0, 0),
        (15, "Попович Алексей", 0, 0, 0, 0, 0),
    ],
    "СШ №5": [
        (1, "Щетина Павел", 2, 0, 1, 9, 7),
        (2, "Антонюк Егор", 2, 3, 0, 12, 10),
        (3, "Набегаев Алексей", 5, 0, 1, 0, 6),
        (4, "Ферапонтов Марк", 0, 0, 0, 0, 2),
        (5, "Ткаченко Дарья", 2, 0, 1, 8, 10),
        (6, "Чижов Степан", 11, 0, 5, 32, 21),
        (7, "Онищенко Александра", 2, 0, 2, 25, 4),
        (9, "Шкатулов Сергей", 0, 1, 0, 0, 2),
        (10, "Шарапов Виктор", 9, 27, 7, 40, 26),
        (11, "Гарькавенко Марк", 23, 10, 11, 52, 43),
        (12, "Деркач Иван", 0, 0, 0, 0, 3),
        (13, "Вутын Алексей", 61, 0, 0, 75, 23),
        (14, "Цвященко Максим", 0, 0, 0, 0, 0),
        (15, "Фролов Кирилл", 0, 0, 0, 0, 0),
        (18, "Кудряшов Дмитрий", 5, 9, 6, 14, 29),
        (20, "Карпенко Сергей", 0, 4, 4, 25, 14),
    ],
    "Анаконда": [
        (2, "Клевогин Павел", 28, 2, 5, 61, 22),
        (3, "Доброконный Роман", 25, 16, 8, 57, 25),
        (4, "Ивлев Владислав", 23, 3, 2, 48, 16),
        (5, "Доброконный Илья", 13, 17, 5, 45, 23),
        (6, "Наумов Михаил", 13, 1, 1, 31, 16),
        (8, "Громова Валентина", 4, 0, 0, 9, 1),
        (9, "Доброконный Вячеслав", 0, 0, 0, 0, 0),
        (10, "Прахт Дмитрий", 0, 0, 0, 0, 0),
        (12, "Горяинов Олег", 1, 1, 2, 14, 11),
        (13, "Макарова Елизавета", 0, 0, 0, 0, 0),
        (14, "Масков Иван", 24, 4, 6, 20, 26),
        (16, "Засыпкина Татьяна", 10, 0, 5, 23, 7),
    ],
    "СВГУ": [
        (1, "Якушков Иван", 9, 4, 13, 44, 37),
        (2, "Горшков Данил", 15, 3, 14, 34, 56),
        (3, "Куняева Екатерина", 0, 0, 0, 0, 0),
        (4, "Николаев Александр", 6, 4, 1, 16, 22),
        (5, "Буга Никита", 113, 0, 0, 127, 18),
        (9, "Суркова Елизавета", 30, 0, 11, 47, 20),
        (10, "Белицкий Петр", 21, 6, 4, 33, 23),
        (11, "Рассохин Геннадий", 3, 23, 11, 21, 36),
        (12, "Целенко Леонид", 4, 11, 11, 29, 56),
    ],
    "Корунд": [
        (2, "Ильин Вячеслав", 18, 0, 0, 36, 5),
        (3, "Зыварь Антон", 5, 9, 3, 20, 18),
        (4, "Шабуневич Илья", 16, 4, 1, 20, 33),
        (5, "Бадышев Станислав", 21, 4, 6, 36, 31),
        (7, "Коротков Сергей", 13, 4, 4, 26, 16),
        (8, "Зырянова Татьяна", 0, 0, 0, 0, 0),
        (9, "Вилисов Сергей", 0, 0, 0, 0, 0),
        (10, "Ляшук Алексей", 3, 0, 2, 0, 5),
        (12, "Лохов Николай", 3, 0, 5, 22, 8),
        (13, "Старцева Татьяна", 3, 0, 3, 5, 5),
        (14, "Ващенко Владимир", 2, 1, 3, 17, 14),
        (16, "Дашиев Жаргал", 0, 5, 0, 5, 4),
        (17, "Высоцкий Иван", 30, 4, 3, 52, 31),
        (18, "Васильева Евгения", 14, 2, 7, 45, 19),
        (19, "Стешанов Василий", 7, 8, 4, 9, 13),
    ],
    "Импульс": [
        (2, "Баталова Наталья", 3, 0, 0, 3, 3),
        (5, "Журавлев Илья", 1, 0, 1, 0, 1),
        (6, "Алехно Андрей", 8, 1, 6, 9, 7),
        (7, "Пидвирный Александр", 29, 9, 6, 23, 41),
        (9, "Козлов Антон", 7, 4, 1, 5, 7),
        (10, "Буйко Анна", 0, 0, 9, 21, 3),
        (11, "Дашевский Иван", 14, 3, 2, 30, 13),
        (12, "Дьяконов Виктор", 0, 0, 1, 1, 1),
        (13, "Савирский Алексей", 0, 0, 0, 0, 0),
        (14, "Яук Алексей", 4, 9, 5, 23, 22),
        (17, "Коляда Герман", 3, 1, 4, 15, 5),
        (22, "Покалюк Евгений", 18, 0, 0, 42, 3),
        (23, "Жомарт Уулу Шерзатбек", 10, 3, 4, 14, 38),
        (25, "Долгерт Вадим", 0, 0, 0, 0, 0),
        (28, "Поповцев Вячеслав", 0, 0, 0, 0, 0),
    ],
    "Юность": [
        (1, "Столинец Валерия", 53, 0, 2, 42, 22),
        (4, "Оськин Владислав", 37, 6, 8, 39, 39),
        (5, "Ерохин Александр", 22, 4, 4, 28, 72),
        (6, "Ежов Роман", 4, 14, 4, 10, 29),
        (7, "Мартынов Макар", 12, 7, 4, 25, 31),
        (9, "Недашковский Иван", 6, 12, 3, 10, 34),
        (10, "Мамышев Артем", 45, 2, 2, 39, 30),
        (33, "Ашакова Ксения", 4, 0, 5, 20, 14),
    ],
    "УниKids": [
        (1, "Лукин Александр", 8, 1, 5, 10, 28),
        (3, "Коксина Любовь", 16, 0, 1, 34, 5),
        (4, "Чередниченко Юрий", 1, 20, 7, 6, 24),
        (5, "Сухан Максим", 6, 0, 0, 6, 12),
        (6, "Хекилаева Элина", 57, 0, 0, 71, 10),
        (8, "Кульчицкий Артем", 0, 5, 1, 3, 10),
        (9, "Галактионов Максим", 10, 1, 1, 23, 37),
        (10, "Насинов Сунатулло", 10, 0, 0, 15, 3),
        (11, "Оглы Алексей", 6, 12, 0, 18, 15),
        (55, "Зайцева Нина", 15, 1, 3, 43, 15),
    ],
    "Вихрь": [
        (3, "Ежов Андрей", 0, 1, 6, 16, 10),
        (4, "Харин Иван", 5, 0, 1, 13, 11),
        (5, "Горшков Александр", 13, 9, 12, 28, 42),
        (6, "Чабан Софья", 0, 0, 2, 12, 6),
        (7, "Воропаева Ангелина", 10, 0, 1, 20, 11),
        (8, "Влесков Василий", 6, 1, 3, 16, 13),
        (9, "Вебер Данила", 50, 0, 0, 57, 9),
        (10, "Козловский Ян", 5, 0, 3, 8, 14),
        (12, "Крупица Вадим", 10, 1, 7, 11, 28),
        (13, "Рейдер Денис", 7, 1, 0, 17, 8),
        (16, "Моисеенков Дмитрий", 1, 0, 0, 6, 7),
        (22, "Леванюк Максим", 16, 6, 4, 23, 24),
        (22, "Молканов Сергей", 3, 0, 0, 6, 0),
        (24, "Биндей Владимир", 0, 0, 0, 0, 0),
        (55, "Кочура Алексей", 3, 2, 2, 5, 8),
    ],
}

def _unique_login(db, preferred, team_slug):
    candidate = preferred
    suffix = 2
    while db.conn.execute(
        "SELECT 1 FROM users WHERE login=?", (candidate,)
    ).fetchone():
        candidate = f"{preferred}_{team_slug}" if suffix == 2 else f"{preferred}_{team_slug}{suffix}"
        suffix += 1
    return candidate


def _provision_captain_accounts(db, team_ids):
    accounts = []
    with db.conn:
        for team_name, (captain, preferred_login) in CAPTAINS.items():
            team_id = team_ids[team_name]
            linked = db.conn.execute(
                """
                SELECT a.login, a.full_name, a.user_id
                FROM official_team_accounts a
                WHERE a.team_id=? AND a.season=?
                """,
                (team_id, CURRENT_SEASON),
            ).fetchone()
            if linked:
                accounts.append({
                    "team": team_name, "full_name": linked["full_name"],
                    "login": linked["login"], "password": None,
                    "created": False,
                })
                continue

            login = _unique_login(db, preferred_login, {
                "Рваный Кед": "rvanyyked", "ОрлАнс": "orlans",
                "МагаданЭнерго": "magadanenergo", "СШ №5": "ssh5",
                "Анаконда": "anakonda", "СВГУ": "svgu", "Корунд": "korund",
                "Импульс": "impuls", "Юность": "yunost",
                "УниKids": "unikids", "Вихрь": "vihr",
            }[team_name])
            cur = db.conn.execute(
                """
                INSERT INTO users(login, pass_hash, role, full_name, team_id)
                VALUES(?,?,?,?,?)
                """,
                (login, hash_password(DEFAULT_PASSWORD), ROLE_COACH, captain, team_id),
            )
            user_id = cur.lastrowid
            db.conn.execute(
                """
                INSERT INTO official_team_accounts(
                    team_id, season, user_id, login, full_name
                ) VALUES(?,?,?,?,?)
                """,
                (team_id, CURRENT_SEASON, user_id, login, captain),
            )
            accounts.append({
                "team": team_name, "full_name": captain, "login": login,
                "password": DEFAULT_PASSWORD, "created": True,
            })
    return accounts


def import_magadan_teams(db):
    """Импортирует 14 команд, текущие составы ЛВЛ 26-27 и 11 капитанских аккаунтов.

    Исторические записи из сезона 2025-2026 сохраняются без старых составов и аккаунтов.
    """
    team_ids = {}
    added_teams = 0
    imported_standings = 0
    imported_roster = 0
    with db.conn:
        for season, rows in STANDINGS.items():
            for row in rows:
                (place, name, points, matches, wins, losses, points_for,
                 points_against, points_ratio, sets_won, sets_lost, sets_ratio) = row
                team = db.conn.execute(
                    "SELECT id, city FROM teams WHERE name=?", (name,)
                ).fetchone()
                if team is None:
                    cur = db.conn.execute(
                        "INSERT INTO teams(name, city, captain) VALUES(?,?,?)",
                        (name, "Магадан", CAPTAINS.get(name, ("", ""))[0]),
                    )
                    team_id = cur.lastrowid
                    added_teams += 1
                else:
                    team_id = team["id"]
                    db.conn.execute(
                        "UPDATE teams SET city=CASE WHEN trim(city)='' THEN 'Магадан' "
                        "ELSE city END, captain=CASE WHEN ?<>'' THEN ? ELSE captain END "
                        "WHERE id=?",
                        (CAPTAINS.get(name, ("", ""))[0],
                         CAPTAINS.get(name, ("", ""))[0], team_id),
                    )
                team_ids[name] = team_id
                db.conn.execute(
                    """
                    INSERT INTO team_season_standings(
                        team_id, league, season, place, points, matches_played,
                        wins, losses, points_scored, points_conceded, points_ratio,
                        sets_won, sets_lost, sets_ratio, source_url, imported_at
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(team_id, season) DO UPDATE SET
                        league=excluded.league, place=excluded.place,
                        points=excluded.points, matches_played=excluded.matches_played,
                        wins=excluded.wins, losses=excluded.losses,
                        points_scored=excluded.points_scored,
                        points_conceded=excluded.points_conceded,
                        points_ratio=excluded.points_ratio,
                        sets_won=excluded.sets_won, sets_lost=excluded.sets_lost,
                        sets_ratio=excluded.sets_ratio, source_url=excluded.source_url,
                        imported_at=excluded.imported_at
                    """,
                    (
                        team_id, LEAGUE_NAME, season, place, points, matches,
                        wins, losses, points_for, points_against, points_ratio,
                        sets_won, sets_lost, sets_ratio,
                        SOURCES.get(name, ""), SOURCE_DATE,
                    ),
                )
                imported_standings += 1

        # Текущий состав ровно по сезону 2026-2027: старые сезоны в roster не смешиваем.
        for team_name, roster in ROSTERS.items():
            team_id = team_ids[team_name]
            db.conn.execute(
                "DELETE FROM official_team_roster WHERE team_id=? AND season=?",
                (team_id, CURRENT_SEASON),
            )
            for number, full_name, reception, blocks, aces, defense, errors in roster:
                db.conn.execute(
                    """
                    INSERT INTO official_team_roster(
                        team_id, season, jersey_number, full_name, reception,
                        blocks, aces, defense, errors, source_url, imported_at
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        team_id, CURRENT_SEASON, number, full_name, reception,
                        blocks, aces, defense, errors, SOURCES[team_name], SOURCE_DATE,
                    ),
                )
                imported_roster += 1

    accounts = _provision_captain_accounts(db, team_ids)
    return {
        "added_teams": added_teams,
        "imported_standings": imported_standings,
        "imported_roster": imported_roster,
        "total_teams": db.conn.execute("SELECT COUNT(*) FROM teams").fetchone()[0],
        "current_roster_teams": len(ROSTERS),
        "captain_accounts": accounts,
        "source_date": SOURCE_DATE,
    }
