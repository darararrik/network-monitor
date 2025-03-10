import os
from PyQt6.QtWidgets import QMainWindow, QTableWidgetItem
from PyQt6 import uic
from PyQt6.QtCore import Qt
from .network_client import NetworkClient

class ClientWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Загружаем UI
        ui_file = os.path.join(os.path.dirname(__file__), "client_window.ui")
        uic.loadUi(ui_file, self)

        # Создаем клиент
        self.client = NetworkClient()
        
        # Подключаем сигналы клиента
        self.client.connected.connect(self.on_connected)
        self.client.disconnected.connect(self.on_disconnected)
        self.client.error.connect(self.on_error)
        self.client.log_message.connect(self.update_log)
        self.client.adapter_info_received.connect(self.update_adapter_info)
        self.client.speeds_received.connect(self.update_speeds)
        self.client.adapters_list_received.connect(self.update_adapters_list)
        
        # Подключаем сигналы UI
        self.connectButton.clicked.connect(self.toggle_connection)
        self.adapterList.itemSelectionChanged.connect(self.on_adapter_selected)
        
        # Инициализация UI
        self.setup_ui()
        
    def setup_ui(self):
        """Настройка начального состояния UI"""
        # Настраиваем таблицу информации об адаптере
        self.adapterInfoTable.setColumnCount(2)
        self.adapterInfoTable.setHorizontalHeaderLabels(["Параметр", "Значение"])
        
        # Очищаем список адаптеров
        self.adapterList.clear()
        
        # Устанавливаем начальный статус
        self.statusLabel.setText("Статус: Не подключен")
        
    def toggle_connection(self):
        """Подключение/отключение от сервера"""
        if not self.client.is_connected:
            # Подключаемся
            ip = self.serverIPInput.text()
            try:
                port = int(self.serverPortInput.text())
            except ValueError:
                self.update_log("Ошибка: некорректный порт")
                return
                
            self.client.connect_to_server(ip, port)
        else:
            # Отключаемся
            self.client.disconnect()
            
    def on_connected(self):
        """Обработка успешного подключения"""
        self.connectButton.setText("Отключиться")
        self.statusLabel.setText("Статус: Подключен")
        self.serverIPInput.setEnabled(False)
        self.serverPortInput.setEnabled(False)
        
        # Загружаем список адаптеров
        adapters = self.client.get_adapters_list()
        self.update_adapters_list(adapters)
        
    def on_disconnected(self):
        """Обработка отключения"""
        self.connectButton.setText("Подключиться")
        self.statusLabel.setText("Статус: Не подключен")
        self.serverIPInput.setEnabled(True)
        self.serverPortInput.setEnabled(True)
        self.adapterList.clear()
        self.adapterInfoTable.setRowCount(0)
        
    def on_error(self, error_msg):
        """Обработка ошибок"""
        self.update_log(f"Ошибка: {error_msg}")
        
    def update_log(self, message):
        """Обновление лога"""
        self.logWidget.append(message)
        
    def on_adapter_selected(self):
        """Обработка выбора адаптера из списка"""
        items = self.adapterList.selectedItems()
        if not items:
            return
            
        adapter_name = items[0].text()
        # Получаем информацию об адаптере
        info = self.client.get_adapter_info(adapter_name)
        self.update_adapter_info(info)
        
    def update_adapter_info(self, info):
        """Обновление информации об адаптере"""
        self.adapterInfoTable.setRowCount(len(info))
        for row, (key, value) in enumerate(info.items()):
            self.adapterInfoTable.setItem(row, 0, QTableWidgetItem(str(key)))
            self.adapterInfoTable.setItem(row, 1, QTableWidgetItem(str(value)))
            
        # Настраиваем ширину столбцов
        self.adapterInfoTable.resizeColumnsToContents()
        self.adapterInfoTable.horizontalHeader().setStretchLastSection(True)
            
    def update_speeds(self, speeds):
        """Обновление информации о скорости"""
        # Проверяем, есть ли уже строки для скорости
        speed_rows = []
        for row in range(self.adapterInfoTable.rowCount()):
            param = self.adapterInfoTable.item(row, 0).text()
            if "Загрузка" in param or "Отдача" in param:
                speed_rows.append(row)
                
        # Если строк для скорости нет, добавляем их
        if not speed_rows:
            # Добавляем строки для текущей скорости
            current_row = self.adapterInfoTable.rowCount()
            self.adapterInfoTable.setRowCount(current_row + 2)
            
            self.adapterInfoTable.setItem(current_row, 0, QTableWidgetItem("Загрузка - текущая"))
            self.adapterInfoTable.setItem(current_row, 1, QTableWidgetItem(f"{speeds['download']:.2f} Кбит/с"))
            
            self.adapterInfoTable.setItem(current_row + 1, 0, QTableWidgetItem("Отдача - текущая"))
            self.adapterInfoTable.setItem(current_row + 1, 1, QTableWidgetItem(f"{speeds['upload']:.2f} Кбит/с"))
            
            # Добавляем статистику
            if 'stats' in speeds:
                stats = speeds['stats']
                stat_row = current_row + 2
                self.adapterInfoTable.setRowCount(stat_row + 4)
                
                self.adapterInfoTable.setItem(stat_row, 0, QTableWidgetItem("Загрузка - максимальная"))
                self.adapterInfoTable.setItem(stat_row, 1, QTableWidgetItem(f"{stats['max_download']:.2f} Кбит/с"))
                
                self.adapterInfoTable.setItem(stat_row + 1, 0, QTableWidgetItem("Загрузка - средняя"))
                self.adapterInfoTable.setItem(stat_row + 1, 1, QTableWidgetItem(f"{stats['avg_download']:.2f} Кбит/с"))
                
                self.adapterInfoTable.setItem(stat_row + 2, 0, QTableWidgetItem("Отдача - максимальная"))
                self.adapterInfoTable.setItem(stat_row + 2, 1, QTableWidgetItem(f"{stats['max_upload']:.2f} Кбит/с"))
                
                self.adapterInfoTable.setItem(stat_row + 3, 0, QTableWidgetItem("Отдача - средняя"))
                self.adapterInfoTable.setItem(stat_row + 3, 1, QTableWidgetItem(f"{stats['avg_upload']:.2f} Кбит/с"))
        else:
            # Обновляем существующие строки
            for row in range(self.adapterInfoTable.rowCount()):
                param = self.adapterInfoTable.item(row, 0).text()
                if param == "Загрузка - текущая":
                    self.adapterInfoTable.setItem(row, 1, QTableWidgetItem(f"{speeds['download']:.2f} Кбит/с"))
                elif param == "Отдача - текущая":
                    self.adapterInfoTable.setItem(row, 1, QTableWidgetItem(f"{speeds['upload']:.2f} Кбит/с"))
                
                # Обновляем статистику
                if 'stats' in speeds:
                    stats = speeds['stats']
                    if param == "Загрузка - максимальная":
                        self.adapterInfoTable.setItem(row, 1, QTableWidgetItem(f"{stats['max_download']:.2f} Кбит/с"))
                    elif param == "Загрузка - средняя":
                        self.adapterInfoTable.setItem(row, 1, QTableWidgetItem(f"{stats['avg_download']:.2f} Кбит/с"))
                    elif param == "Отдача - максимальная":
                        self.adapterInfoTable.setItem(row, 1, QTableWidgetItem(f"{stats['max_upload']:.2f} Кбит/с"))
                    elif param == "Отдача - средняя":
                        self.adapterInfoTable.setItem(row, 1, QTableWidgetItem(f"{stats['avg_upload']:.2f} Кбит/с"))
                        
        # Настраиваем ширину столбцов
        self.adapterInfoTable.resizeColumnsToContents()
        self.adapterInfoTable.horizontalHeader().setStretchLastSection(True)

    def update_adapters_list(self, adapters):
        """Обновление списка адаптеров"""
        self.adapterList.clear()
        for adapter in adapters:
            self.adapterList.addItem(adapter)
            
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        if self.client.is_connected:
            self.client.disconnect()
        event.accept() 