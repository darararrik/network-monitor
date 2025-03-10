import os
import sys
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QTabWidget
from PyQt6 import uic
from src.core.network_monitor import NetworkMonitor
from src.core.graph_builder import GraphBuilder
from src.ui.adapter_management import AdapterManagement
from src.ui.measurement_management import MeasurementManagement
from src.ui.ping_tool import PingTool
from src.ui.traceroute_tool import TracerouteTool
from src.ui.server_management import ServerManagement

class NetworkMonitorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        ui_file = os.path.join(os.path.dirname(__file__), "network_monitor.ui")
        uic.loadUi(ui_file, self)

        self.network_monitor = NetworkMonitor()
        # Инициализация серверной части (должна быть первой, т.к. она управляет удаленным мониторингом)
        self.server_management = ServerManagement(self)
        
        # Инициализация управления локальными адаптерами
        self.adapter_management = AdapterManagement(self, self.network_monitor)
        self.adapter_management.setup_table()
        self.adapter_management.load_adapters()
        
        # Инициализация управления измерениями скорости
        self.measurement_management = MeasurementManagement(self)
        
        self.adapterList.currentTextChanged.connect(self.adapter_management.on_adapter_selected)
        self.setup_ui()
        
        # Инициализация инструмента пинга
        self.ping_tool = PingTool(self)
        
        # Инициализация инструмента трассировки
        self.traceroute_tool = TracerouteTool(self)

    def setup_ui(self):
            """Настройка пользовательского интерфейса"""
            self.measureSpeedButton.setEnabled(False)
            self.measureSpeedButton.clicked.connect(self.measurement_management.toggle_measurement)

            if hasattr(self, "clearGraphs"):
                self.clearGraphs.clicked.connect(self.measurement_management.clear_graphs)
            # Настройка таймера
            self.target_time = 0
            self.hoursInput.setPlaceholderText("Часы")
            self.minutesInput.setPlaceholderText("Мин")
            self.secondsInput.setPlaceholderText("Сек")
            
            self.hoursInput.textChanged.connect(self.measurement_management.on_time_changed)
            self.minutesInput.textChanged.connect(self.measurement_management.on_time_changed)
            self.secondsInput.textChanged.connect(self.measurement_management.on_time_changed)

            # Настраиваем график скорости
            if hasattr(self, "graphWidget"):
                self.graph_builder = GraphBuilder(self.graphWidget)
                
            # Подключаем чекбоксы
            if hasattr(self, "hideDownload"):
                self.hideDownload.stateChanged.connect(self.on_hide_download_changed)
            if hasattr(self, "hideUpload"):
                self.hideUpload.stateChanged.connect(self.on_hide_upload_changed)

            # Подключаем обработчик выбора вкладки
            if hasattr(self, "tabWidget"):
                self.tabWidget.currentChanged.connect(self.on_tab_changed)

            # Подключаем обработчик закрытия окна
            self.closeEvent = self.closeEvent

    def on_hide_download_changed(self, state):
        """Обработчик изменения состояния чекбокса скрытия линии загрузки"""
        if hasattr(self, "graph_builder"):
            self.graph_builder.set_download_visible(not bool(state))

    def on_hide_upload_changed(self, state):
        """Обработчик изменения состояния чекбокса скрытия линии отдачи"""
        if hasattr(self, "graph_builder"):
            self.graph_builder.set_upload_visible(not bool(state))
            
    def on_tab_changed(self, index):
        """Обработчик изменения текущей вкладки"""
        pass

    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        # Останавливаем измерения, если они запущены
        if hasattr(self, "measurement_management"):
            self.measurement_management.stop_measurement()
            
        # Останавливаем сервер, если запущен
        if hasattr(self, "server_management"):
            self.server_management.server.stop_server()
        
        event.accept()

    