import sys
import os
from PyQt6.QtWidgets import QApplication

# Добавляем путь к корневой директории проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.network_monitor_window import NetworkMonitorWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NetworkMonitorWindow()
    window.show()
    sys.exit(app.exec())