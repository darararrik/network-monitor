import psutil
import wmi  # Добавляем импорт WMI

class NetworkMonitor:
    def __init__(self):
        self.selected_adapter = None
        self.download_speeds = []
        self.upload_speeds = []
        self.prev_recv = 0
        self.prev_sent = 0
        self.max_download = 0
        self.max_upload = 0
        self.total_download = 0
        self.total_upload = 0
        self.measurement_count = 0
        # Инициализируем WMI
        try:
            self.wmi = wmi.WMI()
        except:
            self.wmi = None

    def get_adapters(self):
        """Возвращает список доступных сетевых адаптеров"""
        return list(psutil.net_if_addrs().keys())

    def get_adapter_description(self, adapter_name):
        """Получает подробное описание адаптера через WMI"""
        if not self.wmi:
            return adapter_name
            
        try:
            # Получаем все сетевые адаптеры через WMI
            for adapter in self.wmi.Win32_NetworkAdapter():
                # Проверяем, совпадает ли имя адаптера
                if adapter.NetConnectionID == adapter_name:
                    return adapter.Name or adapter.Description or adapter_name
            return adapter_name
        except:
            return adapter_name

    def get_adapter_info(self, adapter_name):
        """Получает информацию о сетевом адаптере"""
        addresses = psutil.net_if_addrs().get(adapter_name, [])
        stats = psutil.net_if_stats().get(adapter_name)
        
        info = {
            'id': adapter_name,  # Используем имя адаптера как ID
            'description': self.get_adapter_description(adapter_name),  # Получаем подробное описание
            'interface_type': 'Ethernet',  # По умолчанию предполагаем Ethernet
            'ip': '',
            'mac': '',
            'speed': '',
            'mtu': '',
            'status': ''
        }
        
        for addr in addresses:
            if addr.family.name == "AF_INET":
                info['ip'] = addr.address
            elif addr.family.name in ["AF_PACKET", "AF_LINK"]:
                info['mac'] = addr.address

        if stats:
            info['speed'] = f"{stats.speed} Мбит/с"
            info['mtu'] = f"{stats.mtu} байт"
            info['status'] = "Активен" if stats.isup else "Неактивен"
            
        # Определяем тип интерфейса на основе имени
        if 'wi' in adapter_name.lower() or 'wlan' in adapter_name.lower():
            info['interface_type'] = 'Wi-Fi'
        elif 'bluetooth' in adapter_name.lower():
            info['interface_type'] = 'Bluetooth'
        elif 'vpn' in adapter_name.lower():
            info['interface_type'] = 'VPN'
        elif 'loopback' in adapter_name.lower():
            info['interface_type'] = 'Loopback'
            
        return info

    def start_measurement(self, adapter_name):
        """Начинает измерение скорости"""
        self.selected_adapter = adapter_name
        self.download_speeds = []
        self.upload_speeds = []
        self.prev_recv = psutil.net_io_counters(pernic=True)[adapter_name].bytes_recv
        self.prev_sent = psutil.net_io_counters(pernic=True)[adapter_name].bytes_sent
        self.max_download = 0
        self.max_upload = 0
        self.total_download = 0
        self.total_upload = 0
        self.measurement_count = 0

    def stop_measurement(self):
        """Останавливает измерение скорости"""
        self.selected_adapter = None

    def get_current_speeds(self):
        """Получает текущую скорость сети"""
        if not self.selected_adapter:
            return None

        net_io = psutil.net_io_counters(pernic=True).get(self.selected_adapter)
        if not net_io:
            return None

        recv_speed = (net_io.bytes_recv - self.prev_recv) / 1024  # КБ/с
        sent_speed = (net_io.bytes_sent - self.prev_sent) / 1024  # КБ/с

        self.prev_recv = net_io.bytes_recv
        self.prev_sent = net_io.bytes_sent

        # Обновление статистики
        self.max_download = max(self.max_download, recv_speed)
        self.max_upload = max(self.max_upload, sent_speed)
        self.total_download += recv_speed
        self.total_upload += sent_speed
        self.measurement_count += 1

        # Добавление в историю
        self.download_speeds.append(recv_speed)
        self.upload_speeds.append(sent_speed)

        # Ограничение количества точек
        max_points = 60
        if len(self.download_speeds) > max_points:
            self.download_speeds.pop(0)
            self.upload_speeds.pop(0)

        return {
            'download': recv_speed,
            'upload': sent_speed,
            'stats': {
                'max_download': self.max_download,
                'max_upload': self.max_upload,
                'avg_download': self.total_download / self.measurement_count,
                'avg_upload': self.total_upload / self.measurement_count
            }
        } 