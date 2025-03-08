import socket
import json
from typing import Optional, Dict, Any

class NetworkClient:
    def __init__(self, host: str, port: int = 5000):
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.connected = False

    def connect(self) -> bool:
        """Подключается к серверу"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            return True
        except Exception as e:
            print(f"Ошибка подключения к серверу: {e}")
            return False

    def disconnect(self):
        """Отключается от сервера"""
        if self.socket:
            self.socket.close()
            self.socket = None
            self.connected = False

    def _send_command(self, command: dict) -> Optional[dict]:
        """Отправляет команду серверу и получает ответ"""
        if not self.connected:
            print("Не подключено к серверу")
            return None

        try:
            # Отправляем команду
            self.socket.send(json.dumps(command).encode('utf-8'))
            
            # Получаем ответ
            response = self.socket.recv(1024).decode('utf-8')
            if not response:
                return None
                
            return json.loads(response)
        except Exception as e:
            print(f"Ошибка при отправке команды: {e}")
            return None

    def get_adapters(self) -> Optional[list]:
        """Получает список сетевых адаптеров"""
        response = self._send_command({'type': 'get_adapters'})
        if response and response.get('type') == 'adapters_list':
            return response.get('adapters', [])
        return None

    def get_adapter_info(self, adapter_name: str) -> Optional[dict]:
        """Получает информацию об адаптере"""
        response = self._send_command({
            'type': 'get_adapter_info',
            'adapter': adapter_name
        })
        if response and response.get('type') == 'adapter_info':
            return response.get('info')
        return None

    def start_measurement(self, adapter_name: str) -> bool:
        """Начинает измерение скорости"""
        response = self._send_command({
            'type': 'start_measurement',
            'adapter': adapter_name
        })
        return response and response.get('type') == 'measurement_started'

    def stop_measurement(self) -> bool:
        """Останавливает измерение скорости"""
        response = self._send_command({'type': 'stop_measurement'})
        return response and response.get('type') == 'measurement_stopped'

    def get_speeds(self) -> Optional[dict]:
        """Получает текущие значения скорости"""
        response = self._send_command({'type': 'get_speeds'})
        if response and response.get('type') == 'speeds_data':
            return response.get('data')
        return None 