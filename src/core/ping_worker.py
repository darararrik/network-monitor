import subprocess
import platform
from PyQt6.QtCore import QObject, QThread, pyqtSignal, QProcess

class PingWorker(QObject):
    """Рабочий объект для выполнения пинга в отдельном потоке"""
    resultReady = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, address, count=10):
        super().__init__()
        self.address = address
        self.count = count
        self.process = None
        
    def run(self):
        """Выполнение команды ping"""
        try:
            # Определяем параметры в зависимости от ОС
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            
            # Создаем процесс
            self.process = QProcess()
            
            # Подключаем обработчики событий
            self.process.readyReadStandardOutput.connect(self.handle_output)
            self.process.readyReadStandardError.connect(self.handle_error)
            self.process.finished.connect(self.process_finished)
            
            # Запускаем процесс
            self.process.start('ping', [param, str(self.count), self.address])
            
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
        self.resultReady.emit("Выполнение завершено")
        self.finished.emit()
        
    def stop(self):
        """Остановка процесса"""
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill() 