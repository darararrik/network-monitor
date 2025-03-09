from PyQt6.QtCore import QThread
from PyQt6.QtWidgets import QListWidgetItem, QProgressBar, QInputDialog, QMessageBox
from src.core.network_scanner import NetworkScanner, NetworkScannerWorker

class NetworkDiscovery:
    """Класс для поиска и отображения доступных хостов в сети"""
    
    def __init__(self, window):
        """
        Инициализация инструмента поиска сети
        
        Args:
            window: Главное окно приложения
        """
        self.window = window
        self.scanner = NetworkScanner()
        self.scanner_worker = None
        self.scanner_thread = None
        self.progress_bar = None
        
        # Настройка сигналов сканера
        self.scanner.host_found.connect(self.on_host_found)
        self.scanner.scan_progress.connect(self.on_scan_progress)
        self.scanner.scan_complete.connect(self.on_scan_complete)
        
        # Настройка интерфейса
        self.setup_ui()
        
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Подключаем кнопку сканирования
        if hasattr(self.window, "scanNetworkButton"):
            self.window.scanNetworkButton.clicked.connect(self.toggle_scan)
            
        # Подключаем кнопку настройки диапазона (если есть)
        if hasattr(self.window, "scanRangeButton"):
            self.window.scanRangeButton.clicked.connect(self.set_scan_range)
            
        # Очищаем список хостов
        if hasattr(self.window, "availableHostsList"):
            self.window.availableHostsList.clear()
            
        # Подключаем обработчик выбора хоста
        if hasattr(self.window, "availableHostsList"):
            self.window.availableHostsList.itemDoubleClicked.connect(self.on_host_selected)
            
        # Создаем прогресс-бар для отображения прогресса сканирования
        if hasattr(self.window, "scanProgressBar"):
            self.progress_bar = self.window.scanProgressBar
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(False)
            
        # Флаг сканирования
        self.is_scanning = False
        
        # Диапазон сканирования по умолчанию
        self.scan_prefix = None  # Автоопределение
        self.scan_start = 1
        self.scan_end = 254
        
    def set_scan_range(self):
        """Установка диапазона сканирования"""
        # Определяем текущий префикс сети
        current_prefix = self.scanner.get_network_prefix()
        
        # Запрашиваем у пользователя диапазон для сканирования
        prefix, ok = QInputDialog.getText(
            self.window, 
            "Диапазон сканирования", 
            "Введите сетевой префикс (например, 192.168.1):",
            text=current_prefix
        )
        
        if not ok:
            return
            
        # Запрашиваем начальный адрес
        start, ok = QInputDialog.getInt(
            self.window,
            "Диапазон сканирования",
            "Введите начальный адрес (1-254):",
            value=1, min=1, max=254
        )
        
        if not ok:
            return
            
        # Запрашиваем конечный адрес
        end, ok = QInputDialog.getInt(
            self.window,
            "Диапазон сканирования",
            "Введите конечный адрес (1-254):",
            value=254, min=start, max=254
        )
        
        if not ok:
            return
            
        # Устанавливаем новый диапазон
        self.scan_prefix = prefix
        self.scan_start = start
        self.scan_end = end
        
        # Выводим информацию о новом диапазоне
        QMessageBox.information(
            self.window,
            "Диапазон сканирования",
            f"Установлен диапазон сканирования: {prefix}.{start} - {prefix}.{end}"
        )
        
    def toggle_scan(self):
        """Запуск или остановка сканирования сети"""
        if self.is_scanning:
            self.stop_scan()
            # Меняем текст кнопки
            if hasattr(self.window, "scanNetworkButton"):
                self.window.scanNetworkButton.setText("Сканировать")
            self.is_scanning = False
            return
            
        # Очищаем предыдущие результаты
        if hasattr(self.window, "availableHostsList"):
            self.window.availableHostsList.clear()
            
        # Показываем прогресс-бар
        if self.progress_bar:
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(True)
            
        # Создаем и запускаем рабочий объект в отдельном потоке
        self.scanner_worker = NetworkScannerWorker(
            self.scanner, 
            self.scan_prefix, 
            self.scan_start, 
            self.scan_end
        )
        self.scanner_thread = QThread()
        self.scanner_worker.moveToThread(self.scanner_thread)
        
        # Подключаем сигналы
        self.scanner_thread.started.connect(self.scanner_worker.run)
        self.scanner_worker.finished.connect(self.scanner_thread.quit)
        self.scanner_worker.finished.connect(self.scanner_worker.deleteLater)
        self.scanner_thread.finished.connect(self.scanner_thread.deleteLater)
        
        # Запускаем поток
        self.scanner_thread.start()
        
        # Меняем текст кнопки
        if hasattr(self.window, "scanNetworkButton"):
            self.window.scanNetworkButton.setText("Остановить")
            
        # Устанавливаем флаг сканирования
        self.is_scanning = True
        
    def stop_scan(self):
        """Остановка сканирования сети"""
        if self.scanner:
            self.scanner.stop_scan()
        
        # Скрываем прогресс-бар
        if self.progress_bar:
            self.progress_bar.setVisible(False)
            
    def on_host_found(self, ip, hostname):
        """Обработчик обнаружения хоста"""
        if hasattr(self.window, "availableHostsList"):
            # Создаем элемент списка
            text = f"{ip} ({hostname})" if hostname else ip
            item = QListWidgetItem(text)
            # Сохраняем IP адрес как пользовательские данные
            item.setData(256, ip)  # Qt.UserRole = 256
            # Добавляем элемент в список
            self.window.availableHostsList.addItem(item)
            
    def on_scan_progress(self, current, total):
        """Обработчик обновления прогресса сканирования"""
        if self.progress_bar:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
            
    def on_scan_complete(self):
        """Обработчик завершения сканирования"""
        # Меняем текст кнопки
        if hasattr(self.window, "scanNetworkButton"):
            self.window.scanNetworkButton.setText("Сканировать")
            
        # Скрываем прогресс-бар
        if self.progress_bar:
            self.progress_bar.setVisible(False)
            
        # Сбрасываем флаг сканирования
        self.is_scanning = False
        
        # Показываем сообщение с результатами, если список не пуст
        if hasattr(self.window, "availableHostsList") and self.window.availableHostsList.count() > 0:
            QMessageBox.information(
                self.window,
                "Сканирование завершено",
                f"Найдено {self.window.availableHostsList.count()} активных хостов в сети"
            )
        
    def on_host_selected(self, item):
        """Обработчик выбора хоста из списка"""
        # Получаем IP адрес из данных элемента
        ip = item.data(256)  # Qt.UserRole = 256
        
        # Устанавливаем IP в поле подключения
        if hasattr(self.window, "remoteIPInput"):
            self.window.remoteIPInput.setText(ip) 