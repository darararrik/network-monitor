import socket
import json
import threading
import time
from typing import Dict, Any
from src.core.network_monitor import NetworkMonitor

class NetworkServer:
    def __init__(self, host: str = '0.0.0.0', port: int = 5000):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients: Dict[str, socket.socket] = {}
        self.network_monitor = NetworkMonitor()
        self.is_running = False
        self.accept_thread = None

    def start(self):
        """Запускает сервер"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Позволяет повторно использовать адрес
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.is_running = True
            print(f"Сервер запущен на {self.host}:{self.port}")
            
            # Запускаем отдельный поток для приема подключений
            self.accept_thread = threading.Thread(target=self.accept_connections)
            self.accept_thread.daemon = True
            self.accept_thread.start()
            
            # Держим основной поток живым
            while self.is_running:
                time.sleep(1)
                
        except Exception as e:
            print(f"Ошибка при запуске сервера: {e}")
            self.stop()

    def stop(self):
        """Останавливает сервер"""
        self.is_running = False
        
        # Закрываем все клиентские соединения
        for client in list(self.clients.values()):
            try:
                client.close()
            except:
                pass
        self.clients.clear()
        
        # Закрываем серверный сокет
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
            
        print("Сервер остановлен.")

    def accept_connections(self):
        """Принимает подключения от клиентов"""
        while self.is_running and self.server_socket:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"Подключение от {address}")
                
                # Запускаем отдельный поток для обработки клиента
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
                
                self.clients[address[0]] = client_socket
            except Exception as e:
                if self.is_running:
                    print(f"Ошибка при приеме подключения: {e}")
                break

    def handle_client(self, client_socket: socket.socket, address: tuple):
        """Обрабатывает подключение клиента"""
        print(f"Начало обработки клиента {address}")
        try:
            while self.is_running:
                # Получаем команду от клиента
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break

                print(f"Получена команда от {address}: {data}")
                command = json.loads(data)
                
                # Обрабатываем команду
                response = self.process_command(command)
                
                # Отправляем ответ клиенту
                response_data = json.dumps(response).encode('utf-8')
                client_socket.send(response_data)
                print(f"Отправлен ответ клиенту {address}: {response}")
                
        except Exception as e:
            print(f"Ошибка при обработке клиента {address}: {e}")
        finally:
            print(f"Закрытие соединения с клиентом {address}")
            try:
                client_socket.close()
            except:
                pass
            if address[0] in self.clients:
                del self.clients[address[0]]

    def process_command(self, command: dict) -> dict:
        """Обрабатывает команды от клиента"""
        try:
            cmd_type = command.get('type')
            
            if cmd_type == 'get_adapters':
                adapters = self.network_monitor.get_adapters()
                return {
                    'type': 'adapters_list',
                    'adapters': adapters
                }
                
            elif cmd_type == 'get_adapter_info':
                adapter_name = command.get('adapter')
                info = self.network_monitor.get_adapter_info(adapter_name)
                return {
                    'type': 'adapter_info',
                    'info': info
                }
                
            elif cmd_type == 'start_measurement':
                adapter_name = command.get('adapter')
                self.network_monitor.start_measurement(adapter_name)
                return {'type': 'measurement_started'}
                
            elif cmd_type == 'stop_measurement':
                self.network_monitor.stop_measurement()
                return {'type': 'measurement_stopped'}
                
            elif cmd_type == 'get_speeds':
                speeds = self.network_monitor.get_current_speeds()
                return {
                    'type': 'speeds_data',
                    'data': speeds
                }
                
            return {'type': 'error', 'message': 'Неизвестная команда'}
            
        except Exception as e:
            print(f"Ошибка при обработке команды: {e}")
            return {'type': 'error', 'message': str(e)} 