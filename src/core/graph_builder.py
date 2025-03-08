from PyQt6.QtWidgets import QVBoxLayout
import pyqtgraph as pg
from pyqtgraph import mkPen

class GraphBuilder:
    def __init__(self, graph_widget):
        self.graph = graph_widget
        self.configure_graph()
        self.time_axis = []
        self.max_points = 60
        
        # Определяем цвета
        self.download_color = (0, 100, 255)  # Синий
        self.upload_color = (255, 50, 50)    # Красный
        
        # Создаем перья для рисования
        self.download_pen = pg.mkPen(color=self.download_color, width=2)
        self.upload_pen = pg.mkPen(color=self.upload_color, width=2)
        
        # Создаем кривые
        self.download_curve = self.graph.plot(pen=self.download_pen, name='Загрузка')
        self.upload_curve = self.graph.plot(pen=self.upload_pen, name='Отдача')
        
        # Состояние видимости
        self.download_visible = True
        self.upload_visible = True

        # Данные для графиков
        self.download_speeds = []
        self.upload_speeds = []

    def configure_graph(self):
        """Настройка графика"""
        self.graph.setBackground(None)
        self.graph.showGrid(x=True, y=True, alpha=0.3)
        self.graph.setLabel('left', 'Скорость', units='КБ/с')
        self.graph.setLabel('bottom', 'Время', units='с')
        self.graph.getAxis('bottom').setPen((50, 50, 50))
        self.graph.getAxis('left').setPen((50, 50, 50))
        self.graph.setMouseEnabled(x=True, y=True)
        
        # Добавляем и настраиваем легенду
        self.graph.addLegend(offset=(10, 10))  # Отступ от верхнего левого угла
        self.graph.getPlotItem().legend.setScale(0.9)  # Немного уменьшаем размер легенды

    def update_graph(self, download_speeds, upload_speeds):
        """Обновление графика"""
        print(f"Вызван update_graph с данными:")
        print(f"download_speeds: {download_speeds}")
        print(f"upload_speeds: {upload_speeds}")
        
        if not download_speeds or not upload_speeds:
            print("Нет данных для обновления графика")
            return
            
        # Сохраняем данные
        self.download_speeds = download_speeds
        self.upload_speeds = upload_speeds
            
        # Обновляем временную ось
        self.time_axis = list(range(len(download_speeds)))
        print(f"Временная ось: {self.time_axis}")
        
        # Обновляем кривые если они видимы
        if self.download_visible:
            print("Обновляем кривую загрузки")
            self.download_curve.setData(self.time_axis, download_speeds)
            
        if self.upload_visible:
            print("Обновляем кривую отдачи")
            self.upload_curve.setData(self.time_axis, upload_speeds)
            
        print("Обновление графика завершено")

    def set_download_visible(self, visible):
        """Устанавливает видимость линии загрузки"""
        self.download_visible = visible
        self.download_curve.setVisible(visible)

    def set_upload_visible(self, visible):
        """Устанавливает видимость линии отдачи"""
        self.upload_visible = visible
        self.upload_curve.setVisible(visible)

    def clear_graphs(self):
        """Очищает графики и сбрасывает данные"""
        print("Очистка графиков в GraphBuilder...")
        # Очищаем данные
        self.download_speeds = []
        self.upload_speeds = []
        self.time_axis = []
        
        # Очищаем кривые
        self.download_curve.setData([], [])
        self.upload_curve.setData([], [])
        
        # Обновляем отображение
        self.graph.replot()
        print("Графики очищены") 