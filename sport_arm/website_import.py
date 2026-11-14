"""Импорт официальных команд и таблиц Федерации волейбола г. Магадан.

Источники:
- https://volleyball-mgdn.ru/ (ЛВЛ 2026-2027)
- https://volleyball-mgdn.ru/tournament/лвл-2025-2026/
Снимок зафиксирован 14.11.2026. Это не live API.
Составы игроков не выдумываются: общая страница игроков не даёт
надёжной привязки всех записей к командам.
"""
SOURCE_DATE = "2026-11-14"
LEAGUE_NAME = "Любительская Волейбольная Лига"
CURRENT_SEASON = "2026-2027"
PREVIOUS_SEASON = "2025-2026"
SOURCES = {
    CURRENT_SEASON: "https://volleyball-mgdn.ru/",
    PREVIOUS_SEASON: "https://volleyball-mgdn.ru/tournament/лвл-2025-2026/",
}
# place, team, points, matches, wins, losses, points_for, points_against,
# points_ratio, sets_won, sets_lost, sets_ratio
STANDINGS = {
    CURRENT_SEASON: [
        (1, "Рваный Кед", 12, 4, 4, 0, 347, 260, 1.335, 12, 2, 6.000),
        (2, "ОрлАнс", 12, 4, 4, 0, 351, 288, 1.219, 12, 2, 6.000),
        (3, "МагаданЭнерго", 9, 4, 3, 1, 305, 270, 1.130, 9, 4, 2.250),
        (4, "СШ №5", 7, 4, 3, 1, 357, 307, 1.163, 10, 7, 1.429),
        (5, "Анаконда", 7, 4, 2, 2, 338, 317, 1.066, 9, 6, 1.500),
        (6, "СВГУ", 6, 4, 2, 2, 244, 293, 0.833, 6, 7, 0.857),
        (7, "Юность", 4, 3, 1, 2, 274, 289, 0.948, 6, 7, 0.857),
        (8, "Импульс", 2, 3, 1, 2, 239, 277, 0.863, 4, 8, 0.500),
        (9, "УниKids", 1, 3, 0, 3, 206, 246, 0.837, 2, 9, 0.222),
        (10, "Вихрь", 0, 3, 0, 3, 216, 270, 0.800, 2, 9, 0.222),
        (11, "Корунд", 0, 4, 0, 4, 262, 322, 0.814, 1, 12, 0.083),
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

def import_magadan_teams(db):
    """Идемпотентно добавляет 14 команд и две сезонные таблицы.

    Ручные названия, города и капитаны существующих команд не перезаписываются.
    Показатели сезонов обновляются из снимка официального сайта.
    """
    added_teams = 0
    imported_rows = 0
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
                        (name, "Магадан", ""),
                    )
                    team_id = cur.lastrowid
                    added_teams += 1
                else:
                    team_id = team["id"]
                    if not (team["city"] or "").strip():
                        db.conn.execute(
                            "UPDATE teams SET city=? WHERE id=?",
                            ("Магадан", team_id),
                        )
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
                    (team_id, LEAGUE_NAME, season, place, points, matches,
                     wins, losses, points_for, points_against, points_ratio,
                     sets_won, sets_lost, sets_ratio, SOURCES[season], SOURCE_DATE),
                )
                imported_rows += 1
    return {
        "added_teams": added_teams,
        "imported_rows": imported_rows,
        "total_teams": db.conn.execute("SELECT COUNT(*) FROM teams").fetchone()[0],
        "current_season_teams": len(STANDINGS[CURRENT_SEASON]),
        "previous_season_teams": len(STANDINGS[PREVIOUS_SEASON]),
        "source_date": SOURCE_DATE,
    }
