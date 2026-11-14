"""Безопасный сброс локальной базы АРМ «Спортивный организатор»."""

from datetime import datetime
from pathlib import Path
import shutil

from database import Database

DB_PATH = Path(__file__).with_name("sport_arm.db")


def main():
    print("СБРОС БАЗЫ АРМ «СПОРТИВНЫЙ ОРГАНИЗАТОР»")
    print(f"Файл базы: {DB_PATH}")
    print("Сначала закройте основное приложение.")
    if input("Для очистки введите RESET: ").strip() != "RESET":
        print("Отменено. База не изменена.")
        return 0

    backup_path = None
    if DB_PATH.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = DB_PATH.with_name(f"sport_arm_backup_{stamp}.db")
        shutil.copy2(DB_PATH, backup_path)
        print(f"Резервная копия: {backup_path}")

    try:
        if DB_PATH.exists():
            DB_PATH.unlink()
        db = Database(str(DB_PATH))
        db.close()
    except Exception:
        if backup_path and backup_path.exists():
            if DB_PATH.exists():
                DB_PATH.unlink()
            shutil.copy2(backup_path, DB_PATH)
        raise

    print("Создана новая пустая база данных.")
    print("Организатор: admin / admin")
    print("Откройте программу и импортируйте команды в разделе «Команды».")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
