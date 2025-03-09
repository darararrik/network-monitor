import socket
import ipaddress
import platform
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from PyQt6.QtCore import QObject, QThread, pyqtSignal

class NetworkScanner(QObject):
    """Класс для сканирования сети и поиска доступных хостов"""
    host_found = pyqtSignal(str, str)  # IP, имя_хоста
    scan_progress = pyqtSignal(int, int)  # текущий, всего
    scan_complete = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.is_scanning = False
        self.should_stop = False
        self.progress_lock = threading.Lock()
        self.current_progress = 0
        self.max_workers = 50  # Максимальное количество одновременных потоков
        
    def get_network_prefix(self):
        """Определение текущего сетевого префикса"""
        try:
            # Получаем IP-адрес текущего компьютера
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            # Берем первые три октета для сканирования сети класса C
            prefix = '.'.join(local_ip.split('.')[:3])
            return prefix
        except:
            # Если не удалось определить, используем локальную сеть по умолчанию
            return "192.168.1"
    
    def scan_network(self, prefix=None, start=1, end=254):
        """
        Сканирование сети на наличие активных хостов
        
        Args:
            prefix: Сетевой префикс (например, 192.168.1)
            start: Начальный адрес для сканирования
            end: Конечный адрес для сканирования
        """
        if self.is_scanning:
            return
            
        self.is_scanning = True
        self.should_stop = False
        self.current_progress = 0
        
        # Если префикс не указан, определяем автоматически
        if not prefix:
            prefix = self.get_network_prefix()
            
        total_hosts = end - start + 1
        
        # Создаем список IP-адресов для сканирования
        ips_to_scan = [f"{prefix}.{i}" for i in range(start, end + 1)]
        
        # Запускаем параллельное сканирование
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Проверяем IP-адреса параллельно
            for ip in ips_to_scan:
                if self.should_stop:
                    break
                # Отправляем задачу в пул потоков
                executor.submit(self._check_host_thread, ip, total_hosts)
        
        # Сканирование завершено
        self.is_scanning = False
        self.scan_complete.emit()
    
    def _check_host_thread(self, ip, total_hosts):
        """Проверка хоста в отдельном потоке"""
        # Проверяем хост
        is_alive, hostname = self.check_host(ip)
        
        # Если хост доступен, сообщаем об этом
        if is_alive:
            self.host_found.emit(ip, hostname)
        
        # Обновляем прогресс
        with self.progress_lock:
            self.current_progress += 1
            self.scan_progress.emit(self.current_progress, total_hosts)
    
    def stop_scan(self):
        """Остановка процесса сканирования"""
        self.should_stop = True
    
    def check_host(self, ip):
        """
        Проверка доступности хоста и получение его имени
        
        Args:
            ip: IP-адрес для проверки
            
        Returns:
            tuple: (is_alive, hostname)
        """
        # Проверяем доступность хоста с помощью пинга
        is_alive = self.ping_host(ip)
        
        if is_alive:
            # Пытаемся получить имя хоста
            try:
                hostname = socket.getfqdn(ip)
                if hostname == ip:  # Если не удалось получить имя, используем IP
                    hostname = "Неизвестный хост"
            except:
                hostname = "Неизвестный хост"
        else:
            hostname = ""
            
        return is_alive, hostname
    
    def ping_host(self, ip):
        """
        Проверка доступности хоста с помощью пинга
        
        Args:
            ip: IP-адрес для проверки
            
        Returns:
            bool: True, если хост доступен
        """
        try:
            # Определяем команду пинга в зависимости от ОС
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            count_param = '1'
            timeout_param = '-w' if platform.system().lower() == 'windows' else '-W'
            timeout_value = '200'  # уменьшаем таймаут до 200 мс для Windows, 0.2 сек для Linux
            
            args = ['ping', param, count_param, timeout_param, timeout_value, ip]
            
            # Выполняем пинг и перенаправляем вывод в никуда
            with open('NUL' if platform.system().lower() == 'windows' else '/dev/null', 'w') as devnull:
                return subprocess.call(args, stdout=devnull, stderr=devnull) == 0
        except:
            return False

class NetworkScannerWorker(QObject):
    """Рабочий объект для выполнения сканирования сети в отдельном потоке"""
    finished = pyqtSignal()
    
    def __init__(self, scanner, prefix=None, start=1, end=254):
        super().__init__()
        self.scanner = scanner
        self.prefix = prefix
        self.start = start
        self.end = end
    
    def run(self):
        """Запуск сканирования сети"""
        self.scanner.scan_network(self.prefix, self.start, self.end)
        self.finished.emit() 