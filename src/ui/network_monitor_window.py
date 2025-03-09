import os
import sys
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QTabWidget
from PyQt6 import uic

from src.core.network_monitor import NetworkMonitor
from src.core.graph_builder import GraphBuilder
from src.ui.adapter_management import AdapterManagement
from src.ui.measurement_management import MeasurementManagement
from src.ui.remote.monitoring import RemoteMonitoring
from src.ui.ping_tool import PingTool
from src.ui.traceroute_tool import TracerouteTool
from src.ui.network_discovery import NetworkDiscovery

class NetworkMonitorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        ui_file = os.path.join(os.path.dirname(__file__), "network_monitor.ui")
        uic.loadUi(ui_file, self)

        self.network_monitor = NetworkMonitor()
        self.adapter_management = AdapterManagement(self, self.network_monitor)
        self.adapter_management.setup_table()
        self.adapter_management.load_adapters()
        self.measurement_management = MeasurementManagement(self)
        
        self.adapterList.currentTextChanged.connect(self.adapter_management.on_adapter_selected)
        self.setup_ui()
        
        # Инициализация удаленного мониторинга
        self.remote_monitoring = RemoteMonitoring(self, self.network_monitor)
        self.remote_monitoring.setup_remote_monitoring()
        
        # Счетчик удаленных вкладок
        self.remote_tab_count = 1
        self.remote_monitors = {0: self.remote_monitoring}  # Хранение объектов мониторинга
        
        # Подключение кнопки добавления новой вкладки
        if hasattr(self, "addRemoteTabButton"):
            self.addRemoteTabButton.clicked.connect(self.add_remote_tab)
            
        # Инициализация инструмента пинга
        self.ping_tool = PingTool(self)
        
        # Инициализация инструмента трассировки
        self.traceroute_tool = TracerouteTool(self)
        
        # Инициализация инструмента поиска сети
        self.network_discovery = NetworkDiscovery(self)

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
            
        # Отключаемся от удаленного компьютера, если подключены
        if hasattr(self, "remote_monitoring") and self.remote_monitoring.remote_connected:
            self.remote_monitoring.disconnect_from_remote()
        
        event.accept()

    def add_remote_tab(self):
        """Добавление новой вкладки для мониторинга удаленного ПК"""
        try:
            if hasattr(self, "remoteTabsWidget"):
                # Увеличиваем счетчик вкладок
                self.remote_tab_count += 1
                
                # Создаем новую вкладку
                new_tab = QWidget()
                new_tab.setObjectName(f"remoteTab{self.remote_tab_count}")
                
                # Создаем базовый лейаут для вкладки
                layout = QVBoxLayout(new_tab)
                
                # Создаем верхнюю панель
                top_layout = QHBoxLayout()
                
                # Добавляем поля ввода и кнопки
                ip_input = QLineEdit("IP")
                ip_input.setObjectName(f"remoteIPInput{self.remote_tab_count}")
                ip_input.setMinimumWidth(100)
                
                port_input = QLineEdit("5000")
                port_input.setObjectName(f"remotePortInput{self.remote_tab_count}")
                port_input.setMinimumWidth(100)
                
                connect_button = QPushButton("Подключиться")
                connect_button.setObjectName(f"connectRemoteButton{self.remote_tab_count}")
                connect_button.setMinimumWidth(100)
                
                ping_button = QPushButton("Ping")
                ping_button.setObjectName(f"pingRemoteButton{self.remote_tab_count}")
                ping_button.setMinimumWidth(100)
                
                # Добавляем их в лейаут
                top_layout.addWidget(ip_input)
                top_layout.addWidget(port_input)
                top_layout.addWidget(connect_button)
                top_layout.addWidget(ping_button)
                top_layout.addStretch()
                
                # Добавляем статус-лейбл
                status_layout = QHBoxLayout()
                status_label = QLabel("Не подключено")
                status_label.setObjectName(f"remoteComputerLabel{self.remote_tab_count}")
                status_layout.addWidget(status_label)
                status_layout.addStretch()
                
                # Добавляем лейауты на вкладку
                layout.addLayout(top_layout)
                layout.addLayout(status_layout)
                
                # Создаем место под остальной контент (оно будет заполнено при создании объекта RemoteMonitoring)
                content_widget = QWidget()
                content_widget.setObjectName(f"remoteContent{self.remote_tab_count}")
                layout.addWidget(content_widget)
                
                # Добавляем вкладку в TabWidget
                self.remoteTabsWidget.addTab(new_tab, f"ПК {self.remote_tab_count}")
                
                # Создаем и инициализируем новый объект мониторинга для этой вкладки
                new_monitor = RemoteMonitoring(self, self.network_monitor, tab_id=self.remote_tab_count)
                new_monitor.setup_remote_monitoring()
                
                # Хранение объекта мониторинга
                self.remote_monitors[self.remote_tab_count - 1] = new_monitor
                
                # Переключаемся на новую вкладку
                self.remoteTabsWidget.setCurrentIndex(self.remote_tab_count - 1)
                
        except Exception as e:
            print(f"Ошибка при добавлении новой вкладки: {e}")

    