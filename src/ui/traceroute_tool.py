import subprocess
import platform
from PyQt6.QtCore import QObject, QThread, pyqtSignal, QProcess

class TracerouteWorker(QObject):
    """Рабочий объект для выполнения трассировки в отдельном потоке"""
    resultReady = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, address):
        super().__init__()
        self.address = address
        self.process = None
        
    def run(self):
        """Выполнение команды трассировки"""
        try:
            # Определяем команду в зависимости от ОС
            command = 'tracert' if platform.system().lower() == 'windows' else 'traceroute'
            
            # Создаем процесс
            self.process = QProcess()
            
            # Подключаем обработчики событий
            self.process.readyReadStandardOutput.connect(self.handle_output)
            self.process.readyReadStandardError.connect(self.handle_error)
            self.process.finished.connect(self.process_finished)
            
            # Запускаем процесс
            if platform.system().lower() == 'windows':
                self.process.start(command, [self.address])
            else:
                self.process.start(command, ["-m", "30", self.address])  # Для Linux/Mac добавляем максимальное число хопов
            
            # Сообщаем о начале трассировки
            self.resultReady.emit(f"Запуск трассировки маршрута до {self.address}...")
            
        except Exception as e:
            self.resultReady.emit(f"Ошибка при запуске: {str(e)}")
            self.finished.emit()
    
    def handle_output(self):
        """Обработка вывода процесса"""
        output = self.process.readAllStandardOutput().data().decode('cp866' if platform.system().lower() == 'windows' else 'utf-8')
        self.resultReady.emit(output)
        
    def handle_error(self):
        """Обработка ошибок процесса"""
        error = self.process.readAllStandardError().data().decode('cp866' if platform.system().lower() == 'windows' else 'utf-8')
        self.resultReady.emit(f"Ошибка: {error}")
    
    def process_finished(self):
        """Обработка завершения процесса"""
        self.resultReady.emit("Трассировка завершена")
        self.finished.emit()
        
    def stop(self):
        """Остановка процесса"""
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()

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