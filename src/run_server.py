import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.network_server import NetworkServer

def main():
    # Создаем и запускаем сервер
    server = NetworkServer()
    try:
        server.start()
        print("Сервер запущен. Нажмите Ctrl+C для остановки.")
        while True:
            pass
    except KeyboardInterrupt:
        print("\nОстанавливаем сервер...")
        server.stop()
        print("Сервер остановлен.")

if __name__ == "__main__":
    main() 