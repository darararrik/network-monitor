import os
import sys
from PyQt6.QtWidgets import QMainWindow, QTableWidgetItem, QHeaderView, QMessageBox, QTabWidget
from PyQt6 import uic
from PyQt6.QtCore import QTimer, Qt

from src.core.network_monitor import NetworkMonitor
from src.core.network_client import NetworkClient
from src.core.graph_builder import GraphBuilder
from src.ui.adapter_management import AdapterManagement
from src.ui.measurement_management import MeasurementManagement

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
        # Настройка кнопок
    #self.is_measuring = False
        

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

            if hasattr(self, "graphWidget") and self.graphWidget is not None:
                self.graph_builder = GraphBuilder(self.graphWidget)
            else:
                print("Ошибка: graphWidget не найден в UI!")

            self.hideDownload.stateChanged.connect(self.on_hide_download_changed)
            self.hideUpload.stateChanged.connect(self.on_hide_upload_changed)

            self.remote_client = None
            self.remote_connected = False
            self.setup_remote_monitoring()


    def setup_remote_monitoring(self):
        """Настройка удаленного мониторинга"""
        print("Настройка удаленного мониторинга...")
        
        # Подключаем кнопку подключения
        if hasattr(self, "connectRemoteButton"):
            self.connectRemoteButton.clicked.connect(self.connect_to_remote)
        
        # Устанавливаем значение порта по умолчанию
        if hasattr(self, "remotePortInput"):
            self.remotePortInput.setText("5000")
            
        # Подключаем обработчик выбора адаптера
        if hasattr(self, "remoteAdapterList"):
            self.remoteAdapterList.currentTextChanged.connect(self.on_remote_adapter_selected)
            
        # Настраиваем таблицу для удаленного мониторинга
        if hasattr(self, "remoteInfoTable"):
            self.setup_remote_table()

        # Подключаем кнопку измерения скорости
        if hasattr(self, "remoteMeasureSpeedButton"):
            self.remoteMeasureSpeedButton.clicked.connect(self.toggle_remote_measurement)
            self.remote_is_measuring = False

        # Подключаем кнопку очистки графиков
        if hasattr(self, "remoteClearGraphs"):
            self.remoteClearGraphs.clicked.connect(self.clear_remote_graphs)

        # Инициализируем таймер для удаленных измерений
        self.remote_timer = QTimer()
        self.remote_timer.timeout.connect(self.update_remote_measurements)

        # Инициализируем график для удаленного режима
        if hasattr(self, "remoteGraphWidget") and self.remoteGraphWidget is not None:
            print("Инициализация графика для удаленного режима...")
            self.remote_graph_builder = GraphBuilder(self.remoteGraphWidget)
            print("График для удаленного режима инициализирован")
        else:
            print("ОШИБКА: remoteGraphWidget не найден в UI!")

        # Подключаем чекбоксы для удаленного режима
        if hasattr(self, "remoteHideDownload"):
            self.remoteHideDownload.stateChanged.connect(self.on_remote_hide_download_changed)
        if hasattr(self, "remoteHideUpload"):
            self.remoteHideUpload.stateChanged.connect(self.on_remote_hide_upload_changed)

        # Инициализируем списки для хранения истории измерений
        self.remote_download_speeds = []
        self.remote_upload_speeds = []
        print("Настройка удаленного мониторинга завершена")

    def setup_remote_table(self):
        """Настройка таблицы с информацией об удаленном адаптере"""
        # Устанавливаем количество строк и столбцов
        self.remoteInfoTable.setColumnCount(2)
        self.remoteInfoTable.setRowCount(15)

        # Устанавливаем заголовки
        self.remoteInfoTable.setHorizontalHeaderLabels(['Параметр', 'Значение'])

        # Устанавливаем фиксированные названия параметров (те же, что и в локальной таблице)
        parameters = [
            'ID адаптера',
            'Описание',
            'Тип интерфейса',
            'IP адрес',
            'MAC адрес',
            'Скорость адаптера',
            'MTU',
            'Статус',
            'Время замера',
            'Загрузка - текущая',
            'Загрузка - максимальная',
            'Загрузка - средняя',
            'Отдача - текущая',
            'Отдача - максимальная',
            'Отдача - средняя'
        ]

        for i, param in enumerate(parameters):
            # Создаем и устанавливаем элемент с названием параметра
            param_item = QTableWidgetItem(param)
            param_item.setFlags(param_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.remoteInfoTable.setItem(i, 0, param_item)
            
            # Создаем и устанавливаем пустое значение
            value_item = QTableWidgetItem('-')
            value_item.setFlags(value_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.remoteInfoTable.setItem(i, 1, value_item)

        # Настраиваем внешний вид таблицы
        self.remoteInfoTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.remoteInfoTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.remoteInfoTable.verticalHeader().hide()
        
        # Устанавливаем высоту строк
        for i in range(15):
            self.remoteInfoTable.setRowHeight(i, 25)

    def connect_to_remote(self):
        """Подключается к удаленному компьютеру"""
        if self.remote_connected:
            self.disconnect_from_remote()
            return

        if not hasattr(self, "remoteIPInput") or not hasattr(self, "remotePortInput"):
            print("Ошибка: Не найдены поля для ввода IP и порта")
            return

        ip = self.remoteIPInput.text()
        try:
            port = int(self.remotePortInput.text())
        except ValueError:
            if hasattr(self, "remoteComputerLabel"):
                self.remoteComputerLabel.setText("Ошибка: неверный формат порта")
            return

        if not ip:
            if hasattr(self, "remoteComputerLabel"):
                self.remoteComputerLabel.setText("Ошибка: введите IP-адрес")
            return

        # Показываем статус подключения
        if hasattr(self, "remoteComputerLabel"):
            self.remoteComputerLabel.setText(f"Подключение к {ip}:{port}...")
        
        # Создаем клиент и подключаемся
        self.remote_client = NetworkClient(ip, port)
        if self.remote_client.connect():
            self.remote_connected = True
            self.connectRemoteButton.setText("Отключиться")
            self.remoteIPInput.setEnabled(False)
            self.remotePortInput.setEnabled(False)
            
            # Загружаем список адаптеров удаленного компьютера
            self.load_remote_adapters()
            
            # Обновляем статус подключения
            if hasattr(self, "remoteComputerLabel"):
                self.remoteComputerLabel.setText(f"Подключено к: {ip}:{port}")
        else:
            if hasattr(self, "remoteComputerLabel"):
                self.remoteComputerLabel.setText(f"Ошибка подключения к {ip}:{port}")
            self.remote_client = None
            self.remote_connected = False

    def disconnect_from_remote(self):
        """Отключается от удаленного компьютера"""
        if self.remote_client:
            # Останавливаем измерения, если они запущены
            if self.remote_is_measuring:
                self.stop_remote_measurement()

            self.remote_client.disconnect()
            self.remote_client = None
            self.remote_connected = False
            self.connectRemoteButton.setText("Подключиться")
            self.remoteIPInput.setEnabled(True)
            self.remotePortInput.setEnabled(True)
            
            # Очищаем данные
            if hasattr(self, "remoteAdapterList"):
                self.remoteAdapterList.clear()
            if hasattr(self, "remoteInfoTable"):
                for i in range(self.remoteInfoTable.rowCount()):
                    self.remoteInfoTable.item(i, 1).setText('-')
            if hasattr(self, "remoteComputerLabel"):
                self.remoteComputerLabel.setText("Отключено")

    def load_remote_adapters(self):
        """Загружает список адаптеров удаленного компьютера"""
        if not self.remote_connected or not hasattr(self, "remoteAdapterList"):
            return

        adapters = self.remote_client.get_adapters() or []
        self.remoteAdapterList.clear()
        self.remoteAdapterList.addItems(adapters)
        
        # Очищаем информацию о предыдущем адаптере
        if hasattr(self, "remoteInfoTable"):
            for i in range(self.remoteInfoTable.rowCount()):
                self.remoteInfoTable.item(i, 1).setText('-')

    def get_remote_computer_name(self):
        """Получает имя удаленного компьютера"""
        if not self.remote_connected:
            return

        # Здесь можно добавить запрос имени компьютера через WMI
        # Пока просто используем IP-адрес
        if hasattr(self, "remoteComputerLabel"):
            self.remoteComputerLabel.setText(f"Подключено к: {self.remote_client.host}")

    def on_remote_adapter_selected(self, adapter_name):
        """Обработчик выбора адаптера на удаленном компьютере"""
        if not self.remote_connected:
            return

        adapter_info = self.remote_client.get_adapter_info(adapter_name) or {}
        
        # Обновляем информацию в таблице
        if hasattr(self, "remoteInfoTable"):
            self.remoteInfoTable.item(0, 1).setText(adapter_info.get('id', '-'))
            self.remoteInfoTable.item(1, 1).setText(adapter_info.get('description', '-'))
            self.remoteInfoTable.item(2, 1).setText(adapter_info.get('interface_type', '-'))
            self.remoteInfoTable.item(3, 1).setText(adapter_info.get('ip', '-'))
            self.remoteInfoTable.item(4, 1).setText(adapter_info.get('mac', '-'))
            self.remoteInfoTable.item(5, 1).setText(adapter_info.get('speed', '-'))
            self.remoteInfoTable.item(6, 1).setText(adapter_info.get('mtu', '-'))
            self.remoteInfoTable.item(7, 1).setText(adapter_info.get('status', '-'))

    






    

    def on_hide_download_changed(self, state):
        """Обработчик изменения состояния чекбокса скрытия линии загрузки"""
        if hasattr(self, "graph_builder"):
            self.graph_builder.set_download_visible(not bool(state))

    def on_hide_upload_changed(self, state):
        """Обработчик изменения состояния чекбокса скрытия линии отдачи"""
        if hasattr(self, "graph_builder"):
            self.graph_builder.set_upload_visible(not bool(state))



    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        if self.remote_connected:
            self.disconnect_from_remote()
        event.accept()

    def toggle_remote_measurement(self):
        """Включает и выключает замер скорости на удаленном компьютере"""
        if not self.remote_connected:
            return

        if self.remote_is_measuring:
            self.stop_remote_measurement()
        else:
            self.start_remote_measurement()

    def start_remote_measurement(self):
        """Запускает замер скорости на удаленном компьютере"""
        if not self.remote_connected:
            return

        current_item = self.remoteAdapterList.currentItem()
        if not current_item:
            return

        adapter_name = current_item.text()
        if not adapter_name:
            return

        # Очищаем историю измерений
        self.remote_download_speeds = []
        self.remote_upload_speeds = []

        # Отправляем команду на запуск измерений
        self.remote_client.start_measurement(adapter_name)
        self.remote_is_measuring = True
        self.remoteMeasureSpeedButton.setText("Стоп")
        self.remote_timer.start(1000)  # Обновляем каждую секунду

    def stop_remote_measurement(self):
        """Останавливает замер скорости на удаленном компьютере"""
        if not self.remote_connected:
            return

        # Отправляем команду на остановку измерений
        self.remote_client.stop_measurement()
        self.remote_is_measuring = False
        self.remoteMeasureSpeedButton.setText("Старт")
        self.remote_timer.stop()

        # Очищаем историю измерений
        self.remote_download_speeds = []
        self.remote_upload_speeds = []

        # Очищаем график
        if hasattr(self, "remote_graph_builder"):
            self.remote_graph_builder.clear_graphs()

        # Очищаем значения в таблице
        if hasattr(self, "remoteInfoTable"):
            for i in range(9, 15):  # Очищаем только значения скорости
                self.remoteInfoTable.item(i, 1).setText('-')

    def update_remote_measurements(self):
        """Обновляет измерения скорости для удаленного адаптера"""
        if not self.remote_connected or not self.remote_is_measuring:
            return

        speeds = self.remote_client.get_speeds()
        print(f"Полученные данные: {speeds}")
        
        if speeds:
            # Добавляем новые значения в историю
            self.remote_download_speeds.append(speeds['download'])
            self.remote_upload_speeds.append(speeds['upload'])

            print(f"История загрузки: {self.remote_download_speeds}")
            print(f"История отдачи: {self.remote_upload_speeds}")

            # Ограничиваем количество точек в истории
            max_points = 60
            if len(self.remote_download_speeds) > max_points:
                self.remote_download_speeds.pop(0)
                self.remote_upload_speeds.pop(0)

            # Обновляем значения скорости в таблице
            self.remoteInfoTable.item(9, 1).setText(f"{speeds['download']:.2f} КБ/с")
            self.remoteInfoTable.item(10, 1).setText(f"{speeds['stats']['max_download']:.2f} КБ/с")
            self.remoteInfoTable.item(11, 1).setText(f"{speeds['stats']['avg_download']:.2f} КБ/с")
            self.remoteInfoTable.item(12, 1).setText(f"{speeds['upload']:.2f} КБ/с")
            self.remoteInfoTable.item(13, 1).setText(f"{speeds['stats']['max_upload']:.2f} КБ/с")
            self.remoteInfoTable.item(14, 1).setText(f"{speeds['stats']['avg_upload']:.2f} КБ/с")

            # Обновляем график
            if hasattr(self, "remote_graph_builder"):
                print("Обновляем график...")
                self.remote_graph_builder.update_graph(
                    self.remote_download_speeds,
                    self.remote_upload_speeds
                )

    def on_remote_hide_download_changed(self, state):
        """Обработчик изменения состояния чекбокса скрытия линии загрузки для удаленного режима"""
        if hasattr(self, "remote_graph_builder"):
            self.remote_graph_builder.set_download_visible(not bool(state))

    def on_remote_hide_upload_changed(self, state):
        """Обработчик изменения состояния чекбокса скрытия линии отдачи для удаленного режима"""
        if hasattr(self, "remote_graph_builder"):
            self.remote_graph_builder.set_upload_visible(not bool(state))

    def clear_remote_graphs(self):
        """Очищает графики и сбрасывает статистику для удаленного режима"""
        try:
            print("Начинаем очистку удаленных графиков...")
            
            # Очищаем историю измерений
            self.remote_download_speeds = []
            self.remote_upload_speeds = []
            print("История измерений очищена")
            
            # Очищаем график
            if hasattr(self, "remote_graph_builder"):
                print("Очищаем график...")
                self.remote_graph_builder.clear_graphs()
                # Принудительно обновляем график пустыми данными
                self.remote_graph_builder.update_graph([], [])
                print("График очищен")
            
            # Очищаем значения в таблице
            if hasattr(self, "remoteInfoTable"):
                print("Очищаем таблицу...")
                for i in range(8, 15):  # Очищаем время и значения скорости
                    self.remoteInfoTable.item(i, 1).setText('-')
                print("Таблица очищена")
                    
            print("Очистка удаленных графиков завершена")
        except Exception as e:
            print(f"Ошибка при очистке удаленных графиков: {e}")