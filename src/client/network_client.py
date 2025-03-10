import socket
import json
import threading
import time
import platform
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QTableWidgetItem
from ..core.network_monitor import NetworkMonitor

class NetworkClient(QObject):
    """Класс для взаимодействия клиента с сервером"""
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    error = pyqtSignal(str)
    log_message = pyqtSignal(str)
    adapter_info_received = pyqtSignal(dict)
    speeds_received = pyqtSignal(dict)
    adapters_list_received = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.socket = None
        self.is_connected = False
        self.receive_thread = None
        self.network_monitor = NetworkMonitor()
        self.current_monitored_adapter = None
        self.monitoring_thread = None
        self.is_monitoring = False
        self.pc_name = self.get_pc_name()
        
    def get_pc_name(self):
        """Получение имени компьютера"""
        try:
            return platform.node()
        except:
            return "Неизвестный ПК"
        
    def connect_to_server(self, ip, port):
        """Подключение к серверу
        
        Args:
            ip: IP-адрес сервера
            port: Порт сервера
            
        Returns:
            bool: True если подключение успешно, иначе False
        """
        try:
            self.log_message.emit(f"Подключаемся к серверу {ip}:{port}...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((ip, port))
            self.is_connected = True
            
            # Устанавливаем таймаут для сокета
            self.socket.settimeout(5.0)
            self.log_message.emit("Соединение установлено успешно!")
            
            # Отправляем информацию о клиенте
            self.log_message.emit("Отправляем информацию о клиенте...")
            self._send_client_info()
            
            # Запускаем поток для приема данных
            self.log_message.emit("Запускаем поток приема данных...")
            self.receive_thread = threading.Thread(target=self._receive_data)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            self.connected.emit()
            self.log_message.emit(f"Подключено к серверу {ip}:{port}")
            return True
        except Exception as e:
            self.error.emit(f"Ошибка подключения: {str(e)}")
            self.log_message.emit(f"Критическая ошибка при подключении: {str(e)}")
            self.is_connected = False
            return False
            
    def disconnect(self):
        """Отключение от сервера"""
        if not self.is_connected:
            return
            
        try:
            # Останавливаем мониторинг, если запущен
            if self.is_monitoring:
                self.stop_monitoring()
                
            # Закрываем сокет
            if self.socket:
                self.socket.close()
                
            self.is_connected = False
            self.disconnected.emit()
            self.log_message.emit("Отключено от сервера")
        except Exception as e:
            self.error.emit(f"Ошибка при отключении: {str(e)}")
            
    def _receive_data(self):
        """Поток для приема данных от сервера"""
        self.log_message.emit("Запущен поток приема данных от сервера")
        while self.is_connected:
            try:
                self.log_message.emit("Ожидаем данные от сервера...")
                data = self.socket.recv(4096)
                if not data:
                    # Сервер отключился
                    self.is_connected = False
                    self.disconnected.emit()
                    self.log_message.emit("Сервер разорвал соединение")
                    break
                
                self.log_message.emit(f"Получены данные от сервера: {len(data)} байт")
                # Обрабатываем полученные данные
                self._process_server_request(data)
            except socket.timeout:
                self.log_message.emit("Таймаут ожидания данных от сервера")
                continue
            except Exception as e:
                # Проверяем, не закрыт ли уже сокет
                if not self.is_connected:
                    break
                
                self.error.emit(f"Ошибка при получении данных: {str(e)}")
                self.log_message.emit(f"Критическая ошибка в потоке приема: {str(e)}")
                self.is_connected = False
                self.disconnected.emit()
                break
        
        self.log_message.emit("Поток приема данных завершен")

    def _process_server_request(self, data):
        """Обработка запроса от сервера
        
        Args:
            data: Полученные данные
        """
        try:
            # Декодируем данные
            self.log_message.emit(f"Декодируем полученные данные: {data[:100]}...")
            message = json.loads(data.decode('utf-8'))
            self.log_message.emit(f"Получено сообщение от сервера: {message}")
            
            # Обрабатываем различные типы сообщений
            if 'type' in message:
                message_type = message['type']
                self.log_message.emit(f"Тип сообщения: {message_type}")
                
                if message_type == 'get_adapters':
                    # Запрос на получение списка адаптеров
                    self.log_message.emit("ПОЛУЧЕН ЗАПРОС НА СПИСОК АДАПТЕРОВ")
                    self._send_adapters_list()
                    
                elif message_type == 'get_adapter_info':
                    # Запрос на получение информации об адаптере
                    adapter_name = message.get('adapter')
                    if adapter_name:
                        self.log_message.emit(f"ПОЛУЧЕН ЗАПРОС НА ИНФОРМАЦИЮ ОБ АДАПТЕРЕ: {adapter_name}")
                        self._send_adapter_info(adapter_name)
                    else:
                        self.error.emit("Получен запрос без имени адаптера")
                        
                elif message_type == 'start_monitoring':
                    # Запрос на начало мониторинга
                    adapter_name = message.get('adapter')
                    if adapter_name:
                        self.log_message.emit(f"ПОЛУЧЕН ЗАПРОС НА НАЧАЛО МОНИТОРИНГА АДАПТЕРА: {adapter_name}")
                        self.start_monitoring(adapter_name)
                    else:
                        self.error.emit("Получен запрос на мониторинг без имени адаптера")
                        
                elif message_type == 'stop_monitoring':
                    # Запрос на остановку мониторинга
                    self.log_message.emit("ПОЛУЧЕН ЗАПРОС НА ОСТАНОВКУ МОНИТОРИНГА")
                    self.stop_monitoring()
                    
                elif message_type == 'error':
                    # Сообщение об ошибке от сервера
                    error_msg = message.get('message', 'Неизвестная ошибка сервера')
                    self.error.emit(f"Ошибка от сервера: {error_msg}")
                    
                else:
                    # Неизвестный тип сообщения
                    self.log_message.emit(f"Получено неизвестное сообщение: {message_type}")
                    
            else:
                # Сообщение без типа
                self.log_message.emit(f"Получено сообщение без типа: {message}")
                
        except json.JSONDecodeError as e:
            self.error.emit(f"Получены некорректные данные от сервера: {str(e)}")
            self.log_message.emit(f"Ошибка декодирования JSON: {str(e)}, данные: {data[:100]}...")
        except Exception as e:
            self.error.emit(f"Ошибка обработки данных от сервера: {str(e)}")
            self.log_message.emit(f"Критическая ошибка при обработке данных: {str(e)}")
            
    def _send_message(self, message):
        """Отправка сообщения серверу
        
        Args:
            message: Сообщение для отправки
            
        Returns:
            bool: True если отправка успешна, иначе False
        """
        if not self.is_connected:
            self.log_message.emit("Не удалось отправить сообщение: нет подключения к серверу")
            return False
            
        try:
            self.log_message.emit(f"Отправляем сообщение серверу: {message}")
            data = json.dumps(message).encode('utf-8')
            self.socket.sendall(data)
            self.log_message.emit(f"Сообщение успешно отправлено ({len(data)} байт)")
            return True
        except Exception as e:
            self.error.emit(f"Ошибка отправки сообщения: {str(e)}")
            self.log_message.emit(f"Ошибка при отправке данных: {str(e)}")
            return False
            
    def _send_adapters_list(self):
        """Отправка списка адаптеров серверу"""
        adapters = self.network_monitor.get_adapters()
        self.log_message.emit(f"Отправляем список адаптеров: {adapters}")
        message = {
            'type': 'adapters_list',
            'adapters': adapters
        }
        self._send_message(message)
        self.adapters_list_received.emit(adapters)
        self.log_message.emit(f"Отправлен список адаптеров: {adapters}")
        
    def _send_adapter_info(self, adapter_name):
        """Отправка информации об адаптере серверу
        
        Args:
            adapter_name: Имя адаптера
        """
        info = self.network_monitor.get_adapter_info(adapter_name)
        self.log_message.emit(f"Отправляем информацию об адаптере {adapter_name}: {info}")
        message = {
            'type': 'adapter_info',
            'adapter': adapter_name,
            'info': info
        }
        self._send_message(message)
        self.adapter_info_received.emit(info)
        self.log_message.emit(f"Отправлена информация об адаптере {adapter_name}")
        
    def start_monitoring(self, adapter_name):
        """Запуск мониторинга скорости адаптера
        
        Args:
            adapter_name: Имя адаптера для мониторинга
        """
        if self.is_monitoring:
            self.stop_monitoring()
            
        try:
            # Запоминаем текущий адаптер
            self.current_monitored_adapter = adapter_name
            
            # Устанавливаем адаптер в NetworkMonitor
            self.network_monitor.selected_adapter = adapter_name
            self.network_monitor.start_measurement(adapter_name)
            
            # Запускаем мониторинг
            self.is_monitoring = True
            
            # Запускаем поток мониторинга
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
            
            self.log_message.emit(f"Запущен мониторинг адаптера {adapter_name}")
        except Exception as e:
            self.error.emit(f"Ошибка запуска мониторинга: {str(e)}")
            self.log_message.emit(f"Не удалось запустить мониторинг: {str(e)}")
            self.is_monitoring = False
            
    def stop_monitoring(self):
        """Остановка мониторинга скорости"""
        if not self.is_monitoring:
            return
            
        self.is_monitoring = False
        self.current_monitored_adapter = None
        
        # Ждем завершения потока
        if self.monitoring_thread:
            try:
                self.monitoring_thread.join(1.0)
            except:
                pass
                
        self.log_message.emit("Мониторинг остановлен")
        
    def _monitoring_loop(self):
        """Цикл мониторинга и отправки данных серверу"""
        while self.is_monitoring and self.is_connected:
            try:
                # Получаем текущие скорости
                speeds = self.network_monitor.get_current_speeds()
                
                if speeds:
                    # Отправляем данные серверу
                    message = {
                        'type': 'speeds_data',
                        'adapter': self.current_monitored_adapter,
                        'data': speeds
                    }
                    self._send_message(message)
                    self.speeds_received.emit(speeds)
                    
            except Exception as e:
                self.error.emit(f"Ошибка мониторинга: {str(e)}")
                
            # Пауза между измерениями
            time.sleep(1)
            
    def get_adapters_list(self):
        """Получение списка адаптеров
        
        Returns:
            list: Список адаптеров
        """
        return self.network_monitor.get_adapters()
        
    def get_adapter_info(self, adapter_name):
        """Получение информации об адаптере
        
        Args:
            adapter_name: Имя адаптера
            
        Returns:
            dict: Информация об адаптере
        """
        return self.network_monitor.get_adapter_info(adapter_name)

    def _send_client_info(self):
        """Отправка информации о клиенте серверу"""
        message = {
            'type': 'client_info',
            'pc_name': self.pc_name
        }
        self._send_message(message)
        self.log_message.emit(f"Отправлена информация о клиенте: {self.pc_name}") 