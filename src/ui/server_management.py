from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QListWidgetItem
from src.core.network_server import NetworkServer

class ServerManagement:
    """Класс для управления серверной частью приложения"""
    
    def __init__(self, window):
        """
        Инициализация менеджера сервера
        
        Args:
            window: Главное окно приложения
        """
        self.window = window
        self.server = NetworkServer()
        
        # Настройка сигналов сервера
        self.server.client_connected.connect(self.on_client_connected)
        self.server.client_disconnected.connect(self.on_client_disconnected)
        self.server.server_started.connect(self.on_server_started)
        self.server.server_stopped.connect(self.on_server_stopped)
        self.server.log_message.connect(self.on_log_message)
        
        # Настройка интерфейса
        self.setup_ui()
        
        # Таймер для обновления статуса
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)  # Обновление каждые 5 секунд
        
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Подключаем кнопку запуска сервера
        if hasattr(self.window, "startServerButton"):
            self.window.startServerButton.clicked.connect(self.toggle_server)
            
        # Устанавливаем порт по умолчанию
        if hasattr(self.window, "serverPortInput"):
            self.window.serverPortInput.setText("5000")
            
        # Очищаем список клиентов
        if hasattr(self.window, "clientsListWidget"):
            self.window.clientsListWidget.clear()
            
        # Инициализируем лог сервера
        if hasattr(self.window, "serverLogWidget"):
            self.window.serverLogWidget.clear()
            self.window.serverLogWidget.setReadOnly(True)
            
        # Устанавливаем статус сервера
        if hasattr(self.window, "serverStatusLabel"):
            self.window.serverStatusLabel.setText("Сервер не запущен")
            
    def toggle_server(self):
        """Запуск или остановка сервера"""
        # Проверяем, запущен ли уже сервер
        if self.server.is_running:
            # Останавливаем сервер
            self.server.stop_server()
            return
            
        # Получаем порт из поля ввода
        port = 5000
        if hasattr(self.window, "serverPortInput"):
            try:
                port = int(self.window.serverPortInput.text())
            except ValueError:
                self.log_message("Некорректный порт. Используется порт 5000.")
                port = 5000
        
        # Очищаем лог перед запуском
        if hasattr(self.window, "serverLogWidget"):
            self.window.serverLogWidget.clear()
                
        # Запускаем сервер
        self.server.start_server(port)
        
    def update_status(self):
        """Обновление статуса сервера"""
        if not self.server.is_running:
            return
            
        # Обновляем статус сервера
        if hasattr(self.window, "serverStatusLabel"):
            clients_count = self.server.get_clients_count()
            self.window.serverStatusLabel.setText(f"Сервер запущен. Клиентов: {clients_count}")
            
    def on_client_connected(self, ip, port):
        """Обработчик подключения клиента"""
        # Добавляем клиента в список
        if hasattr(self.window, "clientsListWidget"):
            item = QListWidgetItem(f"{ip}:{port}")
            item.setData(256, (ip, port))  # Qt.UserRole = 256
            self.window.clientsListWidget.addItem(item)
            
    def on_client_disconnected(self, ip, port):
        """Обработчик отключения клиента"""
        # Удаляем клиента из списка
        if hasattr(self.window, "clientsListWidget"):
            for i in range(self.window.clientsListWidget.count()):
                item = self.window.clientsListWidget.item(i)
                if item.data(256) == (ip, port):
                    self.window.clientsListWidget.takeItem(i)
                    break
                    
    def on_server_started(self, port):
        """Обработчик запуска сервера"""
        # Обновляем интерфейс
        if hasattr(self.window, "startServerButton"):
            self.window.startServerButton.setText("Остановить")
            
        if hasattr(self.window, "serverStatusLabel"):
            self.window.serverStatusLabel.setText(f"Сервер запущен на порту {port}")
            
        # Выводим сообщение в лог
        self.log_message(f"Сервер запущен на порту {port}")
        
    def on_server_stopped(self):
        """Обработчик остановки сервера"""
        # Обновляем интерфейс
        if hasattr(self.window, "startServerButton"):
            self.window.startServerButton.setText("Запустить")
            
        if hasattr(self.window, "serverStatusLabel"):
            self.window.serverStatusLabel.setText("Сервер не запущен")
            
        # Очищаем список клиентов
        if hasattr(self.window, "clientsListWidget"):
            self.window.clientsListWidget.clear()
            
        # Выводим сообщение в лог
        self.log_message("Сервер остановлен")
        
    def on_log_message(self, message):
        """Обработчик сообщений лога"""
        self.log_message(message)
        
    def log_message(self, message):
        """Добавление сообщения в лог"""
        if hasattr(self.window, "serverLogWidget"):
            # Добавляем временную метку
            import time
            timestamp = time.strftime("[%H:%M:%S] ")
            
            # Проверяем тип виджета и используем соответствующий метод
            from PyQt6.QtWidgets import QTextEdit, QPlainTextEdit, QLineEdit
            from PyQt6.QtGui import QTextCursor
            
            widget = self.window.serverLogWidget
            if isinstance(widget, (QTextEdit, QPlainTextEdit)):
                # Для многострочных виджетов используем append
                widget.append(f"{timestamp}{message}")
                # Прокручиваем до последнего сообщения
                widget.moveCursor(QTextCursor.MoveOperation.End)
            elif isinstance(widget, QLineEdit):
                # Для однострочных виджетов просто устанавливаем текст
                widget.setText(f"{timestamp}{message}")
            else:
                # Для других типов виджетов пишем в консоль
                print(f"{timestamp}{message}")
            
    def get_server_instance(self):
        """Получение экземпляра сервера"""
        return self.server 