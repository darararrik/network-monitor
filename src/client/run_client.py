import sys
import os
from PyQt6.QtWidgets import QApplication

# Добавляем корневую директорию проекта в PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.client.client_window import ClientWindow

def main():
    """Запуск клиентского приложения"""
    app = QApplication(sys.argv)
    window = ClientWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 