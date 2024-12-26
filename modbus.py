import sys
import json
import serial
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QComboBox, QTextEdit, QPushButton, 
                            QLabel, QGroupBox, QGridLayout, QMenuBar, QMenu, QAction, QMessageBox, QLineEdit, QDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon, QPixmap
from serial.serialutil import SerialException
import datetime
from serial_settings_dialog import SerialSettingsDialog
from protocol_settings_dialog import ProtocolSettingsDialog
import os
from config_manager import ConfigManager
from serial_handler import SerialHandler
from modbus_parser import ModbusParser
from internal_variables import InternalVariables

logger = logging.getLogger(__name__)

# 在文件顶部的 import 部分添加
import base64
from PyQt5.QtGui import QIcon, QPixmap

# 在 ModbusSimulator 类定义之前添加图标数据
ICON_BASE64 = """
PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAg
d2lkdGg9IjMyIgogICBoZWlnaHQ9IjMyIgogICB2aWV3Qm94PSIwIDAgOC40NjY2NjY1IDguNDY2NjY2OSIK
ICAgdmVyc2lvbj0iMS4xIj4KICA8Y2lyY2xlCiAgICAgc3R5bGU9ImZpbGw6IzAwNzhkNztmaWxsLW9wYWNp
dHk6MSIKICAgICBjeD0iNC4yMzMzMzMzIgogICAgIGN5PSI0LjIzMzMzMzQiCiAgICAgcj0iMy4xNzUiIC8+
CiAgPHBhdGgKICAgICBzdHlsZT0iZmlsbDojZmZmZmZmO2ZpbGwtb3BhY2l0eToxIgogICAgIGQ9Ik0gMy4x
NzUsNC4yMzMzMzM0IEggNS4yOTE2NjY2IFYgNS4yOTE2NjY4IEggMy4xNzUgWiIgLz4KICA8cGF0aAogICAg
IHN0eWxlPSJmaWxsOiNmZmZmZmY7ZmlsbC1vcGFjaXR5OjEiCiAgICAgZD0iTSA0LjIzMzMzMzMsNS4yOTE2
NjY4IFYgMy4xNzUwMDAxIEggNS4yOTE2NjY2IFYgNS4yOTE2NjY4IFoiIC8+Cjwvc3ZnPgo=
"""

# 在ModbusSimulator类中添加自定义的ComboBox类
class PortComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

    def showPopup(self):
        # 在显示下拉列表前刷口表
        self.parent.refresh_com_ports()
        super().showPopup()

class ModbusSimulator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modbus Protocol Simulator")
        
        # Initialize serial port attribute
        self.serial_port = None
        
        # 首先初始化关键属性
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        
        # 设置应用图标
        icon_data = base64.b64decode(ICON_BASE64)
        pixmap = QPixmap()
        pixmap.loadFromData(icon_data)
        self.setWindowIcon(QIcon(pixmap))
        
        self.setMinimumSize(1600, 1000)
        
        # Set stylesheet for the entire application
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QGroupBox {
                font-size: 12pt;
                font-weight: bold;
                border: 2px solid #c0c0c0;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #0078D7;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 11pt;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #1084E0;
            }
            QPushButton:pressed {
                background-color: #006CC1;
            }
            QComboBox {
                padding: 6px;
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                min-width: 200px;
                font-size: 11pt;
            }
            QLabel {
                font-size: 11pt;
            }
            QTextEdit {
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                padding: 5px;
                font-size: 11pt;
                min-height: 200px;
            }
        """)
        
        # Initialize main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # 创建菜单栏
        self._create_menu_bar()
        
        # 初始化各个模块
        self.config_manager = ConfigManager()
        self.serial_handler = SerialHandler() 
        self.modbus_parser = ModbusParser()
        
        # 加载配置
        self.config_manager.load_config()
        self.config_manager.load_protocols()
        
        # 按顺序加载配置
        self.config_manager.load_protocols()  # 先加载协议
        self.load_config()    # 再加载配置
        
        # Create UI components
        self._create_protocol_section(layout)
        self._create_communication_section(layout)
        
        # 应用配置
        self.apply_last_config()
        
        # Set light theme
        self.set_light_theme()

    def _create_protocol_section(self, parent_layout):
        group = QGroupBox("内部变量")
        layout = QGridLayout()
        layout.setSpacing(15)
        
        # 创建内部变量管理器实例
        self.internal_vars = InternalVariables()
        self.internal_vars.add_observer(self)  # 添加自身为观察者
        
        # 创建变量显示和编辑控件
        self.var_widgets = {}
        row = 0
        
        # 时间戳显示（只读）
        timestamp_label = QLabel("时间戳:")
        self.timestamp_display = QLineEdit()
        self.timestamp_display.setReadOnly(True)
        layout.addWidget(timestamp_label, row, 0)
        layout.addWidget(self.timestamp_display, row, 1)
        row += 1
        
        # 创建其他变量的输入控件
        for meta in self.internal_vars.get_variable_metadata():
            label = QLabel(f"{meta['display_name']} ({meta['unit']}):")
            input_widget = QLineEdit()
            input_widget.setPlaceholderText(str(meta['placeholder']))
            layout.addWidget(label, row, 0)
            layout.addWidget(input_widget, row, 1)
            self.var_widgets[meta['name']] = input_widget
            row += 1
        
        # 更新按钮
        update_btn = QPushButton("更新变量")
        update_btn.clicked.connect(self.update_internal_variables)
        layout.addWidget(update_btn, row, 0, 1, 2)
        
        # 设置样式
        self._apply_input_styles()
        
        # 初始化显示
        self.update_variable_displays()
        
        # 启动定时器更新时间戳显示
        self.timer = QTimer()
        self.timer.timeout.connect(self.internal_vars.update_timestamp)
        self.timer.start(1000)  # 每秒更新一次
        
        group.setLayout(layout)
        parent_layout.addWidget(group)

    def _create_communication_section(self, parent_layout):
        group = QGroupBox("Communication")
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Message input/output with larger size
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Enter Modbus message here...")
        self.input_text.setMinimumHeight(250)
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(250)
        
        # Add headers with better styling
        input_label = QLabel("Input Message:")
        input_label.setStyleSheet("font-weight: bold; color: #444;")
        output_label = QLabel("Response:")
        output_label.setStyleSheet("font-weight: bold; color: #444;")
        
        layout.addWidget(input_label)
        layout.addWidget(self.input_text)
        layout.addWidget(output_label)
        layout.addWidget(self.output_text)
        
        # Control buttons with better layout
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.send_btn = QPushButton("Send Message")
        self.clear_btn = QPushButton("Clear")
        
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #107C10;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #138713;
            }
        """)
        
        self.send_btn.clicked.connect(self.send_message)
        self.clear_btn.clicked.connect(self.clear_messages)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.send_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        group.setLayout(layout)
        parent_layout.addWidget(group)

    def set_light_theme(self):
        """Apply light theme to the application"""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.WindowText, Qt.black)
        palette.setColor(QPalette.Base, Qt.white)
        palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.black)
        palette.setColor(QPalette.Text, Qt.black)
        palette.setColor(QPalette.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ButtonText, Qt.black)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(0, 120, 215))
        palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        
        QApplication.setPalette(palette)

    def refresh_com_ports(self):
        """Refresh available COM ports"""
        try:
            try:
                import serial.tools.list_ports
            except ImportError:
                self.log_message("PySerial not installed. Please run 'pip install pyserial'", "ERROR")
                logger.error("PySerial not installed")
                return

            ports = serial.tools.list_ports.comports()
            if not ports:
                self.log_message("No COM ports found", "WARNING")
            else:
                port_list = [port.device for port in ports]
                self.log_message(f"Available COM ports: {', '.join(port_list)}")
        except Exception as e:
            self.log_message(f"Error refreshing COM ports: {str(e)}", "ERROR")
            logger.error(f"Error refreshing COM ports: {e}")

    def send_message(self):
        """Send Modbus message"""
        message = self.input_text.toPlainText()
        try:
            # TODO: Implement actual Modbus message sending
            response = f"Simulated response for: {message}"
            self.log_message(response)
        except Exception as e:
            error_message = f"Error sending message: {str(e)}"
            self.log_message(error_message, "ERROR")
            logger.error(error_message)

    def clear_messages(self):
        """Clear input and output message areas"""
        self.input_text.clear()
        self.output_text.clear()

    def toggle_serial_port(self):
        """Toggle serial port open/close"""
        try:
            if self.serial_port is None or not self.serial_port.is_open:
                # 尝试打开串口
                port = self.port_combo.currentText()
                baud_rate = int(self.baud_combo.currentText())
                
                self.serial_port = serial.Serial(
                    port=port,
                    baudrate=baud_rate,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=1
                )
                
                # 创建并启动串口监听线程
                self.serial_monitor = SerialMonitorThread(self.serial_port)
                self.serial_monitor.data_received.connect(self.handle_received_data)
                self.serial_monitor.start()
                
                # 更新按钮文本和样式为"关闭串口"
                self.serial_btn.setText("关闭串口")
                self.serial_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #C42B1C;
                        min-width: 120px;
                    }
                    QPushButton:hover {
                        background-color: #D43B2C;
                    }
                """)
                self.log_message(f"串口 {port} 已成功打开")
                
                # 禁用端口和波特率选择
                self.port_combo.setEnabled(False)
                self.baud_combo.setEnabled(False)
                
            else:
                # 停止串口监听线程
                if hasattr(self, 'serial_monitor'):
                    self.serial_monitor.stop()
                    self.serial_monitor.wait()
                
                # 关闭串口
                self.serial_port.close()
                self.serial_port = None
                
                # 更新按钮文本和样式为"打开串口"
                self.serial_btn.setText("打开串口")
                self.serial_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #107C10;
                        min-width: 120px;
                    }
                    QPushButton:hover {
                        background-color: #138713;
                    }
                """)
                self.log_message("串口已关闭")
                
                # 启用端口和波特率选择
                self.port_combo.setEnabled(True)
                self.baud_combo.setEnabled(True)
                
            # 保存配置
            self.save_config()
            
        except SerialException as e:
            error_message = f"串口错误: {str(e)}"
            self.log_message(error_message, "ERROR")
            logger.error(error_message)
            
            # 确保在发生错误时重置状态
            if hasattr(self, 'serial_monitor'):
                self.serial_monitor.stop()
                self.serial_monitor.wait()
            if self.serial_port:
                self.serial_port.close()
            self.serial_port = None
            self.serial_btn.setText("打开串口")
            self.port_combo.setEnabled(True)
            self.baud_combo.setEnabled(True)

    def handle_received_data(self, data):
        """处理接收到的串口数据"""
        try:
            # 将接收到的数据转换为十六进制字符串
            hex_data = ' '.join([f'{b:02X}' for b in data])
            self.log_message(f"Received data: {hex_data}")
            
            # 解析Modbus帧
            self.parse_modbus_message(data)
            
        except Exception as e:
            self.log_message(f"Error handling received data: {str(e)}", "ERROR")
            logger.error(f"Error handling received data: {e}")

    def log_message(self, message, message_type="INFO"):
        """输出日志到Response窗"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] [{message_type}] {message}"
        self.output_text.append(formatted_message)

    def _create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
                padding: 2px;
            }
            QMenuBar::item {
                padding: 5px 10px;
                margin: 1px;
                border-radius: 3px;
            }
            QMenuBar::item:selected {
                background-color: #e9ecef;
            }
            QMenu {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                padding: 5px;
            }
            QMenu::item {
                padding: 5px 30px 5px 30px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #e9ecef;
            }
            QMenu::separator {
                height: 1px;
                background-color: #dee2e6;
                margin: 5px 0px;
            }
        """)
        
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        
        exit_action = QAction('退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 参数配置菜单
        config_menu = menubar.addMenu('参数配置')
        
        # 串口配置动作
        serial_settings_action = QAction('串口配置', self)
        serial_settings_action.setShortcut('Ctrl+S')
        serial_settings_action.triggered.connect(self.show_serial_settings)
        config_menu.addAction(serial_settings_action)
        
        # 协议配置动作
        protocol_settings_action = QAction('协议配置', self)
        protocol_settings_action.setShortcut('Ctrl+P')
        protocol_settings_action.triggered.connect(self.show_protocol_settings)
        config_menu.addAction(protocol_settings_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu('工具')
        
        clear_logs_action = QAction('清除日志', self)
        clear_logs_action.triggered.connect(self.clear_messages)
        tools_menu.addAction(clear_logs_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助')
        
        about_action = QAction('关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def show_serial_settings(self):
        """显示串口设置对话框"""
        try:
            # 创建对话框并传入当前配置
            dialog = SerialSettingsDialog(self)
            
            # 如果存在已保存的串口设置，则应用它
            if hasattr(self, 'serial_settings'):
                dialog.set_settings(self.serial_settings)
                
            # 显示对话框
            if dialog.exec_() == QDialog.Accepted:
                # 获取新的设置并保存
                new_settings = dialog.get_settings()
                self.serial_settings = new_settings
                self.config["serial_settings"] = new_settings
                self.save_config()
                self.log_message(f"Serial settings updated: {new_settings['port']}, {new_settings['baudrate']} baud")
        except Exception as e:
            self.log_message(f"Error showing serial settings dialog: {str(e)}", "ERROR")
            logger.error(f"Error in serial settings dialog: {e}")

    def show_protocol_settings(self):
        """显示协议配置对话框"""
        dialog = ProtocolSettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            selected_protocol = dialog.get_selected_protocol()
            self.load_protocol_config(selected_protocol)

    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, 
                         "关于 Modbus Protocol Simulator",
                         "Modbus Protocol Simulator v1.0\n\n"
                         "一个用于Modbus协议试的模拟器工具。\n\n"
                         "© 2024 Your Company")

    def load_protocol_config(self, protocol_name):
        """加载具体的协议配置"""
        try:
            if protocol_name in self.config["protocols"]:
                protocol_info = self.config["protocols"][protocol_name]
                config_file = f"protocols/{protocol_info['config_file']}"
                
                # 读取具体的协议配置
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.current_protocol = json.load(f)
                    self.current_protocol_name = protocol_name
                    self.log_message(f"已加载协议配置：{protocol_name}")
                    
                    # 保存当前协议选择到配置
                    self.config["last_protocol"] = protocol_name
                    self.save_config()
            else:
                self.log_message(f"未找到协议配置：{protocol_name}", "ERROR")
                
        except Exception as e:
            self.log_message(f"加载协议配置失败：{str(e)}", "ERROR")

    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                    self.log_message("Configuration loaded successfully")
            else:
                self.log_message("Configuration file not found, creating default configuration")
                self.config = self.create_default_config()
                if self.config is None:
                    raise Exception("Failed to create default configuration")
                
        except Exception as e:
            self.log_message(f"Error loading configuration: {str(e)}", "ERROR")
            logger.error(f"Error loading configuration: {e}")
            # 使用内存中的默认配置
            self.config = self.get_default_config()

    def get_default_config(self):
        """获取默认配置"""
        return {
            "serial_settings": {
                "port": "COM1",
                "baudrate": 9600,
                "parity": "N",
                "stopbits": 1,
                "bytesize": 8,
                "timeout": 1000
            },
            "protocols": {
                "古瑞瓦特逆变器 Modbus RTU Protocol_II V1.24简版": {
                    "id": "growatt_inverter",
                    "description": "古瑞瓦特逆变器通信协议",
                    "config_file": "growatt_protocol.json"
                },
                "正泰——CPS SCAxxKTL-T 系列 Modbus协议": {
                    "id": "chint_inverter",
                    "description": "正泰CPS系列逆变器通信协议",
                    "config_file": "chint_protocol.json"
                }
            },
            "last_protocol": ""
        }

    def create_default_config(self):
        """创建默认配置文件"""
        default_config = self.get_default_config()
        try:
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            self.log_message("Created default configuration file")
            return default_config
        except Exception as e:
            self.log_message(f"Error creating default config: {str(e)}", "ERROR")
            return None

    def save_config(self):
        """保存配置到文件"""
        try:
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
                self.log_message("Configuration saved successfully")
        except Exception as e:
            self.log_message(f"Error saving configuration: {str(e)}", "ERROR")
            logger.error(f"Error saving configuration: {e}")

    def apply_last_config(self):
        """应用上次的配置"""
        try:
            # 应用串口设置
            if "serial_settings" in self.config:
                settings = self.config["serial_settings"]
                # 保存串口设置供串口设置对话框使用
                self.serial_settings = settings
                # 记录日志
                self.log_message(f"Loaded serial settings: {settings['port']}, {settings['baudrate']} baud")
            
            # 加载上次使用的协议
            if "last_protocol" in self.config:
                protocol_name = self.config["last_protocol"]
                if protocol_name in self.config["protocols"]:
                    self.current_protocol = self.config["protocols"][protocol_name]
                    self.current_protocol_name = protocol_name
                    self.log_message(f"Loaded protocol: {protocol_name}")
        except Exception as e:
            self.log_message(f"Error applying configuration: {str(e)}", "ERROR")
            logger.error(f"Error applying configuration: {e}")

    def closeEvent(self, event):
        """窗口关闭时的处理"""
        try:
            # 停止串口监听线程
            if hasattr(self, 'serial_monitor'):
                self.serial_monitor.stop()
                self.serial_monitor.wait()
            
            # 关闭串口
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            
            # 保存配置
            self.save_config()
            
        except Exception as e:
            logger.error(f"Error in closeEvent: {e}")
        
        event.accept()

    def parse_modbus_message(self, message):
        """
        Parse received Modbus message and display result
        Args:
            message: bytes object containing the Modbus message
        """
        try:
            # 使用ModbusParser解析消息
            result = self.modbus_parser.parse_message(message)
            
            # 格式化并显示结果
            formatted_result = self.modbus_parser.format_parse_result(result)
            self.log_message(formatted_result)
            
        except Exception as e:
            error_message = f"解析Modbus消息时发生错误: {str(e)}"
            self.log_message(error_message, "ERROR")
            logger.error(error_message)

    def update_internal_variables(self):
        """更新内部变量值"""
        updates = {}
        for var_name, widget in self.var_widgets.items():
            value = widget.text()
            if value.strip():  # 只在有输入值时更新
                updates[var_name] = value
        
        success, errors = self.internal_vars.batch_update(updates)
        
        if success:
            self.log_message("所有变量更新成功")
        else:
            self.log_message(f"以下变量更新失败: {', '.join(errors)}", "ERROR")

    def update_variable_displays(self):
        """更新变量显示"""
        try:
            for var_name, widget in self.var_widgets.items():
                value = self.internal_vars.get_formatted_value(var_name)
                if value:
                    widget.setText(value)
        except Exception as e:
            self.log_message(f"更新显示时发生错误: {str(e)}", "ERROR")

    def on_variable_updated(self, var_name: str):
        """变量更新的观察者回调"""
        if var_name == 'timestamp':
            value = self.internal_vars.get_formatted_value('timestamp')
            if value:
                self.timestamp_display.setText(value)
        elif var_name in self.var_widgets:
            value = self.internal_vars.get_formatted_value(var_name)
            if value:
                self.var_widgets[var_name].setText(value)

    def _apply_input_styles(self):
        """应用输入框样式"""
        style = """
            QLineEdit {
                padding: 5px;
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 1px solid #0078D7;
            }
        """
        for widget in self.var_widgets.values():
            widget.setStyleSheet(style)
        self.timestamp_display.setStyleSheet(style)
