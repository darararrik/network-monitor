import socket
import json
import threading
import time
from typing import Dict, Any
from src.core.network_monitor import NetworkMonitor
from PyQt6.QtCore import QObject, pyqtSignal

class NetworkServer(QObject):
    """Класс для управления сетевым сервером"""
    client_connected = pyqtSignal(str, int)  # ip, port
    client_disconnected = pyqtSignal(str, int)  # ip, port
    server_started = pyqtSignal(int)  # port
    server_stopped = pyqtSignal()
    log_message = pyqtSignal(str)  # сообщение для лога
    
    def __init__(self):
        super().__init__()
        self.server_socket = None
        self.is_running = False
        self.clients = {}  # {client_id: (client_socket, client_address)}
        self.client_id_counter = 0
        self.server_thread = None
        self.network_monitor = NetworkMonitor()
        
    def start_server(self, port=5000):
        """Запуск сервера на указанном порту"""
        if self.is_running:
            self.log_message.emit("Сервер уже запущен")
            return False
            
        try:
            # Создаем серверный сокет
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', port))
            self.server_socket.listen(5)
            
            # Запускаем сервер в отдельном потоке
            self.is_running = True
            self.server_thread = threading.Thread(target=self._accept_connections)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            self.log_message.emit(f"Сервер запущен на порту {port}")
            self.server_started.emit(port)
            return True
            
        except Exception as e:
            self.log_message.emit(f"Ошибка при запуске сервера: {str(e)}")
            return False
            
    def stop_server(self):
        """Остановка сервера"""
        if not self.is_running:
            return
            
        try:
            # Останавливаем сервер
            self.is_running = False
            
            # Закрываем все соединения с клиентами
            for client_id, (client_socket, client_address) in list(self.clients.items()):
                try:
                    client_socket.close()
                    self.client_disconnected.emit(client_address[0], client_address[1])
                except:
                    pass
            
            # Закрываем серверный сокет
            if self.server_socket:
                self.server_socket.close()
                
            self.clients = {}
            self.client_id_counter = 0
            self.log_message.emit("Сервер остановлен")
            self.server_stopped.emit()
            
        except Exception as e:
            self.log_message.emit(f"Ошибка при остановке сервера: {str(e)}")
            
    def _accept_connections(self):
        """Прием подключений от клиентов (запускается в отдельном потоке)"""
        try:
            self.server_socket.settimeout(1.0)  # Таймаут для проверки флага остановки
            
            while self.is_running:
                try:
                    # Принимаем подключение от клиента
                    client_socket, client_address = self.server_socket.accept()
                    
                    # Добавляем клиента в список
                    client_id = self.client_id_counter
                    self.client_id_counter += 1
                    self.clients[client_id] = (client_socket, client_address)
                    
                    # Запускаем поток для обработки клиента
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_id, client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                    # Отправляем сигнал о подключении клиента
                    self.log_message.emit(f"Клиент подключен: {client_address[0]}:{client_address[1]}")
                    self.client_connected.emit(client_address[0], client_address[1])
                    
                except socket.timeout:
                    # Тайм-аут нужен для проверки флага остановки
                    continue
                except Exception as e:
                    if self.is_running:
                        self.log_message.emit(f"Ошибка при приеме подключения: {str(e)}")
                    break
                    
        except Exception as e:
            if self.is_running:
                self.log_message.emit(f"Ошибка в цикле приема подключений: {str(e)}")
                
        finally:
            # Если поток завершился, но сервер еще запущен, останавливаем его
            if self.is_running:
                self.stop_server()
                
    def _handle_client(self, client_id, client_socket, client_address):
        """Обработка клиента (запускается в отдельном потоке)"""
        try:
            # Настраиваем таймаут для сокета
            client_socket.settimeout(1.0)
            
            while self.is_running:
                try:
                    # Читаем данные от клиента
                    data = client_socket.recv(4096)
                    if not data:
                        # Клиент отключился
                        break
                        
                    # Обрабатываем данные от клиента
                    self._process_client_data(client_id, data, client_address)
                    
                except socket.timeout:
                    # Тайм-аут нужен для проверки флага остановки
                    continue
                except Exception as e:
                    self.log_message.emit(f"Ошибка при обработке данных от клиента {client_address[0]}:{client_address[1]}: {str(e)}")
                    break
                    
        except Exception as e:
            self.log_message.emit(f"Ошибка в обработчике клиента {client_address[0]}:{client_address[1]}: {str(e)}")
            
        finally:
            # Закрываем соединение с клиентом
            try:
                client_socket.close()
            except:
                pass
                
            # Удаляем клиента из списка, если он еще там
            if client_id in self.clients:
                del self.clients[client_id]
                
            # Отправляем сигнал об отключении клиента
            self.log_message.emit(f"Клиент отключен: {client_address[0]}:{client_address[1]}")
            self.client_disconnected.emit(client_address[0], client_address[1])
            
    def _process_client_data(self, client_id, data, client_address):
        """Обработка данных от клиента"""
        try:
            # Пытаемся декодировать данные как JSON
            message = json.loads(data.decode('utf-8'))
            
            # Логируем полученное сообщение
            self.log_message.emit(f"Получено от {client_address[0]}:{client_address[1]}: {message}")
            
            # Обрабатываем различные типы сообщений
            if 'type' in message:
                # Здесь можно добавить логику обработки различных типов сообщений
                if message['type'] == 'get_adapters':
                    self._send_adapters_list(client_id)
                elif message['type'] == 'get_adapter_info':
                    self._send_adapter_info(client_id, message.get('adapter_name'))
                elif message['type'] == 'get_speeds':
                    self._send_speeds(client_id, message.get('adapter_name'))
                else:
                    self.log_message.emit(f"Неизвестный тип сообщения: {message['type']}")
            else:
                self.log_message.emit(f"Получено сообщение без типа: {message}")
                
        except json.JSONDecodeError:
            self.log_message.emit(f"Получены некорректные данные от {client_address[0]}:{client_address[1]}")
        except Exception as e:
            self.log_message.emit(f"Ошибка при обработке данных от клиента {client_address[0]}:{client_address[1]}: {str(e)}")
            
    def _send_adapters_list(self, client_id):
        """Отправка списка адаптеров клиенту"""
        if client_id not in self.clients:
            return
            
        try:
            # Здесь будет логика получения списка адаптеров
            # Пока отправляем тестовые данные
            adapters = ["Adapter 1", "Adapter 2", "Ethernet", "Wi-Fi"]
            
            # Формируем и отправляем сообщение
            message = {
                'type': 'adapters_list',
                'adapters': adapters
            }
            self._send_message(client_id, message)
            
        except Exception as e:
            self.log_message.emit(f"Ошибка при отправке списка адаптеров: {str(e)}")
            
    def _send_adapter_info(self, client_id, adapter_name):
        """Отправка информации об адаптере клиенту"""
        if client_id not in self.clients or not adapter_name:
            return
            
        try:
            # Здесь будет логика получения информации об адаптере
            # Пока отправляем тестовые данные
            adapter_info = {
                'id': '12345',
                'description': f'Description for {adapter_name}',
                'interface_type': 'Ethernet',
                'ip': '192.168.1.100',
                'mac': '00:11:22:33:44:55',
                'speed': '1 Gbps',
                'mtu': '1500',
                'status': 'Up'
            }
            
            # Формируем и отправляем сообщение
            message = {
                'type': 'adapter_info',
                'adapter_name': adapter_name,
                'info': adapter_info
            }
            self._send_message(client_id, message)
            
        except Exception as e:
            self.log_message.emit(f"Ошибка при отправке информации об адаптере: {str(e)}")
            
    def _send_speeds(self, client_id, adapter_name):
        """Отправка информации о скорости сети клиенту"""
        if client_id not in self.clients:
            return
            
        try:
            # Здесь будет логика получения информации о скорости сети
            # Пока отправляем тестовые данные
            import random
            download = random.uniform(1.0, 10.0)  # KB/s
            upload = random.uniform(0.5, 5.0)  # KB/s
            
            # Формируем и отправляем сообщение
            message = {
                'type': 'speeds',
                'adapter_name': adapter_name,
                'download': download,
                'upload': upload,
                'time': time.strftime('%H:%M:%S')
            }
            self._send_message(client_id, message)
            
        except Exception as e:
            self.log_message.emit(f"Ошибка при отправке информации о скорости: {str(e)}")
            
    def _send_message(self, client_id, message):
        """Отправка сообщения клиенту"""
        if client_id not in self.clients:
            return False
            
        try:
            # Получаем сокет клиента
            client_socket, client_address = self.clients[client_id]
            
            # Сериализуем сообщение в JSON
            data = json.dumps(message).encode('utf-8')
            
            # Отправляем данные
            client_socket.sendall(data)
            return True
            
        except Exception as e:
            self.log_message.emit(f"Ошибка при отправке сообщения клиенту {client_address[0]}:{client_address[1]}: {str(e)}")
            return False
            
    def broadcast_message(self, message):
        """Отправка сообщения всем подключенным клиентам"""
        for client_id in list(self.clients.keys()):
            self._send_message(client_id, message)
            
    def get_clients_count(self):
        """Получение количества подключенных клиентов"""
        return len(self.clients)
        
    def get_clients_list(self):
        """Получение списка подключенных клиентов"""
        return [(client_address[0], client_address[1]) for _, client_address in self.clients.values()]

    def process_command(self, command: dict) -> dict:
        """Обрабатывает команды от клиента"""
        try:
            cmd_type = command.get('type')
            
            if cmd_type == 'get_adapters':
                adapters = self.network_monitor.get_adapters()
                print(f"Отправляем список адаптеров: {adapters}")
                return {
                    'type': 'adapters_list',
                    'adapters': adapters
                }
                
            elif cmd_type == 'get_adapter_info':
                adapter_name = command.get('adapter')
                print(f"Получаем информацию об адаптере: {adapter_name}")
                info = self.network_monitor.get_adapter_info(adapter_name)
                print(f"Информация об адаптере: {info}")
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