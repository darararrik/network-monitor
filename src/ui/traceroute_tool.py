from PyQt6.QtCore import QThread
from PyQt6.QtWidgets import QLineEdit
from src.core.traceroute_worker import TracerouteWorker

class TracerouteTool:
    """Класс управления инструментом трассировки маршрутов"""
    
    def __init__(self, window):
        """
        Инициализация инструмента трассировки
        
        Args:
            window: Главное окно приложения
        """
        self.window = window
        self.traceroute_worker = None
        self.traceroute_thread = None
        
        # Настройка интерфейса
        self.setup_ui()
        
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Подключаем кнопку трассировки
        if hasattr(self.window, "executeTracerouteButton"):
            self.window.executeTracerouteButton.clicked.connect(self.execute_traceroute)
            
        # Устанавливаем начальное значение в поле ввода
        if hasattr(self.window, "tracerouteAddressInput"):
            self.window.tracerouteAddressInput.setText("8.8.8.8")
            
        # Очищаем список вывода
        if hasattr(self.window, "tracerouteOutputList"):
            self.window.tracerouteOutputList.clear()
            
        # Флаг запущенной трассировки
        self.is_tracing = False
            
    def execute_traceroute(self):
        """Выполнение команды трассировки или её остановка"""
        # Если трассировка уже запущена, останавливаем её
        if self.is_tracing:
            self.stop_traceroute()
            # Меняем текст кнопки обратно на "Трассировка"
            if hasattr(self.window, "executeTracerouteButton"):
                self.window.executeTracerouteButton.setText("Трассировка")
            self.is_tracing = False
            return
        
        # Получаем адрес из поля ввода
        address = self.window.tracerouteAddressInput.text() if hasattr(self.window, "tracerouteAddressInput") else "8.8.8.8"
        
        # Очищаем предыдущий вывод
        if hasattr(self.window, "tracerouteOutputList"):
            self.window.tracerouteOutputList.clear()
            
        # Создаем и запускаем рабочий объект в отдельном потоке
        self.traceroute_worker = TracerouteWorker(address)
        self.traceroute_thread = QThread()
        self.traceroute_worker.moveToThread(self.traceroute_thread)
        
        # Подключаем сигналы
        self.traceroute_thread.started.connect(self.traceroute_worker.run)
        self.traceroute_worker.resultReady.connect(self.update_output)
        self.traceroute_worker.finished.connect(self.on_traceroute_finished)
        self.traceroute_worker.finished.connect(self.traceroute_thread.quit)
        self.traceroute_worker.finished.connect(self.traceroute_worker.deleteLater)
        self.traceroute_thread.finished.connect(self.traceroute_thread.deleteLater)
        
        # Запускаем поток
        self.traceroute_thread.start()
        
        # Меняем текст кнопки на "Стоп"
        if hasattr(self.window, "executeTracerouteButton"):
            self.window.executeTracerouteButton.setText("Стоп")
            
        # Устанавливаем флаг запущенной трассировки
        self.is_tracing = True
        
    def on_traceroute_finished(self):
        """Обработчик завершения трассировки"""
        # Меняем текст кнопки обратно на "Трассировка"
        if hasattr(self.window, "executeTracerouteButton"):
            self.window.executeTracerouteButton.setText("Трассировка")
        self.is_tracing = False
        
    def update_output(self, output):
        """Обновление вывода в списке"""
        if hasattr(self.window, "tracerouteOutputList"):
            # Разделяем вывод на строки и добавляем каждую в список
            lines = output.strip().split('\n')
            for line in lines:
                if line.strip():
                    self.window.tracerouteOutputList.addItem(line.strip())
                    # Прокручиваем к последнему элементу
                    self.window.tracerouteOutputList.scrollToBottom()
                    
    def stop_traceroute(self):
        """Остановка выполнения трассировки"""
        if self.traceroute_worker:
            self.traceroute_worker.stop() 