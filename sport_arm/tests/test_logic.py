import csv
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import (Database, ValidationError, fmt_date, load_demo,  # noqa: E402
                      parse_date, seed_order, export_to_file)


def make_db():
    return Database(":memory:")


def add_team(db, name, players=6):
    db.conn.execute("INSERT INTO teams(name, city, captain) VALUES(?,?,?)", (name, "Город", "Кап"))
    tid = db.conn.execute("SELECT id FROM teams WHERE name=?", (name,)).fetchone()[0]
    for i in range(players):
        db.add_player(tid, f"Игрок {i}", i + 1, "Нап", 2003)
    return tid


def tournament_with_teams(db, n, system="olympic"):
    tid = db.create_tournament("Т", "Футбол", system, "01.06.2026", "30.06.2026", "Зал")
    ids = [add_team(db, f"Команда {i}") for i in range(n)]
    for team in ids:
        app = db.submit_application(tid, team)
        db.set_application_status(app, "approved")
    return tid, ids


class AuthTests(unittest.TestCase):
    def test_default_admin(self):
        db = make_db()
        self.assertIsNotNone(db.login("admin", "admin"))
        self.assertIsNone(db.login("admin", "wrong"))
        self.assertIsNone(db.login("nobody", "x"))

    def test_register_coach(self):
        db = make_db()
        uid = db.register_coach("ivan", "pass1", "Иванов И.", "Орлы", "Магадан")
        user = db.login("IVAN", "pass1")          # логин без учёта регистра
        self.assertEqual(user["id"], uid)
        self.assertEqual(user["role"], "coach")
        self.assertEqual(db.get_team(user["team_id"])["name"], "Орлы")
        with self.assertRaises(ValidationError):
            db.register_coach("ivan", "pass1", "Другой", "Другая", "")
        with self.assertRaises(ValidationError):
            db.register_coach("new", "pass1", "Другой", "орлы", "")
        with self.assertRaises(ValidationError):
            db.register_coach("ab", "pass1", "Х", "Y", "")
        with self.assertRaises(ValidationError):
            db.register_coach("abc", "123", "Х", "Y", "")


class TeamTests(unittest.TestCase):
    def test_players_validation(self):
        db = make_db()
        t = add_team(db, "А", 0)
        db.add_player(t, "Петров П.", 10, "Вратарь", 2003)
        with self.assertRaises(ValidationError):
            db.add_player(t, "Дубль", 10, "", 2003)       # номер занят
        with self.assertRaises(ValidationError):
            db.add_player(t, "", 11, "", 2003)
        with self.assertRaises(ValidationError):
            db.add_player(t, "Х", 100, "", 2003)
        with self.assertRaises(ValidationError):
            db.add_player(t, "Х", "abc", "", 2003)
        with self.assertRaises(ValidationError):
            db.add_player(t, "Х", 5, "", 1900)
        pid = db.list_players(t)[0]["id"]
        db.update_player(pid, "Петров П.П.", 10, "Защитник", 2002)   # свой номер — можно
        self.assertEqual(db.list_players(t)[0]["position"], "Защитник")
        db.delete_player(pid)
        self.assertEqual(len(db.list_players(t)), 0)

    def test_roster_limit(self):
        db = make_db()
        t = add_team(db, "А", 0)
        for i in range(30):
            db.add_player(t, f"И{i}", i, "", 2003)
        with self.assertRaises(ValidationError):
            db.add_player(t, "Лишний", 50, "", 2003)

    def test_update_team_duplicate(self):
        db = make_db()
        a, b = add_team(db, "А"), add_team(db, "Б")
        with self.assertRaises(ValidationError):
            db.update_team(b, "а", "", "")
        db.update_team(b, "Б2", "Магадан", "Капитан")
        self.assertEqual(db.get_team(b)["name"], "Б2")


class ApplicationTests(unittest.TestCase):
    def test_flow(self):
        db = make_db()
        tid = db.create_tournament("Т", "Футбол", "olympic", "01.06.2026", "10.06.2026")
        small = add_team(db, "Малая", 2)
        big = add_team(db, "Большая", 6)
        with self.assertRaises(ValidationError):
            db.submit_application(tid, small)            # мало игроков
        app = db.submit_application(tid, big)
        with self.assertRaises(ValidationError):
            db.submit_application(tid, big)              # дубль
        db.set_application_status(app, "approved")
        self.assertEqual(len(db.approved_teams(tid)), 1)
        db.set_application_status(app, "rejected")
        self.assertEqual(len(db.approved_teams(tid)), 0)
        db.withdraw_application(app)
        self.assertEqual(len(db.list_applications(tid)), 0)

    def test_closed_after_start(self):
        db = make_db()
        tid, ids = tournament_with_teams(db, 3)
        db.generate_bracket(tid)
        extra = add_team(db, "Опоздавшая")
        with self.assertRaises(ValidationError):
            db.submit_application(tid, extra)
        app = db.list_applications(tid)[0]["id"]
        with self.assertRaises(ValidationError):
            db.withdraw_application(app)
        with self.assertRaises(ValidationError):
            db.set_application_status(app, "rejected")


class TournamentTests(unittest.TestCase):
    def test_validation(self):
        db = make_db()
        with self.assertRaises(ValidationError):
            db.create_tournament("", "Ф", "olympic", "01.06.2026", "02.06.2026")
        with self.assertRaises(ValidationError):
            db.create_tournament("Т", "Ф", "olympic", "05.06.2026", "02.06.2026")
        with self.assertRaises(ValidationError):
            db.create_tournament("Т", "Ф", "olympic", "32.13.2026", "02.06.2026")
        with self.assertRaises(ValidationError):
            db.create_tournament("Т", "Ф", "bad", "01.06.2026", "02.06.2026")
        tid = db.create_tournament("Т", "Ф", "olympic", "01.06.2026", "02.06.2026")
        with self.assertRaises(ValidationError):
            db.create_tournament("т", "Ф", "olympic", "01.06.2026", "02.06.2026")
        db.update_tournament(tid, "Т", "Ф", "round_robin", "01.06.2026", "05.06.2026", "Зал")
        self.assertEqual(db.get_tournament(tid)["system"], "round_robin")

    def test_dates(self):
        self.assertEqual(parse_date("25.05.2026"), "2026-05-25")
        self.assertEqual(parse_date("2026-05-25"), "2026-05-25")
        self.assertEqual(fmt_date("2026-05-25"), "25.05.2026")

    def test_delete_cascade(self):
        db = make_db()
        tid, _ = tournament_with_teams(db, 4)
        db.generate_bracket(tid)
        db.delete_tournament(tid)
        self.assertEqual(db.conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0], 0)
        self.assertEqual(db.conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0], 0)


class OlympicTests(unittest.TestCase):
    def test_seed_order(self):
        self.assertEqual(seed_order(8), [1, 8, 4, 5, 2, 7, 3, 6])
        self.assertEqual(seed_order(2), [1, 2])

    def test_sizes(self):
        for n, total_real in [(2, 1), (3, 3), (4, 3), (5, 7), (7, 7), (8, 7), (9, 15)]:
            db = make_db()
            tid, _ = tournament_with_teams(db, n)
            db.generate_bracket(tid)
            matches = db.list_matches(tid)
            size = 1
            while size < n:
                size *= 2
            self.assertEqual(len(matches), size - 1, f"n={n}")
            byes = [m for m in matches if m["status"] == "bye"]
            self.assertEqual(len(byes), size - n, f"n={n}")
            self.assertEqual(db.get_tournament(tid)["status"], "running")

    def test_bye_advances_and_full_play(self):
        db = make_db()
        tid, ids = tournament_with_teams(db, 5)
        db.generate_bracket(tid)
        matches = db.list_matches(tid)
        # всё, что ещё не сыграно, но имеет двух соперников, играем: побеждает команда 1
        guard = 0
        while True:
            guard += 1
            self.assertLess(guard, 50)
            ready = [m for m in db.list_matches(tid)
                     if m["status"] == "scheduled" and m["team1_id"] and m["team2_id"]]
            if not ready:
                break
            db.record_result(ready[0]["id"], 2, 1)
        self.assertEqual(db.get_tournament(tid)["status"], "finished")
        self.assertIsNotNone(db.tournament_winner(tid))
        final = db.list_matches(tid)[-1]
        self.assertEqual(final["round_name"], "Финал")
        self.assertIsNotNone(final["winner_id"])

    def test_no_draw_in_olympic(self):
        db = make_db()
        tid, _ = tournament_with_teams(db, 4)
        db.generate_bracket(tid)
        m = db.list_matches(tid)[0]
        with self.assertRaises(ValidationError):
            db.record_result(m["id"], 1, 1)
        with self.assertRaises(ValidationError):
            db.record_result(m["id"], -1, 1)
        with self.assertRaises(ValidationError):
            db.record_result(m["id"], "x", 1)

    def test_edit_and_clear_propagation(self):
        db = make_db()
        tid, _ = tournament_with_teams(db, 4)
        db.generate_bracket(tid)
        m1, m2, final = db.list_matches(tid)
        db.record_result(m1["id"], 3, 0)
        self.assertEqual(db.get_match(final["id"])["team1_id"], m1["team1_id"])
        db.record_result(m1["id"], 0, 3)          # меняем победителя
        self.assertEqual(db.get_match(final["id"])["team1_id"], m1["team2_id"])
        with self.assertRaises(ValidationError):
            db.record_result(final["id"], 1, 0)   # второй полуфинал не сыгран
        db.record_result(m2["id"], 1, 0)
        db.record_result(final["id"], 1, 0)
        self.assertEqual(db.get_tournament(tid)["status"], "finished")
        with self.assertRaises(ValidationError):
            db.record_result(m1["id"], 3, 0)      # финал уже сыгран
        with self.assertRaises(ValidationError):
            db.clear_result(m1["id"])
        db.clear_result(final["id"])
        self.assertEqual(db.get_tournament(tid)["status"], "running")
        db.clear_result(m1["id"])
        self.assertIsNone(db.get_match(final["id"])["team1_id"])
        with self.assertRaises(ValidationError):
            db.clear_result(m1["id"])             # уже очищен

    def test_regenerate_and_reset(self):
        db = make_db()
        tid, _ = tournament_with_teams(db, 4)
        db.generate_bracket(tid)
        db.generate_bracket(tid)                  # без результатов — можно пересоздать
        self.assertEqual(len(db.list_matches(tid)), 3)
        m = db.list_matches(tid)[0]
        db.record_result(m["id"], 1, 0)
        with self.assertRaises(ValidationError):
            db.generate_bracket(tid)
        with self.assertRaises(ValidationError):
            db.reset_bracket(tid)
        db.clear_result(m["id"])
        db.reset_bracket(tid)
        self.assertEqual(db.match_count(tid), 0)
        self.assertEqual(db.get_tournament(tid)["status"], "registration")

    def test_need_two_teams(self):
        db = make_db()
        tid, _ = tournament_with_teams(db, 1)
        with self.assertRaises(ValidationError):
            db.generate_bracket(tid)


class RoundRobinTests(unittest.TestCase):
    def test_pairs_unique(self):
        for n in (2, 3, 4, 5, 6, 7):
            db = make_db()
            tid, _ = tournament_with_teams(db, n, "round_robin")
            db.generate_bracket(tid)
            matches = db.list_matches(tid)
            self.assertEqual(len(matches), n * (n - 1) // 2, f"n={n}")
            pairs = {frozenset((m["team1_id"], m["team2_id"])) for m in matches}
            self.assertEqual(len(pairs), len(matches))
            by_round = {}
            for m in matches:
                by_round.setdefault(m["round"], []).extend([m["team1_id"], m["team2_id"]])
            for rnd, teams in by_round.items():
                self.assertEqual(len(teams), len(set(teams)), f"n={n} round {rnd}")

    def test_draws_and_standings(self):
        db = make_db()
        tid, ids = tournament_with_teams(db, 3, "round_robin")
        db.generate_bracket(tid)
        matches = db.list_matches(tid)
        db.record_result(matches[0]["id"], 2, 2)
        self.assertIsNone(db.get_match(matches[0]["id"])["winner_id"])
        db.record_result(matches[1]["id"], 3, 0)
        db.record_result(matches[2]["id"], 1, 0)
        self.assertEqual(db.get_tournament(tid)["status"], "finished")
        table = db.standings(tid)
        self.assertEqual(sum(r["played"] for r in table), 6)
        self.assertEqual(sum(r["points"] for r in table), 3 + 3 + 2)   # 2 очка за ничью + 2 победы
        self.assertEqual([r["place"] for r in table], [1, 2, 3])
        self.assertEqual(db.tournament_winner(tid), table[0]["name"])
        for r in table:
            self.assertEqual(r["diff"], r["gf"] - r["ga"])


class RatingTests(unittest.TestCase):
    def test_elo(self):
        db = make_db()
        tid, ids = tournament_with_teams(db, 2)
        db.generate_bracket(tid)
        m = db.list_matches(tid)[0]
        db.record_result(m["id"], 3, 1)
        winner = db.get_team(m["team1_id"])["rating"]
        loser = db.get_team(m["team2_id"])["rating"]
        self.assertAlmostEqual(winner, 1016.0)
        self.assertAlmostEqual(loser, 984.0)
        db.clear_result(m["id"])
        self.assertEqual(db.get_team(ids[0])["rating"], 1000.0)
        self.assertEqual(db.get_team(ids[1])["rating"], 1000.0)

    def test_rating_sum_constant(self):
        db = make_db()
        tid, ids = tournament_with_teams(db, 5, "round_robin")
        db.generate_bracket(tid)
        for i, m in enumerate(db.list_matches(tid)):
            db.record_result(m["id"], i % 4, (i * 3) % 4)
        total = sum(t["rating"] for t in db.list_teams())
        self.assertAlmostEqual(total, 5000.0, places=1)
        table = db.ratings_table()
        self.assertEqual([r["place"] for r in table], list(range(1, 6)))
        self.assertTrue(all(table[i]["rating"] >= table[i + 1]["rating"] for i in range(4)))

    def test_team_stats_and_history(self):
        db = make_db()
        tid, ids = tournament_with_teams(db, 2)
        db.generate_bracket(tid)
        m = db.list_matches(tid)[0]
        db.record_result(m["id"], 4, 2)
        s = db.team_stats(m["team1_id"])
        self.assertEqual((s["wins"], s["gf"], s["ga"], s["points"]), (1, 4, 2, 3))
        s = db.team_stats(m["team2_id"], tid)
        self.assertEqual((s["losses"], s["diff"]), (1, -2))
        h = db.team_history(m["team2_id"])
        self.assertEqual(h[0]["outcome"], "Поражение")
        self.assertEqual(h[0]["score"], "2 : 4")


class ScheduleTests(unittest.TestCase):
    def test_manual_schedule_and_conflicts(self):
        db = make_db()
        tid, _ = tournament_with_teams(db, 4)
        db.generate_bracket(tid)
        m1, m2, final = db.list_matches(tid)
        db.set_match_schedule(m1["id"], "02.06.2026", "10:00", "Зал 1")
        with self.assertRaises(ValidationError):
            db.set_match_schedule(m2["id"], "02.06.2026", "10:00", "зал 1")   # площадка занята
        db.set_match_schedule(m2["id"], "02.06.2026", "10:00", "Зал 2")       # другая площадка
        with self.assertRaises(ValidationError):
            db.set_match_schedule(m1["id"], "02.07.2026", "10:00", "Зал 1")   # вне дат турнира
        with self.assertRaises(ValidationError):
            db.set_match_schedule(m1["id"], "02.06.2026", "25:99", "Зал 1")
        with self.assertRaises(ValidationError):
            db.set_match_schedule(m1["id"], "bad", "10:00", "Зал 1")
        db.set_match_schedule(m1["id"], "", "", "")                           # сброс
        self.assertIsNone(db.get_match(m1["id"])["match_date"])

    def test_team_cannot_play_twice_at_once(self):
        db = make_db()
        tid, _ = tournament_with_teams(db, 3, "round_robin")
        db.generate_bracket(tid)
        ms = db.list_matches(tid)
        db.set_match_schedule(ms[0]["id"], "02.06.2026", "10:00", "Зал 1")
        # у любых двух матчей круговой на 3 команды есть общая команда
        with self.assertRaises(ValidationError):
            db.set_match_schedule(ms[1]["id"], "02.06.2026", "10:00", "Зал 2")

    def test_auto_schedule_no_conflicts(self):
        for system, n in [("olympic", 8), ("olympic", 5), ("round_robin", 6), ("round_robin", 5)]:
            db = make_db()
            tid, _ = tournament_with_teams(db, n, system)
            db.generate_bracket(tid)
            count = db.auto_schedule(tid, ["Зал 1", "Зал 2"], 3, "09:00", 90)
            matches = [m for m in db.list_matches(tid) if m["status"] != "bye"]
            self.assertEqual(count, len(matches))
            seen_venue, seen_team = set(), set()
            for m in matches:
                self.assertIsNotNone(m["match_date"])
                self.assertTrue("2026-06-01" <= m["match_date"] <= "2026-06-30")
                key = (m["match_date"], m["match_time"], m["venue"])
                self.assertNotIn(key, seen_venue)
                seen_venue.add(key)
                for team in (m["team1_id"], m["team2_id"]):
                    if team:
                        tk = (m["match_date"], m["match_time"], team)
                        self.assertNotIn(tk, seen_team)
                        seen_team.add(tk)

    def test_auto_schedule_order_olympic(self):
        db = make_db()
        tid, _ = tournament_with_teams(db, 8)
        db.generate_bracket(tid)
        db.auto_schedule(tid, ["Зал"], 4, "10:00", 120)
        matches = db.list_matches(tid)
        stamps = [(m["match_date"], m["match_time"], m["round"]) for m in matches]
        for a, b in zip(matches, matches[1:]):
            if a["round"] < b["round"]:
                self.assertLess((a["match_date"], a["match_time"]),
                                (b["match_date"], b["match_time"]))

    def test_auto_schedule_errors(self):
        db = make_db()
        tid = db.create_tournament("Т", "Ф", "olympic", "01.06.2026", "01.06.2026")
        with self.assertRaises(ValidationError):
            db.auto_schedule(tid, ["Зал"], 4)          # нет сетки
        ids = [add_team(db, f"К{i}") for i in range(8)]
        for t in ids:
            db.set_application_status(db.submit_application(tid, t), "approved")
        db.generate_bracket(tid)
        with self.assertRaises(ValidationError):
            db.auto_schedule(tid, ["Зал"], 1)          # 7 матчей не влезут в один день
        with self.assertRaises(ValidationError):
            db.auto_schedule(tid, [], 4)
        with self.assertRaises(ValidationError):
            db.auto_schedule(tid, ["Зал"], 12, "20:00", 120)   # за полночь
        self.assertEqual(db.auto_schedule(tid, ["А", "Б", "В", "Г"], 3), 7)


class ExportTests(unittest.TestCase):
    def test_exports(self):
        db = make_db()
        load_demo(db)
        tid = db.list_tournaments()[1]["id"]            # олимпийский или круговой
        for t in db.list_tournaments():
            if db.approved_teams(t["id"]):
                db.generate_bracket(t["id"])
                db.auto_schedule(t["id"], ["Зал"], 4)
        with tempfile.TemporaryDirectory() as tmp:
            for t in db.list_tournaments():
                for kind in ("standings", "schedule", "applications", "roster"):
                    title, headers, rows = db.export_rows(kind, t["id"])
                    self.assertTrue(rows or kind == "roster")
                    for ext in ("csv", "xlsx"):
                        path = os.path.join(tmp, f"{kind}_{t['id']}.{ext}")
                        export_to_file(path, title, headers, rows)
                        self.assertGreater(os.path.getsize(path), 0)
            title, headers, rows = db.export_rows("ratings")
            path = os.path.join(tmp, "r.csv")
            export_to_file(path, title, headers, rows)
            with open(path, encoding="utf-8-sig", newline="") as f:
                data = list(csv.reader(f, delimiter=";"))
            self.assertEqual(data[0], headers)
            self.assertEqual(len(data) - 1, len(rows))
            from openpyxl import load_workbook
            xp = os.path.join(tmp, "r.xlsx")
            export_to_file(xp, title, headers, rows)
            ws = load_workbook(xp).active
            self.assertEqual([c.value for c in ws[1]], headers)
            self.assertEqual(ws.max_row, len(rows) + 1)
        with self.assertRaises(ValidationError):
            db.export_rows("standings", None)
        with self.assertRaises(ValidationError):
            db.export_rows("unknown", tid)


class DemoTests(unittest.TestCase):
    def test_demo_once(self):
        db = make_db()
        self.assertTrue(load_demo(db))
        self.assertFalse(load_demo(db))
        self.assertIsNotNone(db.login("coach", "coach"))
        self.assertEqual(len(db.list_teams()), 8)
        self.assertEqual(len(db.list_tournaments()), 2)


if __name__ == "__main__":
    unittest.main(verbosity=1)



class OfficialLeagueImportTests(unittest.TestCase):
    def test_import_official_teams_is_idempotent(self):
        from website_import import import_magadan_teams

        db = make_db()
        first = import_magadan_teams(db)
        self.assertEqual(first["added_teams"], 14)
        self.assertEqual(first["imported_rows"], 22)
        self.assertEqual(first["total_teams"], 14)
        self.assertEqual(
            db.conn.execute(
                "SELECT COUNT(*) FROM team_season_standings WHERE season='2026-2027'"
            ).fetchone()[0], 11
        )
        self.assertEqual(
            db.conn.execute(
                "SELECT COUNT(*) FROM team_season_standings WHERE season='2025-2026'"
            ).fetchone()[0], 11
        )
        self.assertEqual(len(db.list_teams()), 14)
        self.assertEqual(
            db.conn.execute("SELECT COUNT(*) FROM players").fetchone()[0], 0,
            "Импорт не должен выдумывать составы игроков",
        )

        second = import_magadan_teams(db)
        self.assertEqual(second["added_teams"], 0)
        self.assertEqual(second["imported_rows"], 22)
        self.assertEqual(second["total_teams"], 14)
        self.assertEqual(len(db.list_team_season_stats()), 22)

    def test_old_season_only_teams_are_kept_as_archive(self):
        from website_import import import_magadan_teams

        db = make_db()
        import_magadan_teams(db)
        archive_names = {
            row["name"] for row in db.list_teams()
            if not db.list_team_season_stats("2026-2027", row["id"])
        }
        self.assertEqual(archive_names, {"Бей-Беги", "Больные Колени", "Искра"})
