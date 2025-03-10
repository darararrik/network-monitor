import sys
import os
from PyQt6.QtWidgets import QApplication
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets

# Регистрируем PlotWidget для использования с pyqtgraph
pg.setConfigOption('background', 'w')  # Белый фон для графиков
pg.setConfigOption('foreground', 'k')  # Черный цвет для текста
pg.setConfigOption('antialias', True)  # Включаем сглаживание

# Добавляем путь к корневой директории проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.network_monitor_window import NetworkMonitorWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NetworkMonitorWindow()
    window.show()
    sys.exit(app.exec())