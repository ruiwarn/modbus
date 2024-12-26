from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QComboBox, 
                            QLabel, QPushButton, QGroupBox, QGridLayout,
                            QMessageBox, QSpinBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import serial
import serial.tools.list_ports
from serial.serialutil import SerialException

# 添加SerialMonitorThread类定义
class SerialMonitorThread(QThread):
    data_received = pyqtSignal(bytes)
    
    def __init__(self, serial_port):
        super().__init__()
        self.serial_port = serial_port
        self.running = False
        
    def run(self):
        self.running = True
        while self.running and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting:
                    data = self.serial_port.read(self.serial_port.in_waiting)
                    if data:
                        self.data_received.emit(data)
            except Exception as e:
                print(f"Serial monitoring error: {e}")
            self.msleep(10)  # 短暂休眠避免CPU占用过高
            
    def stop(self):
        self.running = False

# 添加 PortComboBox 类定义
class PortComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

    def showPopup(self):
        # 在显示下拉列表前刷新端口列表
        self.parent.refresh_ports()
        super().showPopup()

class SerialSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("串口设置")
        self.setModal(True)
        
        # 创建布局
        layout = QVBoxLayout()
        
        # 串口设置组
        settings_group = QGroupBox("串口参数")
        settings_layout = QGridLayout()
        
        # 串口选择
        self.port_combo = PortComboBox(self)
        settings_layout.addWidget(QLabel("串口:"), 0, 0)
        settings_layout.addWidget(self.port_combo, 0, 1)
        
        # 波特率选择
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(['9600', '19200', '38400', '57600', '115200'])
        settings_layout.addWidget(QLabel("波特率:"), 1, 0)
        settings_layout.addWidget(self.baud_combo, 1, 1)
        
        # 数据位
        self.data_bits_combo = QComboBox()
        self.data_bits_combo.addItems(['5', '6', '7', '8'])
        self.data_bits_combo.setCurrentText('8')
        settings_layout.addWidget(QLabel("数据位:"), 2, 0)
        settings_layout.addWidget(self.data_bits_combo, 2, 1)
        
        # 校验位
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(['无校验', '奇校验', '偶校验'])
        settings_layout.addWidget(QLabel("校验位:"), 3, 0)
        settings_layout.addWidget(self.parity_combo, 3, 1)
        
        # 停止位
        self.stop_bits_combo = QComboBox()
        self.stop_bits_combo.addItems(['1', '1.5', '2'])
        settings_layout.addWidget(QLabel("停止位:"), 4, 0)
        settings_layout.addWidget(self.stop_bits_combo, 4, 1)
        
        # 超时设置
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(0, 10000)
        self.timeout_spin.setValue(1000)
        self.timeout_spin.setSuffix(" ms")
        settings_layout.addWidget(QLabel("超时时间:"), 5, 0)
        settings_layout.addWidget(self.timeout_spin, 5, 1)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        # 打开/关闭串口按钮
        self.serial_btn = QPushButton("打开串口")
        self.serial_btn.clicked.connect(self.toggle_serial_port)
        self.serial_btn.setStyleSheet("""
            QPushButton {
                background-color: #107C10;
                color: white;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #138713;
            }
        """)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh_ports)
        
        button_layout.addWidget(self.serial_btn)
        button_layout.addWidget(refresh_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # 初始化串口列表
        self.refresh_ports()
        
        # 设置窗口大小
        self.setMinimumWidth(400)
    
    def toggle_serial_port(self):
        """切换串口打开/关闭状态"""
        if self.parent.serial_port is None or not self.parent.serial_port.is_open:
            # 尝试打开串口
            port = self.port_combo.currentText()
            baud_rate = int(self.baud_combo.currentText())
            data_bits = int(self.data_bits_combo.currentText())
            parity = {'无校验': serial.PARITY_NONE,
                     '奇校验': serial.PARITY_ODD,
                     '偶校验': serial.PARITY_EVEN}[self.parity_combo.currentText()]
            stop_bits = float(self.stop_bits_combo.currentText())
            timeout = self.timeout_spin.value() / 1000.0  # 转换为秒
            
            try:
                self.parent.serial_port = serial.Serial(
                    port=port,
                    baudrate=baud_rate,
                    bytesize=data_bits,
                    parity=parity,
                    stopbits=stop_bits,
                    timeout=timeout
                )
                
                # 创建并启动串口监听线程
                self.parent.serial_monitor = SerialMonitorThread(self.parent.serial_port)
                self.parent.serial_monitor.data_received.connect(self.parent.handle_received_data)
                self.parent.serial_monitor.start()
                
                # 更新按钮状态
                self.serial_btn.setText("关闭串口")
                self.serial_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #C42B1C;
                        color: white;
                        min-width: 120px;
                    }
                    QPushButton:hover {
                        background-color: #D43B2C;
                    }
                """)
                
                # 禁用设置控件
                self.port_combo.setEnabled(False)
                self.baud_combo.setEnabled(False)
                self.data_bits_combo.setEnabled(False)
                self.parity_combo.setEnabled(False)
                self.stop_bits_combo.setEnabled(False)
                self.timeout_spin.setEnabled(False)
                
                self.parent.log_message(f"串口 {port} 已成功打开")
                
            except SerialException as e:
                self.parent.log_message(f"串口错误: {str(e)}", "ERROR")
                return
                
        else:
            # 关闭串口
            if hasattr(self.parent, 'serial_monitor'):
                self.parent.serial_monitor.stop()
                self.parent.serial_monitor.wait()
            
            self.parent.serial_port.close()
            self.parent.serial_port = None
            
            # 更新按钮状态
            self.serial_btn.setText("打开串口")
            self.serial_btn.setStyleSheet("""
                QPushButton {
                    background-color: #107C10;
                    color: white;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #138713;
                }
            """)
            
            # 启��设置控件
            self.port_combo.setEnabled(True)
            self.baud_combo.setEnabled(True)
            self.data_bits_combo.setEnabled(True)
            self.parity_combo.setEnabled(True)
            self.stop_bits_combo.setEnabled(True)
            self.timeout_spin.setEnabled(True)
            
            self.parent.log_message("串口已关闭")
        
        # 保存配置
        self.parent.save_config()
    
    def refresh_ports(self):
        """刷新可用串口列表"""
        self.port_combo.clear()
        try:
            ports = serial.tools.list_ports.comports()
            for port in ports:
                self.port_combo.addItem(port.device)
        except Exception as e:
            self.parent.log_message(f"刷新串口列表失败: {str(e)}", "ERROR")
    
    def set_settings(self, settings):
        """设置串口参数"""
        if 'port' in settings:
            index = self.port_combo.findText(settings['port'])
            if index >= 0:
                self.port_combo.setCurrentIndex(index)
        
        if 'baudrate' in settings:
            index = self.baud_combo.findText(str(settings['baudrate']))
            if index >= 0:
                self.baud_combo.setCurrentIndex(index)
        
        if 'bytesize' in settings:
            index = self.data_bits_combo.findText(str(settings['bytesize']))
            if index >= 0:
                self.data_bits_combo.setCurrentIndex(index)
        
        if 'parity' in settings:
            parity_map = {
                serial.PARITY_NONE: '无校验',
                serial.PARITY_ODD: '奇校验',
                serial.PARITY_EVEN: '偶校验'
            }
            if settings['parity'] in parity_map:
                index = self.parity_combo.findText(parity_map[settings['parity']])
                if index >= 0:
                    self.parity_combo.setCurrentIndex(index)
        
        if 'stopbits' in settings:
            index = self.stop_bits_combo.findText(str(settings['stopbits']))
            if index >= 0:
                self.stop_bits_combo.setCurrentIndex(index)
        
        if 'timeout' in settings:
            self.timeout_spin.setValue(int(settings['timeout'] * 1000))  # 转换为毫秒
        
        # 更新按钮状态
        if self.parent.serial_port and self.parent.serial_port.is_open:
            self.serial_btn.setText("关闭串口")
            self.serial_btn.setStyleSheet("""
                QPushButton {
                    background-color: #C42B1C;
                    color: white;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #D43B2C;
                }
            """)
            self.port_combo.setEnabled(False)
            self.baud_combo.setEnabled(False)
            self.data_bits_combo.setEnabled(False)
            self.parity_combo.setEnabled(False)
            self.stop_bits_combo.setEnabled(False)
            self.timeout_spin.setEnabled(False) 