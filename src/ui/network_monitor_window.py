import os
import sys
from PyQt6.QtWidgets import QMainWindow, QTableWidgetItem, QHeaderView, QMessageBox, QTabWidget
from PyQt6 import uic
from PyQt6.QtCore import QTimer, Qt

from src.core.network_monitor import NetworkMonitor
from src.core.network_client import NetworkClient
from src.core.graph_builder import GraphBuilder

class NetworkMonitorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Получаем абсолютный путь к UI файлу
        ui_file = os.path.join(os.path.dirname(__file__), "network_monitor.ui")
        uic.loadUi(ui_file, self)

        # Инициализация локального мониторинга
        self.network_monitor = NetworkMonitor()
        
        # Настройка таблицы
        self.setup_table()
        
        self.selected_adapter = None
        self.load_adapters()
        self.adapterList.currentTextChanged.connect(self.on_adapter_selected)

        # Настройка кнопок
        self.is_measuring = False
        self.measureSpeedButton.setEnabled(False)
        self.measureSpeedButton.clicked.connect(self.toggle_measurement)
        
        # Подключаем кнопку очистки графиков
        if hasattr(self, "clearGraphs"):
            self.clearGraphs.clicked.connect(self.clear_graphs)

        # Настройка таймера
        self.target_time = 0
        self.hoursInput.setPlaceholderText("Часы")
        self.minutesInput.setPlaceholderText("Мин")
        self.secondsInput.setPlaceholderText("Сек")
        
        # Подключаем обработчики изменения времени
        self.hoursInput.textChanged.connect(self.on_time_changed)
        self.minutesInput.textChanged.connect(self.on_time_changed)
        self.secondsInput.textChanged.connect(self.on_time_changed)

        # График
        if hasattr(self, "graphWidget") and self.graphWidget is not None:
            self.graph_builder = GraphBuilder(self.graphWidget)
        else:
            print("Ошибка: graphWidget не найден в UI!")

        # Подключаем чекбоксы
        self.hideDownload.stateChanged.connect(self.on_hide_download_changed)
        self.hideUpload.stateChanged.connect(self.on_hide_upload_changed)

        # Инициализация таймера
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_measurements)
        
        # Инициализация переменных для графика
        self.elapsed_time = -2
        self.first_measurement = True

        # Инициализация удаленного мониторинга
        self.remote_client = None
        self.remote_connected = False
        self.setup_remote_monitoring()

    def setup_remote_monitoring(self):
        """Настройка удаленного мониторинга"""
        # Подключаем кнопку подключения
        if hasattr(self, "connectRemoteButton"):
            self.connectRemoteButton.clicked.connect(self.connect_to_remote)
        
        # Устанавливаем значение порта по умолчанию
        if hasattr(self, "remotePortInput"):
            self.remotePortInput.setText("5000")

    def connect_to_remote(self):
        """Подключается к удаленному компьютеру"""
        if self.remote_connected:
            self.disconnect_from_remote()
            return

        if not hasattr(self, "remoteIPinput") or not hasattr(self, "remotePortInput"):
            return

        ip = self.remoteIPinput.text()
        try:
            port = int(self.remotePortInput.text())
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Неверный формат порта")
            return

        if not ip:
            QMessageBox.warning(self, "Ошибка", "Введите IP-адрес")
            return

        # Создаем клиент и подключаемся
        self.remote_client = NetworkClient(ip, port)
        if self.remote_client.connect():
            self.remote_connected = True
            self.connectRemoteButton.setText("Отключиться")
            self.remoteIPinput.setEnabled(False)
            self.remotePortInput.setEnabled(False)
            
            # Загружаем список адаптеров удаленного компьютера
            self.load_remote_adapters()
            
            # Получаем имя компьютера
            self.get_remote_computer_name()
            
            QMessageBox.information(self, "Успех", "Подключено к удаленному компьютеру")
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к удаленному компьютеру")
            self.remote_client = None
            self.remote_connected = False

    def disconnect_from_remote(self):
        """Отключается от удаленного компьютера"""
        if self.remote_client:
            self.remote_client.disconnect()
            self.remote_client = None
            self.remote_connected = False
            self.connectRemoteButton.setText("Подключиться")
            self.remoteIPinput.setEnabled(True)
            self.remotePortInput.setEnabled(True)
            
            # Очищаем данные
            if hasattr(self, "remoteAdapterList"):
                self.remoteAdapterList.clear()
            if hasattr(self, "remoteInfoTable"):
                for i in range(self.remoteInfoTable.rowCount()):
                    self.remoteInfoTable.item(i, 1).setText('-')

    def load_remote_adapters(self):
        """Загружает список адаптеров удаленного компьютера"""
        if not self.remote_connected or not hasattr(self, "remoteAdapterList"):
            return

        adapters = self.remote_client.get_adapters() or []
        self.remoteAdapterList.clear()
        self.remoteAdapterList.addItems(adapters)

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

    def setup_table(self):
        """Настройка таблицы с информацией об адаптере"""
        # Устанавливаем количество строк и столбцов
        self.adapterInfoTable.setColumnCount(2)
        self.adapterInfoTable.setRowCount(15)

        # Устанавливаем заголовки
        self.adapterInfoTable.setHorizontalHeaderLabels(['Параметр', 'Значение'])

        # Устанавливаем фиксированные названия параметров
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
            self.adapterInfoTable.setItem(i, 0, param_item)
            
            # Создаем и устанавливаем пустое значение
            value_item = QTableWidgetItem('-')
            value_item.setFlags(value_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.adapterInfoTable.setItem(i, 1, value_item)

        # Настраиваем внешний вид таблицы
        self.adapterInfoTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.adapterInfoTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.adapterInfoTable.verticalHeader().hide()
        
        # Устанавливаем высоту строк
        for i in range(15):
            self.adapterInfoTable.setRowHeight(i, 25)

    def load_adapters(self):
        """Загружает список адаптеров"""
        adapters = self.network_monitor.get_adapters()
        self.adapterList.addItems(adapters)

    def on_time_changed(self, text=None):
        """Обработчик изменения времени"""
        try:
            hours = int(self.hoursInput.text()) if self.hoursInput.text() else 0
            minutes = int(self.minutesInput.text()) if self.minutesInput.text() else 0
            seconds = int(self.secondsInput.text()) if self.secondsInput.text() else 0
            
            # Проверяем корректность введенных значений
            if minutes >= 60 or seconds >= 60:
                return
                
            self.target_time = hours * 3600 + minutes * 60 + seconds
        except ValueError:
            self.target_time = 0
        
        # Активируем кнопку только если выбран адаптер
        self.measureSpeedButton.setEnabled(self.selected_adapter is not None)

    def on_adapter_selected(self, adapter_name):
        """Вызывается при выборе адаптера"""
        self.selected_adapter = adapter_name
        # Активируем кнопку только если выбран адаптер
        self.measureSpeedButton.setEnabled(True)
        self.show_adapter_info(adapter_name)

    def show_adapter_info(self, adapter_name):
        """Отображает информацию об адаптере"""
        adapter_info = self.network_monitor.get_adapter_info(adapter_name) or {}
        
        # Обновляем значения в таблице
        self.adapterInfoTable.item(0, 1).setText(adapter_info.get('id', '-'))
        self.adapterInfoTable.item(1, 1).setText(adapter_info.get('description', '-'))
        self.adapterInfoTable.item(2, 1).setText(adapter_info.get('interface_type', '-'))
        self.adapterInfoTable.item(3, 1).setText(adapter_info.get('ip', '-'))
        self.adapterInfoTable.item(4, 1).setText(adapter_info.get('mac', '-'))
        self.adapterInfoTable.item(5, 1).setText(adapter_info.get('speed', '-'))
        self.adapterInfoTable.item(6, 1).setText(adapter_info.get('mtu', '-'))
        self.adapterInfoTable.item(7, 1).setText(adapter_info.get('status', '-'))
        self.adapterInfoTable.item(8, 1).setText('-')  # Время замера будет обновляться отдельно
        
        # Сбрасываем значения скорости
        for i in range(9, 15):
            self.adapterInfoTable.item(i, 1).setText('-')

    def toggle_measurement(self):
        """Включает и выключает замер скорости"""
        if self.is_measuring:
            self.stop_measurement()
        else:
            self.start_measurement()

    def start_measurement(self):
        """Запускает замер скорости"""
        self.network_monitor.start_measurement(self.selected_adapter)
        self.is_measuring = True
        self.measureSpeedButton.setText("Стоп")
        self.timer.start(1000)  # Обновляем каждую секунду
        self.first_measurement = True
        self.elapsed_time = -2  # Начинаем с -2

    def stop_measurement(self):
        """Останавливает замер скорости"""
        self.network_monitor.stop_measurement()
        self.is_measuring = False
        self.measureSpeedButton.setText("Старт")
        self.timer.stop()

    def update_measurements(self):
        """Обновляет все измерения (время и график)"""
        if self.selected_adapter:
            speeds = self.network_monitor.get_current_speeds()
            if speeds:
                # Если это первое измерение, начинаем отсчет времени
                if self.first_measurement:
                    self.first_measurement = False
                    self.elapsed_time = 0
                else:
                    self.elapsed_time += 1

                # Обновляем график
                self.graph_builder.update_graph(
                    self.network_monitor.download_speeds,
                    self.network_monitor.upload_speeds
                )
                
                # Обновляем информацию о скорости в таблице
                stats = speeds['stats']
                
                # Обновляем значения скорости загрузки
                self.adapterInfoTable.item(9, 1).setText(f"{speeds['download']:.2f} КБ/с")
                self.adapterInfoTable.item(10, 1).setText(f"{stats['max_download']:.2f} КБ/с")
                self.adapterInfoTable.item(11, 1).setText(f"{stats['avg_download']:.2f} КБ/с")

                # Обновляем значения скорости отдачи
                self.adapterInfoTable.item(12, 1).setText(f"{speeds['upload']:.2f} КБ/с")
                self.adapterInfoTable.item(13, 1).setText(f"{stats['max_upload']:.2f} КБ/с")
                self.adapterInfoTable.item(14, 1).setText(f"{stats['avg_upload']:.2f} КБ/с")

                # Преобразуем время в формат ЧЧ:ММ:СС
                hours = self.elapsed_time // 3600
                minutes = (self.elapsed_time % 3600) // 60
                seconds = self.elapsed_time % 60
                
                if hasattr(self, "timeLabel"):
                    if self.target_time > 0:
                        # Если установлено время, показываем оставшееся время
                        remaining_time = self.target_time - self.elapsed_time
                        hours = remaining_time // 3600
                        minutes = (remaining_time % 3600) // 60
                        seconds = remaining_time % 60
                        self.timeLabel.setText(f"Осталось: {hours:02d}:{minutes:02d}:{seconds:02d}")
                    else:
                        # Если время не установлено, показываем прошедшее время
                        self.timeLabel.setText(f"Прошло: {hours:02d}:{minutes:02d}:{seconds:02d}")
                
                # Обновляем время в таблице
                self.adapterInfoTable.item(8, 1).setText(f"{self.elapsed_time} сек")
                
                # Проверяем, не истекло ли время, если оно было установлено
                if self.target_time > 0 and self.elapsed_time >= self.target_time:
                    self.stop_measurement()

    def on_hide_download_changed(self, state):
        """Обработчик изменения состояния чекбокса скрытия линии загрузки"""
        if hasattr(self, "graph_builder"):
            self.graph_builder.set_download_visible(not bool(state))

    def on_hide_upload_changed(self, state):
        """Обработчик изменения состояния чекбокса скрытия линии отдачи"""
        if hasattr(self, "graph_builder"):
            self.graph_builder.set_upload_visible(not bool(state))

    def clear_graphs(self):
        """Очищает графики и сбрасывает статистику"""
        try:
            # Очищаем графики
            if hasattr(self, "graph_builder"):
                self.graph_builder.clear_graphs()
            
            # Сбрасываем значения в таблице
            self.adapterInfoTable.item(8, 1).setText('-')  # Время
            for i in range(9, 15):  # Скорости
                self.adapterInfoTable.item(i, 1).setText('-')
            
            # Сбрасываем счетчик времени
            self.elapsed_time = -2
            self.first_measurement = True
            
            # Если есть метка времени, очищаем её
            if hasattr(self, "timeLabel"):
                self.timeLabel.setText("")
                
            # Очищаем данные в network_monitor
            if hasattr(self, "network_monitor"):
                self.network_monitor.download_speeds = []
                self.network_monitor.upload_speeds = []
                self.network_monitor.max_download = 0
                self.network_monitor.max_upload = 0
                self.network_monitor.total_download = 0
                self.network_monitor.total_upload = 0
                self.network_monitor.measurement_count = 0
        except Exception as e:
            print(f"Ошибка при очистке графиков: {e}")

    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        if self.remote_connected:
            self.disconnect_from_remote()
        event.accept()