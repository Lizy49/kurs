"""Превращает assets/ball.png в иконку с прозрачным фоном: icon.png + icon.ico."""
import os
from collections import deque
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QColor

BASE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE, "assets")

src = QImage(os.path.join(ASSETS, "ball.png"))
if src.isNull():
    raise SystemExit("Сначала сохрани картинку мяча в assets/ball.png")

img = src.convertToFormat(QImage.Format.Format_ARGB32)
w, h = img.width(), img.height()

def is_white(x, y):
    c = img.pixelColor(x, y)
    return c.red() >= 240 and c.green() >= 240 and c.blue() >= 240

# Обход в ширину от краёв картинки вглубь:
# стираем только белый фон, белые полосы внутри мяча не трогаем.
seen = [[False] * w for _ in range(h)]
queue = deque([(x, 0) for x in range(w)] + [(x, h - 1) for x in range(w)] +
              [(0, y) for y in range(h)] + [(w - 1, y) for y in range(h)])
while queue:
    x, y = queue.popleft()
    if not (0 <= x < w and 0 <= y < h) or seen[y][x]:
        continue
    seen[y][x] = True
    if not is_white(x, y):
        continue
    img.setPixelColor(x, y, QColor(0, 0, 0, 0))
    queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

img = img.scaled(256, 256,
                 Qt.AspectRatioMode.KeepAspectRatio,
                 Qt.TransformationMode.SmoothTransformation)
img.save(os.path.join(ASSETS, "icon.png"))
img.save(os.path.join(ASSETS, "icon.ico"))  # для .exe и ярлыков
print("Готово: assets/icon.png и assets/icon.ico")