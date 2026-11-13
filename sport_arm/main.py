"""Запуск PyQt6-версии АРМ «Спортивный организатор»."""

import sys

try:
    from qt_main import main
except ImportError as exc:
    raise SystemExit(
        "Не удалось загрузить PyQt6. Установите зависимости командой: "
        "python -m pip install -r requirements.txt"
    ) from exc


if __name__ == "__main__":
    sys.exit(main())
