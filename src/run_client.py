import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication
from src.ui.network_monitor_window import NetworkMonitorWindow

def main():
    if len(sys.argv) != 2:
        print("Использование: python run_client.py <ip_адрес_сервера>")
        sys.exit(1)
        
    server_host = sys.argv[1]
    
    app = QApplication(sys.argv)
    window = NetworkMonitorWindow(server_mode=False, server_host=server_host)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 