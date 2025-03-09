from PyQt6.QtCore import QThread
from PyQt6.QtWidgets import QLineEdit
from src.core.ping_worker import PingWorker

class PingTool:
    """Класс управления инструментом пинга"""
    
    def __init__(self, window):
        """
        Инициализация инструмента пинга
        
        Args:
            window: Главное окно приложения
        """
        self.window = window
        self.ping_worker = None
        self.ping_thread = None
        
        # Настройка интерфейса
        self.setup_ui()
        
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Подключаем кнопку пинга
        if hasattr(self.window, "executePingButton"):
            self.window.executePingButton.clicked.connect(self.execute_ping)
            
        # Устанавливаем начальное значение в поле ввода
        if hasattr(self.window, "pingAddressInput"):
            self.window.pingAddressInput.setText("google.com")
            
        # Очищаем список вывода
        if hasattr(self.window, "pingOutputList"):
            self.window.pingOutputList.clear()
            
        # Флаг запущенного пинга
        self.is_pinging = False
            
    def execute_ping(self):
        """Выполнение команды ping или её остановка"""
        # Если пинг уже запущен, останавливаем его
        if self.is_pinging:
            self.stop_ping()
            # Меняем текст кнопки обратно на "Ping"
            if hasattr(self.window, "executePingButton"):
                self.window.executePingButton.setText("Ping")
            self.is_pinging = False
            return
            
        # Получаем адрес из поля ввода
        address = self.window.pingAddressInput.text() if hasattr(self.window, "pingAddressInput") else "google.com"
        
        # Очищаем предыдущий вывод
        if hasattr(self.window, "pingOutputList"):
            self.window.pingOutputList.clear()
            
        # Создаем и запускаем рабочий объект в отдельном потоке
        self.ping_worker = PingWorker(address)
        self.ping_thread = QThread()
        self.ping_worker.moveToThread(self.ping_thread)
        
        # Подключаем сигналы
        self.ping_thread.started.connect(self.ping_worker.run)
        self.ping_worker.resultReady.connect(self.update_output)
        self.ping_worker.finished.connect(self.on_ping_finished)
        self.ping_worker.finished.connect(self.ping_thread.quit)
        self.ping_worker.finished.connect(self.ping_worker.deleteLater)
        self.ping_thread.finished.connect(self.ping_thread.deleteLater)
        
        # Запускаем поток
        self.ping_thread.start()
        
        # Меняем текст кнопки на "Стоп"
        if hasattr(self.window, "executePingButton"):
            self.window.executePingButton.setText("Стоп")
            
        # Устанавливаем флаг запущенного пинга
        self.is_pinging = True
        
    def on_ping_finished(self):
        """Обработчик завершения пинга"""
        # Меняем текст кнопки обратно на "Ping"
        if hasattr(self.window, "executePingButton"):
            self.window.executePingButton.setText("Ping")
        self.is_pinging = False
        
    def update_output(self, output):
        """Обновление вывода в списке"""
        if hasattr(self.window, "pingOutputList"):
            # Разделяем вывод на строки и добавляем каждую в список
            lines = output.strip().split('\n')
            for line in lines:
                if line.strip():
                    self.window.pingOutputList.addItem(line.strip())
                    # Прокручиваем к последнему элементу
                    self.window.pingOutputList.scrollToBottom()
                    
    def stop_ping(self):
        """Остановка выполнения пинга"""
        if self.ping_worker:
            self.ping_worker.stop() 