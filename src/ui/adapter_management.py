# src/ui/adapter_management.py

from PyQt6.QtWidgets import QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt

class AdapterManagement:
    def __init__(self, window, network_monitor):
        self.window = window
        self.network_monitor = network_monitor

    def setup_table(self):
        """Настройка таблицы с информацией об адаптере"""
        self.window.adapterInfoTable.setColumnCount(2)
        self.window.adapterInfoTable.setRowCount(15)

        # Устанавливаем заголовки
        self.window.adapterInfoTable.setHorizontalHeaderLabels(['Параметр', 'Значение'])

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
            self.add_table_item(i, 0, param)
            self.add_table_item(i, 1, '-')

        self.configure_table()

    def add_table_item(self, row, column, text):
        """Добавляет элемент в таблицу"""
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.window.adapterInfoTable.setItem(row, column, item)

    def configure_table(self):
        """Настраивает внешний вид таблицы"""
        self.window.adapterInfoTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.window.adapterInfoTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.window.adapterInfoTable.verticalHeader().hide()
        for i in range(15):
            self.window.adapterInfoTable.setRowHeight(i, 25)

    def load_adapters(self):
        """Загружает список адаптеров"""
        adapters = self.window.network_monitor.get_adapters()
        self.window.adapterList.addItems(adapters)

    def on_adapter_selected(self, adapter_name):
        """Вызывается при выборе адаптера"""
        self.window.selected_adapter = adapter_name
        # Активируем кнопку только если выбран адаптер
        self.window.measureSpeedButton.setEnabled(True)
        self.show_adapter_info(adapter_name)

    def show_adapter_info(self, adapter_name):
        """Отображает информацию об адаптере"""
        adapter_info = self.network_monitor.get_adapter_info(adapter_name) or {}
        
        # Обновляем значения в таблице
        self.window.adapterInfoTable.item(0, 1).setText(adapter_info.get('id', '-'))
        self.window.adapterInfoTable.item(1, 1).setText(adapter_info.get('description', '-'))
        self.window.adapterInfoTable.item(2, 1).setText(adapter_info.get('interface_type', '-'))
        self.window.adapterInfoTable.item(3, 1).setText(adapter_info.get('ip', '-'))
        self.window.adapterInfoTable.item(4, 1).setText(adapter_info.get('mac', '-'))
        self.window.adapterInfoTable.item(5, 1).setText(adapter_info.get('speed', '-'))
        self.window.adapterInfoTable.item(6, 1).setText(adapter_info.get('mtu', '-'))
        self.window.adapterInfoTable.item(7, 1).setText(adapter_info.get('status', '-'))
        self.window.adapterInfoTable.item(8, 1).setText('-')  # Время замера будет обновляться отдельно
        
        # Сбрасываем значения скорости
        for i in range(9, 15):
            self.window.adapterInfoTable.item(i, 1).setText('-')