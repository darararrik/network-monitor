import sys
import os
import socket
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.network_server import NetworkServer

def get_ip_addresses():
    """Получает список всех IP-адресов компьютера"""
    ip_addresses = []
    try:
        # Получаем имя компьютера
        hostname = socket.gethostname()
        # Получаем все IP-адреса для этого имени
        ips = socket.getaddrinfo(hostname, None)
        
        # Фильтруем только IPv4 адреса
        for ip in ips:
            if ip[0] == socket.AF_INET:  # только IPv4
                ip_addr = ip[4][0]
                if not ip_addr.startswith('127.'):  # исключаем локальный адрес
                    ip_addresses.append(ip_addr)
                    
        # Добавляем внешний IP, если есть подключение к интернету
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            external_ip = s.getsockname()[0]
            if external_ip not in ip_addresses:
                ip_addresses.append(external_ip)
            s.close()
        except:
            pass
            
    except Exception as e:
        print(f"Ошибка при получении IP-адресов: {e}")
    
    return ip_addresses

def main():
    # Создаем и запускаем сервер
    server = NetworkServer()
    try:
        print("\n=== Информация для подключения ===")
        print(f"Порт: {server.port}")
        print("\nДоступные IP-адреса:")
        for ip in get_ip_addresses():
            print(f"* {ip}")
        print("\nИспользуйте любой из этих адресов для подключения клиента.")
        print("Для локального подключения можно использовать: 127.0.0.1")
        print("\nЗапуск сервера...")
        
        server.start()  # Эта функция теперь блокирующая
        
    except KeyboardInterrupt:
        print("\nПолучен сигнал остановки...")
    finally:
        print("Останавливаем сервер...")
        server.stop()

if __name__ == "__main__":
    main() 