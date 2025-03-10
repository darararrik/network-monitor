from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QListWidgetItem, QTableWidgetItem
from src.core.network_server import NetworkServer

class ServerManagement:
    """Класс для управления серверной частью приложения"""
    
    def __init__(self, window):
        """
        Инициализация менеджера сервера
        
        Args:
            window: Главное окно приложения
        """
        self.window = window
        self.server = NetworkServer()
        self.selected_client = None
        self.selected_adapter = None
        self.is_monitoring = False
        
        # Инициализация данных для графика
        self.download_speeds = []
        self.upload_speeds = []
        
        # Настройка сигналов сервера
        self.server.client_connected.connect(self.on_client_connected)
        self.server.client_disconnected.connect(self.on_client_disconnected)
        self.server.server_started.connect(self.on_server_started)
        self.server.server_stopped.connect(self.on_server_stopped)
        self.server.log_message.connect(self.on_log_message)
        self.server.adapters_list_received.connect(self.on_adapters_list_received)
        self.server.adapter_info_received.connect(self.on_adapter_info_received)
        self.server.speeds_data_received.connect(self.on_speeds_data_received)
        
        # Настройка интерфейса
        self.setup_ui()
        
        # Инициализация графика для удаленного мониторинга
        if hasattr(window, "remoteGraphWidget"):
            from src.core.graph_builder import GraphBuilder
            self.log_message("Инициализация графика для удаленного мониторинга...")
            self.graph_builder = GraphBuilder(window.remoteGraphWidget)
            self.log_message("График успешно инициализирован")
        else:
            self.log_message("ВНИМАНИЕ: Виджет remoteGraphWidget не найден!")
        
        # Таймер для обновления статуса
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)  # Обновление каждые 5 секунд
        
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Подключаем кнопку запуска сервера
        if hasattr(self.window, "startServerButton"):
            self.window.startServerButton.clicked.connect(self.toggle_server)
            
        # Настраиваем выбор клиента на вкладке Сервер
        if hasattr(self.window, "clientsListWidget"):
            self.window.clientsListWidget.itemClicked.connect(self.on_client_selected)
            
        # Настраиваем выбор клиента на вкладке Удаленный доступ
        if hasattr(self.window, "clientsList"):
            self.window.clientsList.itemClicked.connect(self.on_client_selected)
            
        # Настраиваем выбор адаптера
        if hasattr(self.window, "remoteAdapterList"):
            self.window.remoteAdapterList.itemClicked.connect(self.on_adapter_selected)
            
        # Настраиваем кнопку замера скорости
        if hasattr(self.window, "remoteMeasureSpeedButton"):
            self.window.remoteMeasureSpeedButton.clicked.connect(self.toggle_monitoring)
            
        # Инициализируем таблицу информации
        if hasattr(self.window, "remoteInfoTable"):
            table = self.window.remoteInfoTable
            table.setColumnCount(2)
            table.setHorizontalHeaderLabels(['Параметр', 'Значение'])
            table.horizontalHeader().setStretchLastSection(True)
            self.log_message("Инициализирована таблица информации об адаптере")
            
        # Устанавливаем порт по умолчанию
        if hasattr(self.window, "serverPortInput"):
            self.window.serverPortInput.setText("5000")
            
    def toggle_server(self):
        """Запуск/остановка сервера"""
        if self.server.is_running:
            self.server.stop_server()
            if hasattr(self.window, "startServerButton"):
                self.window.startServerButton.setText("Запустить сервер")
            
            # Очищаем список клиентов при остановке сервера
            if hasattr(self.window, "clientsListWidget"):
                self.window.clientsListWidget.clear()
                
            # Сбрасываем выбор клиента и адаптера
            self.selected_client = None
            self.selected_adapter = None
            
            # Обновляем состояние UI
            self.update_ui_state(False)
        else:
            try:
                port = 5000
                if hasattr(self.window, "serverPortInput"):
                    try:
                        port = int(self.window.serverPortInput.text())
                    except ValueError:
                        self.log_message("Ошибка: некорректный порт. Используется порт 5000.")
                        port = 5000
                
                if self.server.start_server(port):
                    if hasattr(self.window, "startServerButton"):
                        self.window.startServerButton.setText("Остановить сервер")
                    
                    # Обновляем состояние UI
                    self.update_ui_state(True)
            except Exception as e:
                self.log_message(f"Ошибка запуска сервера: {e}")
                
    def update_ui_state(self, server_running):
        """Обновление состояния UI в зависимости от статуса сервера"""
        # Отключаем поле ввода порта при запущенном сервере
        if hasattr(self.window, "serverPortInput"):
            self.window.serverPortInput.setEnabled(not server_running)
            
        # Обновляем доступность компонентов для работы с клиентами на вкладке Сервер
        if hasattr(self.window, "clientsListWidget"):
            self.window.clientsListWidget.setEnabled(server_running)
            
        # Обновляем доступность компонентов для работы с клиентами на вкладке Удаленный доступ
        if hasattr(self.window, "clientsList"):
            self.window.clientsList.setEnabled(server_running)
            
        if hasattr(self.window, "remoteAdapterList"):
            self.window.remoteAdapterList.setEnabled(False) # По умолчанию отключен до выбора клиента
            
        if hasattr(self.window, "remoteMeasureSpeedButton"):
            self.window.remoteMeasureSpeedButton.setEnabled(False) # По умолчанию отключен до выбора адаптера
            
    def update_status(self):
        """Обновление статуса сервера"""
        status = "Запущен" if self.server.is_running else "Остановлен"
        clients_count = len(self.server.clients) if self.server.is_running else 0
        
        if hasattr(self.window, "serverStatusLabel"):
            self.window.serverStatusLabel.setText(f"Статус сервера: {status}")
            
        if hasattr(self.window, "clientsCountLabel"):
            self.window.clientsCountLabel.setText(f"Подключено клиентов: {clients_count}")
            
    def on_client_connected(self, ip, port):
        """Обработка подключения клиента"""
        client_id = f"{ip}:{port}"
        self.log_message(f"Клиент подключен: {client_id}")
        
        # Добавляем клиента в список на вкладке Сервер
        if hasattr(self.window, "clientsListWidget"):
            item = QListWidgetItem(client_id)
            # Сохраняем идентификатор клиента в данных элемента
            item.setData(Qt.ItemDataRole.UserRole, client_id)
            self.window.clientsListWidget.addItem(item)
            
        # Добавляем клиента в список на вкладке Удаленный доступ
        if hasattr(self.window, "clientsList"):
            item = QListWidgetItem(client_id)
            # Сохраняем идентификатор клиента в данных элемента
            item.setData(Qt.ItemDataRole.UserRole, client_id)
            self.window.clientsList.addItem(item)
            
        # Запускаем таймер для обновления имени клиента после получения полной информации
        QTimer.singleShot(1000, lambda: self.update_client_names(client_id))
        
    def update_client_names(self, client_id):
        """Обновление отображения имени клиента в списках
        
        Args:
            client_id: Идентификатор клиента
        """
        pc_name = self.server.get_client_name(client_id)
        display_name = f"{client_id} ({pc_name})"
        
        # Обновляем имя в списке на вкладке Сервер
        if hasattr(self.window, "clientsListWidget"):
            items = self.window.clientsListWidget.findItems(client_id, Qt.MatchFlag.MatchStartsWith)
            for item in items:
                if item.data(Qt.ItemDataRole.UserRole) == client_id:
                    item.setText(display_name)
                    
        # Обновляем имя в списке на вкладке Удаленный доступ
        if hasattr(self.window, "clientsList"):
            items = self.window.clientsList.findItems(client_id, Qt.MatchFlag.MatchStartsWith)
            for item in items:
                if item.data(Qt.ItemDataRole.UserRole) == client_id:
                    item.setText(display_name)
        
    def on_client_disconnected(self, ip, port):
        """Обработка отключения клиента"""
        client_id = f"{ip}:{port}"
        self.log_message(f"Клиент отключен: {client_id}")
        
        # Удаляем клиента из списка на вкладке Сервер
        if hasattr(self.window, "clientsListWidget"):
            items = self.window.clientsListWidget.findItems(client_id, 0)
            for item in items:
                row = self.window.clientsListWidget.row(item)
                self.window.clientsListWidget.takeItem(row)
                
        # Удаляем клиента из списка на вкладке Удаленный доступ
        if hasattr(self.window, "clientsList"):
            items = self.window.clientsList.findItems(client_id, 0)
            for item in items:
                row = self.window.clientsList.row(item)
                self.window.clientsList.takeItem(row)
                
        # Если отключился выбранный клиент, сбрасываем выбор
        if self.selected_client == client_id:
            self.selected_client = None
            if hasattr(self.window, "remoteAdapterList"):
                self.window.remoteAdapterList.clear()
                self.window.remoteAdapterList.setEnabled(False)
                
            if hasattr(self.window, "remoteInfoTable"):
                self.window.remoteInfoTable.clearContents()
                self.window.remoteInfoTable.setRowCount(0)
                
            if hasattr(self.window, "remoteMeasureSpeedButton"):
                self.window.remoteMeasureSpeedButton.setEnabled(False)
                
    def on_server_started(self, port):
        """Обработка запуска сервера"""
        self.log_message(f"Сервер запущен на порту {port}")
        if hasattr(self.window, "serverStatusLabel"):
            self.window.serverStatusLabel.setText(f"Статус сервера: Запущен (порт {port})")
            
        # Обновляем информацию для подключения
        ips = self.server.get_ip_addresses()
        ip_info = "IP-адреса для подключения клиентов:"
        for ip in ips:
            ip_info += f"\n - {ip}:{port}"
            
        self.log_message(ip_info)
        
    def on_server_stopped(self):
        """Обработка остановки сервера"""
        self.log_message("Сервер остановлен")
        if hasattr(self.window, "serverStatusLabel"):
            self.window.serverStatusLabel.setText("Статус сервера: Остановлен")
            
        # Очищаем список клиентов на вкладке Сервер
        if hasattr(self.window, "clientsListWidget"):
            self.window.clientsListWidget.clear()
            
        # Очищаем список клиентов на вкладке Удаленный доступ
        if hasattr(self.window, "clientsList"):
            self.window.clientsList.clear()
            
    def on_log_message(self, message):
        """Обработка сообщений от сервера"""
        self.log_message(message)
        
    def log_message(self, message):
        """Добавление сообщения в лог"""
        if hasattr(self.window, "serverLogWidget"):
            self.window.serverLogWidget.append(message)
            
    def on_client_selected(self, item):
        """Обработка выбора клиента из списка"""
        # Получаем идентификатор клиента из данных элемента
        client_id = item.data(Qt.ItemDataRole.UserRole)
        if not client_id:
            client_id = item.text()  # Для обратной совместимости
            
        self.selected_client = client_id
        self.log_message(f"Выбран клиент: {client_id}")
        
        # Запрашиваем список адаптеров
        self.log_message(f"Отправляем запрос на получение списка адаптеров для клиента {client_id}")
        result = self.server.request_adapters_list(self.selected_client)
        self.log_message(f"Результат запроса адаптеров: {result}")
        
        # Включаем список адаптеров
        if hasattr(self.window, "remoteAdapterList"):
            self.window.remoteAdapterList.setEnabled(True)
            self.window.remoteAdapterList.clear()
            
        # Сбрасываем выбранный адаптер
        self.selected_adapter = None
        
        # Отключаем кнопку замера скорости
        if hasattr(self.window, "remoteMeasureSpeedButton"):
            self.window.remoteMeasureSpeedButton.setEnabled(False)
            
    def on_adapter_selected(self, item):
        """Обработка выбора адаптера из списка"""
        if not self.selected_client:
            self.log_message("Не выбран клиент, нельзя запросить информацию об адаптере")
            return
            
        self.selected_adapter = item.text()
        self.log_message(f"Выбран адаптер: {self.selected_adapter}")
        
        # Запрашиваем информацию об адаптере
        self.log_message(f"Отправляем запрос на получение информации об адаптере {self.selected_adapter} для клиента {self.selected_client}")
        result = self.server.request_adapter_info(self.selected_client, self.selected_adapter)
        self.log_message(f"Результат запроса информации об адаптере: {result}")
        
        # Включаем кнопку замера скорости
        if hasattr(self.window, "remoteMeasureSpeedButton"):
            self.window.remoteMeasureSpeedButton.setEnabled(True)
            self.window.remoteMeasureSpeedButton.setText("Начать замер")
            
    def on_adapters_list_received(self, client_id, adapters):
        """Обработка полученного списка адаптеров"""
        self.log_message(f"Получен список адаптеров от клиента {client_id}: {adapters}")
        
        if self.selected_client != client_id:
            self.log_message(f"Игнорируем список адаптеров, т.к. выбран другой клиент: {self.selected_client}")
            return
            
        # Заполняем список адаптеров
        if hasattr(self.window, "remoteAdapterList"):
            self.log_message(f"Заполняем список адаптеров на UI: {adapters}")
            self.window.remoteAdapterList.clear()
            for adapter in adapters:
                self.window.remoteAdapterList.addItem(adapter)
                
    def on_adapter_info_received(self, client_id, adapter, info):
        """Обработка полученной информации об адаптере"""
        self.log_message(f"Получена информация об адаптере {adapter} от клиента {client_id}: {info}")
        
        if self.selected_client != client_id or self.selected_adapter != adapter:
            self.log_message(f"Игнорируем информацию об адаптере, т.к. выбран другой клиент/адаптер: {self.selected_client}/{self.selected_adapter}")
            return
            
        # Заполняем таблицу информацией
        if hasattr(self.window, "remoteInfoTable"):
            self.log_message(f"Заполняем таблицу информацией об адаптере: {info}")
            table = self.window.remoteInfoTable
            table.setRowCount(len(info))
            table.setColumnCount(2)
            table.setHorizontalHeaderLabels(['Параметр', 'Значение'])
            
            for row, (key, value) in enumerate(info.items()):
                table.setItem(row, 0, QTableWidgetItem(str(key)))
                table.setItem(row, 1, QTableWidgetItem(str(value)))
                
            # Настраиваем ширину столбцов
            table.horizontalHeader().setStretchLastSection(True)
            
    def toggle_monitoring(self):
        """Включение/выключение мониторинга скорости на выбранном адаптере"""
        if not self.selected_client or not self.selected_adapter:
            return
            
        if self.is_monitoring:
            # Останавливаем мониторинг
            self.stop_monitoring()
        else:
            # Запускаем мониторинг
            self.start_monitoring()
            
    def start_monitoring(self):
        """Запуск мониторинга скорости"""
        if not self.selected_client or not self.selected_adapter:
            return
            
        # Запускаем мониторинг на сервере
        self.server.start_monitoring(self.selected_client, self.selected_adapter)
        self.is_monitoring = True
        
        # Обновляем текст кнопки
        if hasattr(self.window, "remoteMeasureSpeedButton"):
            self.window.remoteMeasureSpeedButton.setText("Остановить замер")
            
        self.log_message(f"Запущен мониторинг скорости для {self.selected_adapter} на клиенте {self.selected_client}")
            
    def stop_monitoring(self):
        """Остановка мониторинга скорости"""
        if not self.selected_client:
            return
            
        # Останавливаем мониторинг на сервере
        self.server.stop_monitoring(self.selected_client)
        self.is_monitoring = False
        
        # Обновляем текст кнопки
        if hasattr(self.window, "remoteMeasureSpeedButton"):
            self.window.remoteMeasureSpeedButton.setText("Начать замер")
            
        self.log_message(f"Остановлен мониторинг скорости на клиенте {self.selected_client}")
            
    def on_speeds_data_received(self, client_id, adapter, data):
        """Обработка данных о скорости от клиента"""
        if self.selected_client != client_id or self.selected_adapter != adapter:
            return
            
        self.log_message(f"Получены данные о скорости для {adapter}: {data}")
            
        # Обновляем информацию о скорости в таблице
        if hasattr(self.window, "remoteInfoTable"):
            table = self.window.remoteInfoTable
            
            # Проверяем, есть ли уже строки для скорости
            speed_rows = []
            for row in range(table.rowCount()):
                param = table.item(row, 0).text()
                if "Загрузка" in param or "Отдача" in param:
                    speed_rows.append(row)
                    
            # Если строк для скорости нет, добавляем их
            if not speed_rows:
                # Добавляем строки для текущей скорости
                current_row = table.rowCount()
                table.setRowCount(current_row + 2)
                
                table.setItem(current_row, 0, QTableWidgetItem("Загрузка - текущая"))
                table.setItem(current_row, 1, QTableWidgetItem(f"{data['download']:.2f} Кбит/с"))
                
                table.setItem(current_row + 1, 0, QTableWidgetItem("Отдача - текущая"))
                table.setItem(current_row + 1, 1, QTableWidgetItem(f"{data['upload']:.2f} Кбит/с"))
                
                # Добавляем статистику
                if 'stats' in data:
                    stats = data['stats']
                    stat_row = current_row + 2
                    table.setRowCount(stat_row + 4)
                    
                    table.setItem(stat_row, 0, QTableWidgetItem("Загрузка - максимальная"))
                    table.setItem(stat_row, 1, QTableWidgetItem(f"{stats['max_download']:.2f} Кбит/с"))
                    
                    table.setItem(stat_row + 1, 0, QTableWidgetItem("Загрузка - средняя"))
                    table.setItem(stat_row + 1, 1, QTableWidgetItem(f"{stats['avg_download']:.2f} Кбит/с"))
                    
                    table.setItem(stat_row + 2, 0, QTableWidgetItem("Отдача - максимальная"))
                    table.setItem(stat_row + 2, 1, QTableWidgetItem(f"{stats['max_upload']:.2f} Кбит/с"))
                    
                    table.setItem(stat_row + 3, 0, QTableWidgetItem("Отдача - средняя"))
                    table.setItem(stat_row + 3, 1, QTableWidgetItem(f"{stats['avg_upload']:.2f} Кбит/с"))
            else:
                # Обновляем существующие строки
                for row in range(table.rowCount()):
                    param = table.item(row, 0).text()
                    if param == "Загрузка - текущая":
                        table.setItem(row, 1, QTableWidgetItem(f"{data['download']:.2f} Кбит/с"))
                    elif param == "Отдача - текущая":
                        table.setItem(row, 1, QTableWidgetItem(f"{data['upload']:.2f} Кбит/с"))
                    
                    # Обновляем статистику
                    if 'stats' in data:
                        stats = data['stats']
                        if param == "Загрузка - максимальная":
                            table.setItem(row, 1, QTableWidgetItem(f"{stats['max_download']:.2f} Кбит/с"))
                        elif param == "Загрузка - средняя":
                            table.setItem(row, 1, QTableWidgetItem(f"{stats['avg_download']:.2f} Кбит/с"))
                        elif param == "Отдача - максимальная":
                            table.setItem(row, 1, QTableWidgetItem(f"{stats['max_upload']:.2f} Кбит/с"))
                        elif param == "Отдача - средняя":
                            table.setItem(row, 1, QTableWidgetItem(f"{stats['avg_upload']:.2f} Кбит/с"))
        
        # Обновляем график скорости, если он есть
        try:
            if hasattr(self, "graph_builder"):
                # Обновляем график напрямую с одним значением
                self.log_message(f"Обновляем график: download={data['download']}, upload={data['upload']}")
                # Используем метод update_graph, который сам обработает точечные значения
                self.graph_builder.update_graph(data['download'], data['upload'])
        except Exception as e:
            self.log_message(f"Ошибка при обновлении графика: {e}")
            import traceback
            self.log_message(traceback.format_exc())
            
    def get_server_instance(self):
        """Получение экземпляра сервера для использования в других компонентах"""
        return self.server 