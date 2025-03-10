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
    adapters_list_received = pyqtSignal(str, list)  # client_id, adapters
    adapter_info_received = pyqtSignal(str, str, dict)  # client_id, adapter, info
    speeds_data_received = pyqtSignal(str, str, dict)  # client_id, adapter, data
    
    def __init__(self):
        super().__init__()
        self.server_socket = None
        self.is_running = False
        self.clients = {}  # {client_id: (client_socket, client_address)}
        self.client_info = {}  # {client_id: {'pc_name': 'PC_NAME'}}
        self.client_id_counter = 0
        self.server_thread = None
        self.network_monitor = NetworkMonitor()
        self.port = None
        
    def get_ip_addresses(self):
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
            self.log_message.emit(f"Ошибка при получении IP-адресов: {e}")
        
        return ip_addresses

    def get_local_ip(self):
        """Получает локальный IPv4 адрес компьютера"""
        try:
            # Создаем временное подключение для определения IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            # Если не удалось определить IP через подключение,
            # пробуем получить через hostname
            try:
                hostname = socket.gethostname()
                ip = socket.gethostbyname(hostname)
                return ip
            except:
                return "127.0.0.1"

    def start_server(self, port=5000):
        """Запуск сервера на указанном порту"""
        if self.is_running:
            self.log_message.emit("Сервер уже запущен")
            return False
            
        try:
            # Получаем локальный IP адрес
            local_ip = self.get_local_ip()
            
            # Создаем серверный сокет
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((local_ip, port))
            
            # Сохраняем порт
            self.port = port
            
            # Выводим информацию о запуске
            self.log_message.emit("\n=== Информация о сервере ===")
            self.log_message.emit(f"Сервер запущен на {local_ip}:{port}")
            self.log_message.emit("\nДля тестирования на этом компьютере:")
            self.log_message.emit(f"1. Используйте IP-адрес: {local_ip}")
            self.log_message.emit(f"2. Порт в обоих случаях: {port}")
            
            # Запускаем сервер в отдельном потоке
            self.is_running = True
            self.server_thread = threading.Thread(target=self._accept_connections)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            self.log_message.emit(f"\nСервер успешно запущен и готов к подключениям")
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
        """Цикл приема подключений"""
        try:
            # Настраиваем сокет для приема подключений
            self.server_socket.listen(5)
            self.log_message.emit(f"Сервер запущен на порту {self.port}")
            self.server_started.emit(self.port)
            
            # Устанавливаем таймаут для проверки флага остановки
            self.server_socket.settimeout(1.0)  # Таймаут для проверки флага остановки
            
            while self.is_running:
                try:
                    # Принимаем подключение от клиента
                    client_socket, client_address = self.server_socket.accept()
                    
                    # Добавляем клиента в список, используя строковый ID в формате ip:port
                    client_id = f"{client_address[0]}:{client_address[1]}"
                    self.log_message.emit(f"Новое подключение с ID: {client_id}")
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
            
            # Сначала пробуем обработать как сообщение от клиентского приложения
            if 'type' in message:
                # Проверяем, есть ли обработчик для этого типа сообщения в _process_client_message
                if message['type'] in ['client_info', 'adapters_list', 'adapter_info', 'speeds_data']:
                    # Обрабатываем как сообщение от клиентского приложения
                    self.log_message.emit(f"Обрабатываем сообщение типа {message['type']} от клиента {client_id}")
                    self._process_client_message(client_id, message)
                    return
                    
                # Обрабатываем различные типы запросов к серверу
                try:
                    if message['type'] == 'get_adapters':
                        self._send_adapters_list(client_id)
                    elif message['type'] == 'get_adapter_info':
                        self._send_adapter_info(client_id, message.get('adapter'))
                    elif message['type'] == 'get_speeds':
                        self._send_speeds(client_id, message.get('adapter'))
                    elif message['type'] == 'start_measurement':
                        # Запускаем измерение для указанного адаптера
                        adapter_name = message.get('adapter')
                        if not adapter_name:
                            raise ValueError("Не указан адаптер для измерения")
                        self.network_monitor.start_measurement(adapter_name)
                        response = {
                            'type': 'measurement_started',
                            'adapter': adapter_name
                        }
                        client_socket = self.clients[client_id][0]
                        self._send_message(client_socket, response)
                        self.log_message.emit(f"Запущено измерение для адаптера {adapter_name}")
                    elif message['type'] == 'stop_measurement':
                        # Останавливаем измерение
                        self.network_monitor.stop_measurement()
                        response = {
                            'type': 'measurement_stopped'
                        }
                        client_socket = self.clients[client_id][0]
                        self._send_message(client_socket, response)
                        self.log_message.emit("Измерение остановлено")
                    else:
                        self.log_message.emit(f"Неизвестный тип сообщения: {message['type']}")
                except Exception as e:
                    error_message = {
                        'type': 'error',
                        'message': str(e)
                    }
                    client_socket = self.clients[client_id][0]
                    self._send_message(client_socket, error_message)
                    self.log_message.emit(f"Ошибка при обработке сообщения: {str(e)}")
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
            # Получаем реальный список адаптеров через NetworkMonitor
            adapters = self.network_monitor.get_adapters()
            
            # Формируем и отправляем сообщение
            message = {
                'type': 'adapters_list',
                'adapters': adapters
            }
            self._send_message(self.clients[client_id][0], message)
            self.log_message.emit(f"Отправлен список адаптеров: {adapters}")
            
        except Exception as e:
            self.log_message.emit(f"Ошибка при отправке списка адаптеров: {str(e)}")
            
    def _send_adapter_info(self, client_id, adapter_name):
        """Отправка информации об адаптере клиенту"""
        if client_id not in self.clients or not adapter_name:
            return
            
        try:
            # Получаем реальную информацию об адаптере через NetworkMonitor
            adapter_info = self.network_monitor.get_adapter_info(adapter_name)
            
            # Формируем и отправляем сообщение
            message = {
                'type': 'adapter_info',
                'adapter_name': adapter_name,
                'info': adapter_info
            }
            self._send_message(self.clients[client_id][0], message)
            self.log_message.emit(f"Отправлена информация об адаптере {adapter_name}")
            
        except Exception as e:
            self.log_message.emit(f"Ошибка при отправке информации об адаптере: {str(e)}")
            
    def _send_speeds(self, client_id, adapter_name=None):
        """Отправка информации о скорости сети клиенту"""
        if client_id not in self.clients:
            return
            
        try:
            # Если адаптер не указан, используем текущий измеряемый адаптер
            if adapter_name is None:
                adapter_name = self.network_monitor.selected_adapter
                
            if adapter_name is None:
                self.log_message.emit("Ошибка: не указан адаптер для измерения скорости")
                error_message = {
                    'type': 'error',
                    'message': 'Не указан адаптер для измерения скорости'
                }
                self._send_message(self.clients[client_id][0], error_message)
                return
                
            # Получаем реальные данные о скорости через NetworkMonitor
            speeds = self.network_monitor.get_current_speeds()
            if speeds is None:
                error_message = {
                    'type': 'error',
                    'message': 'Не удалось получить данные о скорости'
                }
                self._send_message(self.clients[client_id][0], error_message)
                return
                
            # Формируем и отправляем сообщение
            message = {
                'type': 'speeds',
                'adapter_name': adapter_name,
                'speeds': speeds,
                'time': f"{speeds['stats']['duration']} сек"  # Используем длительность замера вместо текущего времени
            }
            self._send_message(self.clients[client_id][0], message)
            self.log_message.emit(f"Отправлена информация о скорости для адаптера {adapter_name}")
            
        except Exception as e:
            self.log_message.emit(f"Ошибка при отправке информации о скорости: {str(e)}")
            error_message = {
                'type': 'error',
                'message': str(e)
            }
            self._send_message(self.clients[client_id][0], error_message)
            
    def _send_message(self, client_socket, message):
        """Отправка сообщения клиенту
        
        Args:
            client_socket: Сокет клиента
            message: Сообщение для отправки
        """
        try:
            # Сериализуем сообщение в JSON
            json_data = json.dumps(message)
            # Отправляем данные
            client_socket.sendall(json_data.encode('utf-8'))
        except Exception as e:
            self.log_message.emit(f"Ошибка при отправке сообщения: {str(e)}")
            
    def broadcast_message(self, message):
        """Отправка сообщения всем подключенным клиентам"""
        for client_id in list(self.clients.keys()):
            self._send_message(self.clients[client_id][0], message)
            
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

    def request_adapters_list(self, client_id):
        """Запрос списка адаптеров у клиента
        
        Args:
            client_id: Идентификатор клиента в формате ip:port
        """
        self.log_message.emit(f"Запрашиваем список адаптеров для клиента {client_id}")
        self.log_message.emit(f"Сервер запущен: {self.is_running}")
        self.log_message.emit(f"Список клиентов: {list(self.clients.keys())}")
        
        if not self.is_running:
            self.log_message.emit("Ошибка: сервер не запущен")
            return False
            
        if client_id not in self.clients:
            self.log_message.emit(f"Ошибка: клиент {client_id} не найден в списке")
            return False
            
        message = {
            'type': 'get_adapters',
        }
        
        try:
            client_socket = self.clients[client_id][0]
            self._send_message(client_socket, message)
            return True
        except Exception as e:
            self.log_message.emit(f"Ошибка при запросе списка адаптеров: {e}")
            return False
            
    def request_adapter_info(self, client_id, adapter):
        """Запрос информации об адаптере у клиента
        
        Args:
            client_id: Идентификатор клиента в формате ip:port
            adapter: Имя адаптера
        """
        if not self.is_running or client_id not in self.clients:
            return False
            
        message = {
            'type': 'get_adapter_info',
            'adapter': adapter
        }
        
        try:
            client_socket = self.clients[client_id][0]
            self._send_message(client_socket, message)
            return True
        except Exception as e:
            self.log_message.emit(f"Ошибка при запросе информации об адаптере: {e}")
            return False
            
    def start_monitoring(self, client_id, adapter):
        """Запуск мониторинга скорости на клиенте
        
        Args:
            client_id: Идентификатор клиента в формате ip:port
            adapter: Имя адаптера
        """
        if not self.is_running or client_id not in self.clients:
            return False
            
        message = {
            'type': 'start_monitoring',
            'adapter': adapter
        }
        
        try:
            client_socket = self.clients[client_id][0]
            self._send_message(client_socket, message)
            return True
        except Exception as e:
            self.log_message.emit(f"Ошибка при запуске мониторинга: {e}")
            return False
            
    def stop_monitoring(self, client_id):
        """Остановка мониторинга скорости на клиенте
        
        Args:
            client_id: Идентификатор клиента в формате ip:port
        """
        if not self.is_running or client_id not in self.clients:
            return False
            
        message = {
            'type': 'stop_monitoring'
        }
        
        try:
            client_socket = self.clients[client_id][0]
            self._send_message(client_socket, message)
            return True
        except Exception as e:
            self.log_message.emit(f"Ошибка при остановке мониторинга: {e}")
            return False

    def _process_client_message(self, client_id, message):
        """Обработка сообщения от клиента
        
        Args:
            client_id: Идентификатор клиента
            message: Полученное сообщение
            
        Returns:
            dict: Ответ клиенту или None, если ответ не требуется
        """
        try:
            message_type = message.get('type')
            
            if message_type == 'client_info':
                # Клиент прислал информацию о себе
                pc_name = message.get('pc_name', 'Неизвестный ПК')
                self.client_info[client_id] = {'pc_name': pc_name}
                self.log_message.emit(f"Получена информация о клиенте {client_id}: {pc_name}")
                return None
                
            elif message_type == 'adapters_list':
                # Клиент прислал список адаптеров
                adapters = message.get('adapters', [])
                self.adapters_list_received.emit(client_id, adapters)
                return None
                
            elif message_type == 'adapter_info':
                # Клиент прислал информацию об адаптере
                adapter = message.get('adapter', '')
                info = message.get('info', {})
                self.adapter_info_received.emit(client_id, adapter, info)
                return None
                
            elif message_type == 'speeds_data':
                # Клиент прислал данные о скорости
                adapter = message.get('adapter', '')
                data = message.get('data', {})
                self.speeds_data_received.emit(client_id, adapter, data)
                return None
                
            else:
                # Неизвестный тип сообщения
                self.log_message.emit(f"Неизвестный тип сообщения от клиента {client_id}: {message_type}")
                return None
                
        except Exception as e:
            self.log_message.emit(f"Ошибка при обработке сообщения от клиента {client_id}: {e}")
            return None
            
    def get_client_name(self, client_id):
        """Получение имени ПК клиента
        
        Args:
            client_id: Идентификатор клиента
            
        Returns:
            str: Имя ПК клиента или "Неизвестный ПК"
        """
        if client_id in self.client_info:
            return self.client_info[client_id].get('pc_name', 'Неизвестный ПК')
        return 'Неизвестный ПК' 