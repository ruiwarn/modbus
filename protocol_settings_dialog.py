from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QComboBox, 
                            QLabel, QPushButton, QGroupBox, QMessageBox)
from PyQt5.QtCore import Qt
import json
import os

class ProtocolSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        # 初始化配置文件路径
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(self.base_dir, 'config.json')
        
        self.setWindowTitle("协议配置")
        self.setModal(True)
        self.resize(1000, 200)
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 协议选择组
        group = QGroupBox("选择设备协议")
        group_layout = QVBoxLayout()
        
        # 协议选择
        self.protocol_combo = QComboBox()
        self.protocol_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.protocol_combo.setMinimumWidth(550)
        self.load_protocol_list()
        group_layout.addWidget(self.protocol_combo)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 确定按钮
        self.ok_button = QPushButton("确定")
        self.ok_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 24px;
                border-radius: 4px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.ok_button.clicked.connect(self.accept)
        
        # 取消按钮
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 24px;
                border-radius: 4px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
    def load_protocol_list(self):
        """加载协议列表"""
        try:
            if not os.path.exists(self.config_path):
                QMessageBox.critical(self, "错误", 
                    f"配置文件不存在:\n{self.config_path}\n\n请确保配置文件存在且格式正确。")
                self.parent.log_message(f"配置文件不存在: {self.config_path}", "ERROR")
                return
                
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if "protocols" not in config:
                    QMessageBox.critical(self, "错误", 
                        "配置文件格式错误：未找到protocols字段\n\n请检查配置文件格式。")
                    self.parent.log_message("配置文件中没有找到protocols字段", "ERROR")
                    return
                    
                self.protocol_combo.addItems(config["protocols"].keys())
                
                # 设置上次选择的协议
                if "last_protocol" in config:
                    index = self.protocol_combo.findText(config["last_protocol"])
                    if index >= 0:
                        self.protocol_combo.setCurrentIndex(index)
        except json.JSONDecodeError:
            QMessageBox.critical(self, "错误", 
                "配置文件格式错误\n\n请确保配置文件是有效的JSON格式。")
            self.parent.log_message("配置文件格式错误", "ERROR")
        except Exception as e:
            QMessageBox.critical(self, "错误", 
                f"加载协议列表失败：\n{str(e)}")
            self.parent.log_message(f"加载协议列表失败：{str(e)}", "ERROR")
    
    def get_selected_protocol(self):
        """获取选中的协议"""
        return self.protocol_combo.currentText() 
    
    def load_config(self):
        """加载配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
                return self.config.get('protocols', {})
        except FileNotFoundError:
            QMessageBox.critical(self, "错误", 
                f"配置文件未找到：\n{self.config_path}")
            return {}
        except json.JSONDecodeError:
            QMessageBox.critical(self, "错误", 
                "配置文件格式错误\n\n请确保配置文件是有效的JSON格式。")
            return {} 