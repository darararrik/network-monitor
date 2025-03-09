from PyQt6.QtWidgets import QTableWidgetItem, QHeaderView, QAbstractItemView
from PyQt6.QtCore import Qt, QTimer
from src.core.graph_builder import GraphBuilder
from src.core.network_client import NetworkClient

class RemoteMonitoring:
    def __init__(self, window, network_monitor):
        self.window = window
        self.network_monitor = network_monitor
        self.remote_client = None
        self.remote_connected = False
        self.remote_is_measuring = False
        self.remote_timer = None
        self.remote_graph_builder = None

    def setup_remote_monitoring(self):
        """Настройка удаленного мониторинга"""
        print("Настройка удаленного мониторинга...")
        
        # Настраиваем таблицу информации о подключении
        self.setup_remote_table()
        
        # # Настраиваем график скорости
        # self.setup_remote_graph()
        
        # Настраиваем начальные значения
        if hasattr(self.window, "remoteIPInput"):
            self.window.remoteIPInput.setText("127.0.0.1")
        if hasattr(self.window, "remotePortInput"):
            self.window.remotePortInput.setText("5000")
        if hasattr(self.window, "remoteComputerLabel"):
            self.window.remoteComputerLabel.setText("Не подключено")
        
        # Настраиваем кнопку подключения
        if hasattr(self.window, "connectRemoteButton"):
            self.window.connectRemoteButton.clicked.connect(self.connect_to_remote)

        # Настраиваем кнопку ping
        if hasattr(self.window, "pingRemoteButton"):
            self.window.pingRemoteButton.clicked.connect(self.ping_remote)
        
        # Подключаем обработчик выбора адаптера
        if hasattr(self.window, "remoteAdapterList"):
            self.window.remoteAdapterList.currentTextChanged.connect(self.on_remote_adapter_selected)
            
        # Настраиваем таблицу для удаленного мониторинга
        if hasattr(self.window, "remoteInfoTable"):
            self.setup_remote_table()

        # Подключаем кнопку измерения скорости
        if hasattr(self.window, "remoteMeasureSpeedButton"):
            self.window.remoteMeasureSpeedButton.clicked.connect(self.toggle_remote_measurement)
            self.remote_is_measuring = False

        # Подключаем кнопку очистки графиков
        if hasattr(self.window, "remoteClearGraphs"):
            self.window.remoteClearGraphs.clicked.connect(self.clear_remote_graphs)

        # Инициализируем таймер для удаленных измерений
        self.remote_timer = QTimer()
        self.remote_timer.timeout.connect(self.update_remote_measurements)

        # Инициализируем график для удаленного режима
        if hasattr(self.window, "remoteGraphWidget") and self.window.remoteGraphWidget is not None:
            print("Инициализация графика для удаленного режима...")
            self.remote_graph_builder = GraphBuilder(self.window.remoteGraphWidget)
            print("График для удаленного режима инициализирован")
        else:
            print("ОШИБКА: remoteGraphWidget не найден в UI!")

        # Подключаем чекбоксы для удаленного режима
        if hasattr(self.window, "remoteHideDownload"):
            self.window.remoteHideDownload.stateChanged.connect(self.on_remote_hide_download_changed)
        if hasattr(self.window, "remoteHideUpload"):
            self.window.remoteHideUpload.stateChanged.connect(self.on_remote_hide_upload_changed)
        print("Настройка удаленного мониторинга завершена")

    def setup_remote_table(self):
        """Настройка таблицы для отображения информации об удаленных адаптерах"""
        if not hasattr(self.window, "remoteInfoTable"):
            return
            
        # Задаем параметры таблицы
        table = self.window.remoteInfoTable
        table.setColumnCount(2)
        table.setRowCount(15)
        
        # Добавляем заголовки
        table.setHorizontalHeaderLabels(['Параметр', 'Значение'])
        
        # Задаем параметры для таблицы
        parameters = [
            'ID адаптера', 'Описание', 'Тип интерфейса',
            'IP адрес', 'MAC адрес', 'Скорость адаптера',
            'MTU', 'Статус', 'Время замера',
            'Загрузка - текущая', 'Загрузка - максимальная',
            'Загрузка - средняя', 'Отдача - текущая',
            'Отдача - максимальная', 'Отдача - средняя'
        ]
        
        # Заполняем таблицу начальными значениями
        for i, param in enumerate(parameters):
            item = QTableWidgetItem(param)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(i, 0, item)
            
            value_item = QTableWidgetItem('-')
            value_item.setFlags(value_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(i, 1, value_item)
        
        # Настраиваем отображение заголовков
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        # Отключаем выбор ячеек
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)

    def connect_to_remote(self):
        """Подключение к удаленному компьютеру"""
        # Проверяем, что у нас еще нет активного подключения
        if self.remote_connected:
            self.disconnect_from_remote()
            return
        
        try:
            
            # Получаем IP и порт из полей ввода
            ip = self.window.remoteIPInput.text() if hasattr(self.window, "remoteIPInput") else "127.0.0.1"
            port = 5000
            try:
                port = int(self.window.remotePortInput.text()) if hasattr(self.window, "remotePortInput") else 5000
            except ValueError:
                port = 5000
            
            # Создаем клиент для подключения
            self.remote_client = NetworkClient(ip, port)
            
            # Подключаемся
            if self.remote_client.connect():
                self.remote_connected = True
                
                # Обновляем интерфейс
                if hasattr(self.window, "connectRemoteButton"):
                    self.window.connectRemoteButton.setText("Отключиться")
                
                # Загружаем список адаптеров
                self.load_remote_adapters()
                
                # Обновляем информацию о компьютере
                self.get_remote_computer_name()
            else:
                print("Не удалось подключиться к удаленному компьютеру")
                if hasattr(self.window, "remoteComputerLabel"):
                    self.window.remoteComputerLabel.setText("Не удалось подключиться")
        except Exception as e:
            print(f"Ошибка при подключении: {e}")
            if hasattr(self.window, "remoteComputerLabel"):
                self.window.remoteComputerLabel.setText(f"Ошибка: {str(e)}")

    def disconnect_from_remote(self):
        """Отключение от удаленного компьютера"""
        # Проверяем, есть ли активное подключение
        if not self.remote_connected:
            return
        
        try:
            # Если идет измерение, останавливаем его
            if self.remote_is_measuring:
                self.stop_remote_measurement()
            
            # Отключаемся
            self.remote_client.disconnect()
            self.remote_connected = False
            
            # Обновляем интерфейс
            if hasattr(self.window, "connectRemoteButton"):
                self.window.connectRemoteButton.setText("Подключиться")
            
            # Очищаем список адаптеров
            if hasattr(self.window, "remoteAdapterList"):
                self.window.remoteAdapterList.clear()
            
            # Очищаем информацию о компьютере
            if hasattr(self.window, "remoteComputerLabel"):
                self.window.remoteComputerLabel.setText("Не подключено")
        except Exception as e:
            print(f"Ошибка при отключении: {e}")

    def load_remote_adapters(self):
        """Загрузка списка адаптеров с удаленного компьютера"""
        if not self.remote_connected:
            return
        
        # Получаем список адаптеров
        adapters = self.remote_client.get_adapters()
        
        # Заполняем выпадающий список
        if hasattr(self.window, "remoteAdapterList"):
            self.window.remoteAdapterList.clear()
            if adapters:
                self.window.remoteAdapterList.addItems(adapters)

    def get_remote_computer_name(self):
        """Получение имени удаленного компьютера"""
        if not self.remote_connected:
            return
        
        # Обновляем информацию о компьютере
        if hasattr(self.window, "remoteComputerLabel"):
            self.window.remoteComputerLabel.setText(f"Подключено к: {self.remote_client.host}")

    def on_remote_adapter_selected(self, adapter_name):
        """Обработчик выбора адаптера на удаленном компьютере"""
        if not self.remote_connected:
            return

        adapter_info = self.remote_client.get_adapter_info(adapter_name) or {}
        
        # Обновляем информацию в таблице
        if hasattr(self.window, "remoteInfoTable"):
            self.window.remoteInfoTable.item(0, 1).setText(adapter_info.get('id', '-'))
            self.window.remoteInfoTable.item(1, 1).setText(adapter_info.get('description', '-'))
            self.window.remoteInfoTable.item(2, 1).setText(adapter_info.get('interface_type', '-'))
            self.window.remoteInfoTable.item(3, 1).setText(adapter_info.get('ip', '-'))
            self.window.remoteInfoTable.item(4, 1).setText(adapter_info.get('mac', '-'))
            self.window.remoteInfoTable.item(5, 1).setText(adapter_info.get('speed', '-'))
            self.window.remoteInfoTable.item(6, 1).setText(adapter_info.get('mtu', '-'))
            self.window.remoteInfoTable.item(7, 1).setText(adapter_info.get('status', '-'))
            
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

        current_item = self.window.remoteAdapterList.currentItem() if hasattr(self.window, "remoteAdapterList") else None
        if not current_item:
            return

        adapter_name = current_item.text()
        if not adapter_name:
            return
            
        # Получаем время измерения
        hours = int(self.window.remoteHoursInput.text() or "0") if hasattr(self.window, "remoteHoursInput") else 0
        minutes = int(self.window.remoteMinutesInput.text() or "0") if hasattr(self.window, "remoteMinutesInput") else 1
        seconds = int(self.window.remoteSecondsInput.text() or "0") if hasattr(self.window, "remoteSecondsInput") else 0
        
        time_in_seconds = hours * 3600 + minutes * 60 + seconds
        
        # Запускаем измерение на удаленном компьютере
        self.remote_client.start_measurement(adapter_name)
        
        # Устанавливаем флаг измерения
        self.remote_is_measuring = True
        
        # Очищаем данные
        self.remote_client.download_speeds = []
        self.remote_client.upload_speeds = []
        
        # Обновляем кнопку
        if hasattr(self.window, "remoteMeasureSpeedButton"):
            self.window.remoteMeasureSpeedButton.setText("Остановить")
        
        # Запускаем таймер для обновления данных
        self.remote_timer.start(1000)

    def stop_remote_measurement(self):
        """Останавливает замер скорости на удаленном компьютере"""
        if not self.remote_connected:
            return
            
        # Останавливаем измерение на удаленном компьютере
        self.remote_client.stop_measurement()
        
        # Сбрасываем флаг измерения
        self.remote_is_measuring = False
        
        # Останавливаем таймер
        self.remote_timer.stop()
        
        # Обновляем кнопку
        if hasattr(self.window, "remoteMeasureSpeedButton"):
            self.window.remoteMeasureSpeedButton.setText("Начать")
        
        # Сбрасываем данные
        if hasattr(self.window, "remoteMeasurementTime"):
            self.window.remoteMeasurementTime.setText("00:00:00")
        
        # Очищаем информацию о скорости в таблице
        if hasattr(self.window, "remoteInfoTable"):
            for i in range(8, 15):
                self.window.remoteInfoTable.item(i, 1).setText('-')

    def update_remote_measurements(self):
        """Обновляет данные о скорости с удаленного компьютера"""
        if not self.remote_connected or not self.remote_is_measuring:
            return
            
        # Получаем текущую скорость
        speed_data = self.remote_client.get_speeds()
        print("Получены данные от сервера:", speed_data)  # Отладочная информация
        if not speed_data:
            return
            
        # Извлекаем данные о скорости
        download = speed_data.get('download', 0)
        upload = speed_data.get('upload', 0)
        
        # Сохраняем данные для графика
        self.remote_client.download_speeds.append(download)
        self.remote_client.upload_speeds.append(upload)
        
        # Обновляем график
        if self.remote_graph_builder:
            self.remote_graph_builder.update_graph(self.remote_client.download_speeds, self.remote_client.upload_speeds)
        
        # Обновляем информацию в таблице
        if hasattr(self.window, "remoteInfoTable"):
            # Обновляем время замера
            time_value = speed_data.get('time', '-')
            print(f"Обновляем время замера: {time_value}")  # Отладочная информация
            self.window.remoteInfoTable.item(8, 1).setText(time_value)
            
            # Обновляем скорость загрузки
            self.window.remoteInfoTable.item(9, 1).setText(f"{download:.2f} KB/s")
            
            # Обновляем максимальную скорость загрузки
            max_download = max(self.remote_client.download_speeds)
            self.window.remoteInfoTable.item(10, 1).setText(f"{max_download:.2f} KB/s")
            
            # Обновляем среднюю скорость загрузки
            avg_download = sum(self.remote_client.download_speeds) / len(self.remote_client.download_speeds)
            self.window.remoteInfoTable.item(11, 1).setText(f"{avg_download:.2f} KB/s")
            
            # Обновляем скорость отдачи
            self.window.remoteInfoTable.item(12, 1).setText(f"{upload:.2f} KB/s")
            
            # Обновляем максимальную скорость отдачи
            max_upload = max(self.remote_client.upload_speeds)
            self.window.remoteInfoTable.item(13, 1).setText(f"{max_upload:.2f} KB/s")
            
            # Обновляем среднюю скорость отдачи
            avg_upload = sum(self.remote_client.upload_speeds) / len(self.remote_client.upload_speeds)
            self.window.remoteInfoTable.item(14, 1).setText(f"{avg_upload:.2f} KB/s")

    def on_remote_hide_download_changed(self, state):
        """Обработчик изменения состояния чекбокса скрытия графика загрузки"""
        if self.remote_graph_builder:
            self.remote_graph_builder.set_download_visible(not bool(state))

    def on_remote_hide_upload_changed(self, state):
        """Обработчик изменения состояния чекбокса скрытия графика отдачи"""
        if self.remote_graph_builder:
            self.remote_graph_builder.set_upload_visible(not bool(state))

    def clear_remote_graphs(self):
        """Очищает графики и данные для удаленного мониторинга"""
        # Очищаем данные
        self.remote_client.download_speeds = []
        self.remote_client.upload_speeds = []
        
        # Очищаем график
        if self.remote_graph_builder:
            self.remote_graph_builder.clear_graphs()

    def ping_remote(self):
        """Пинг удаленного компьютера"""
        import subprocess
        import platform
        
        # Получаем IP из поля ввода
        ip = self.window.remoteIPInput.text() if hasattr(self.window, "remoteIPInput") else "127.0.0.1"
        
        # Определяем команду пинга в зависимости от ОС
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, '4', ip]
        
        try:
            # Запускаем процесс пинга
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            # Обрабатываем результат
            result = stdout.decode('cp866' if platform.system().lower() == 'windows' else 'utf-8')
            
            # Определяем успешность пинга
            if "Reply from" in result or "bytes from" in result:
                status = "Пинг успешен!"
            else:
                status = "Пинг не удался!"
                
            # Отображаем результат в интерфейсе
            if hasattr(self.window, "remoteComputerLabel"):
                self.window.remoteComputerLabel.setText(f"{status} ({ip})")
                
            # Возвращаем подробный результат для возможного отображения
            return result
            
        except Exception as e:
            if hasattr(self.window, "remoteComputerLabel"):
                self.window.remoteComputerLabel.setText(f"Ошибка пинга: {str(e)}")
            return None

