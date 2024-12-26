import sys
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from modbus import ModbusSimulator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('modbus_simulator.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def main():
    try:
        # 创建QApplication实例
        app = QApplication(sys.argv)
        
        # 设置应用程序范围的字体
        app.setFont(QFont('Segoe UI', 9))
        
        # 创建并显示主窗口
        logger.info("Starting Modbus Simulator...")
        window = ModbusSimulator()
        window.show()
        
        # 启动应用程序事件循环
        return app.exec_()
        
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}")
        sys.exit(1) 