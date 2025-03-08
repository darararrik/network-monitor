import socket
import json
import threading
from typing import Dict, Any
from src.core.network_monitor import NetworkMonitor

class NetworkServer:
    def __init__(self, host: str = '0.0.0.0', port: int = 5000):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.clients: Dict[str, socket.socket] = {}
        self.network_monitor = NetworkMonitor()
        self.is_running = False

    def start(self):
        """Запускает сервер"""
        self.is_running = True
        print(f"Сервер запущен на {self.host}:{self.port}")
        
        # Запускаем отдельный поток для приема подключений
        accept_thread = threading.Thread(target=self.accept_connections)
        accept_thread.daemon = True
        accept_thread.start()

    def stop(self):
        """Останавливает сервер"""
        self.is_running = False
        for client in self.clients.values():
            client.close()
        self.server_socket.close()

    def accept_connections(self):
        """Принимает подключения от клиентов"""
        while self.is_running:
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
                print(f"Ошибка при приеме подключения: {e}")
                break

    def handle_client(self, client_socket: socket.socket, address: tuple):
        """Обрабатывает подключение клиента"""
        try:
            while self.is_running:
                # Получаем команду от клиента
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break

                command = json.loads(data)
                
                # Обрабатываем команду
                response = self.process_command(command)
                
                # Отправляем ответ клиенту
                client_socket.send(json.dumps(response).encode('utf-8'))
                
        except Exception as e:
            print(f"Ошибка при обработке клиента {address}: {e}")
        finally:
            client_socket.close()
            if address[0] in self.clients:
                del self.clients[address[0]]

    def process_command(self, command: dict) -> dict:
        """Обрабатывает команды от клиента"""
        cmd_type = command.get('type')
        
        if cmd_type == 'get_adapters':
            return {
                'type': 'adapters_list',
                'adapters': self.network_monitor.get_adapters()
            }
            
        elif cmd_type == 'get_adapter_info':
            adapter_name = command.get('adapter')
            return {
                'type': 'adapter_info',
                'info': self.network_monitor.get_adapter_info(adapter_name)
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