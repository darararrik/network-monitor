# src/ui/measurement_management.py

from PyQt6.QtCore import QTimer

class MeasurementManagement:
    def __init__(self, window):
        self.window = window
        self.is_measuring = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_measurements)

    def toggle_measurement(self):
        """Включает и выключает замер скорости"""
        if self.is_measuring:
            self.stop_measurement()
        else:
            self.start_measurement()

    def start_measurement(self):
        """Запускает замер скорости"""
        self.window.network_monitor.start_measurement(self.window.selected_adapter)
        self.is_measuring = True
        self.window.measureSpeedButton.setText("Стоп")
        self.timer.start(1000)  # Обновляем каждую секунду
        self.window.elapsed_time = 0  # Инициализируем время

    def stop_measurement(self):
        """Останавливает замер скорости"""
        self.window.network_monitor.stop_measurement()
        self.is_measuring = False
        self.window.measureSpeedButton.setText("Старт")
        self.timer.stop()

    def update_measurements(self):
        """Обновляет все измерения (время и график)"""
        if self.window.selected_adapter:
            speeds = self.window.network_monitor.get_current_speeds()
            if speeds:
                 # Обновляем график
                self.window.graph_builder.update_graph(
                    self.window.network_monitor.download_speeds,
                    self.window.network_monitor.upload_speeds
                )
                self.update_table(speeds)
                self.window.elapsed_time += 1  # Увеличиваем время на 1 секунду
                self.window.adapterInfoTable.item(8, 1).setText(f"{self.window.elapsed_time} сек")

                # Проверяем, не истекло ли время
                if self.window.target_time > 0 and self.window.elapsed_time >= self.window.target_time:
                    self.stop_measurement()  # Останавливаем замер, если время истекло

    def update_table(self, speeds):
        """Обновляет значения скорости в таблице"""
        stats = speeds['stats']
        self.window.adapterInfoTable.item(9, 1).setText(f"{speeds['download']:.2f} КБ/с")
        self.window.adapterInfoTable.item(10, 1).setText(f"{stats['max_download']:.2f} КБ/с")
        self.window.adapterInfoTable.item(11, 1).setText(f"{stats['avg_download']:.2f} КБ/с")
        self.window.adapterInfoTable.item(12, 1).setText(f"{speeds['upload']:.2f} КБ/с")
        self.window.adapterInfoTable.item(13, 1).setText(f"{stats['max_upload']:.2f} КБ/с")
        self.window.adapterInfoTable.item(14, 1).setText(f"{stats['avg_upload']:.2f} КБ/с")

    def clear_graphs(self):
        """Очищает графики и сбрасывает статистику"""
        try:
            # Очищаем графики
            if hasattr(self.window, "graph_builder"):
                self.window.graph_builder.clear_graphs()
            
            # Сбрасываем значения в таблице
            self.window.adapterInfoTable.item(8, 1).setText('-')  # Время
            for i in range(9, 15):  # Скорости
                self.window.adapterInfoTable.item(i, 1).setText('-')
            
            # Сбрасываем счетчик времени
            self.window.elapsed_time = 0
            
                
            # Очищаем данные в network_monitor
            if hasattr(self.window, "network_monitor"):
                self.window.network_monitor.download_speeds = []
                self.window.network_monitor.upload_speeds = []
                self.window.network_monitor.max_download = 0
                self.window.network_monitor.max_upload = 0
                self.window.network_monitor.total_download = 0
                self.window.network_monitor.total_upload = 0
                self.window.network_monitor.measurement_count = 0
        except Exception as e:
            print(f"Ошибка при очистке графиков: {e}")
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
