from PyQt6.QtWidgets import QVBoxLayout
import pyqtgraph as pg
from pyqtgraph import mkPen
import traceback
import sys

class GraphBuilder:
    def __init__(self, graph_widget):
        try:
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
            
            # Проверяем, что виджет графика правильного типа
            print(f"Тип виджета графика: {type(self.graph)}")
            
            # Создаем кривые
            self.download_curve = self.graph.plot(pen=self.download_pen, name='Загрузка')
            self.upload_curve = self.graph.plot(pen=self.upload_pen, name='Отдача')
            
            # Состояние видимости
            self.download_visible = True
            self.upload_visible = True

            # Данные для графиков
            self.download_speeds = []
            self.upload_speeds = []
            
            print("GraphBuilder успешно инициализирован")
        except Exception as e:
            print(f"ОШИБКА при инициализации GraphBuilder: {e}")
            traceback.print_exc()

    def configure_graph(self):
        """Настройка графика"""
        try:
            self.graph.setBackground(None)
            self.graph.showGrid(x=True, y=True, alpha=0.3)
            self.graph.setLabel('left', 'Скорость', units='КБ/с')
            self.graph.setLabel('bottom', 'Время', units='с')
            self.graph.getAxis('bottom').setPen((50, 50, 50))
            self.graph.getAxis('left').setPen((50, 50, 50))
            self.graph.setMouseEnabled(x=True, y=True)
            print("График успешно настроен")
        except Exception as e:
            print(f"ОШИБКА при настройке графика: {e}")
            traceback.print_exc()

    def update_graph(self, download_speeds, upload_speeds):
        """Обновление графика"""
        try:
            print(f"Вызван update_graph с данными:")
            if isinstance(download_speeds, list):
                print(f"download_speeds: {download_speeds[:5]}... (всего {len(download_speeds)} точек)")
            else:
                print(f"download_speeds: {download_speeds} (тип: {type(download_speeds)})")
            
            if isinstance(upload_speeds, list):
                print(f"upload_speeds: {upload_speeds[:5]}... (всего {len(upload_speeds)} точек)")
            else:
                print(f"upload_speeds: {upload_speeds} (тип: {type(upload_speeds)})")
            
            # Если передано одно значение, а не список - добавляем его к существующим данным
            if not isinstance(download_speeds, list) and not isinstance(upload_speeds, list):
                self.download_speeds.append(download_speeds)
                self.upload_speeds.append(upload_speeds)
                
                # Ограничиваем размер списков
                if len(self.download_speeds) > self.max_points:
                    self.download_speeds.pop(0)
                    self.upload_speeds.pop(0)
                    
                download_speeds = self.download_speeds
                upload_speeds = self.upload_speeds
            
            if not download_speeds or not upload_speeds:
                print("Нет данных для обновления графика")
                return
                
            # Обновляем временную ось
            self.time_axis = list(range(len(download_speeds)))
            print(f"Временная ось: {self.time_axis[:5]}... (всего {len(self.time_axis)} точек)")
            
            # Обновляем кривые если они видимы
            if self.download_visible:
                print("Обновляем кривую загрузки")
                self.download_curve.setData(self.time_axis, download_speeds)
                
            if self.upload_visible:
                print("Обновляем кривую отдачи")
                self.upload_curve.setData(self.time_axis, upload_speeds)
                
            print("График успешно обновлен")
        except Exception as e:
            print(f"ОШИБКА при обновлении графика: {e}")
            traceback.print_exc()

    def set_download_visible(self, visible):
        """Установка видимости кривой загрузки"""
        self.download_visible = visible
        self.download_curve.setVisible(visible)

    def set_upload_visible(self, visible):
        """Установка видимости кривой отдачи"""
        self.upload_visible = visible
        self.upload_curve.setVisible(visible)

    def clear_graphs(self):
        """Очистка графиков"""
        try:
            self.download_speeds = []
            self.upload_speeds = []
            self.time_axis = []
            self.download_curve.setData([], [])
            self.upload_curve.setData([], [])
            print("Графики очищены")
        except Exception as e:
            print(f"ОШИБКА при очистке графиков: {e}")
            traceback.print_exc() 