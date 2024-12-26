import serial
import logging
from PyQt5.QtCore import QThread, pyqtSignal
from serial.serialutil import SerialException

logger = logging.getLogger(__name__)

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
                logger.error(f"Serial monitoring error: {e}")
            self.msleep(10)
            
    def stop(self):
        self.running = False

class SerialHandler:
    def __init__(self):
        self.serial_port = None
        self.serial_monitor = None
        
    def open_port(self, port, baud_rate):
        try:
            self.serial_port = serial.Serial(
                port=port,
                baudrate=baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            
            self.serial_monitor = SerialMonitorThread(self.serial_port)
            return True
            
        except SerialException as e:
            logger.error(f"Serial port error: {e}")
            return False
            
    def close_port(self):
        try:
            if self.serial_monitor:
                self.serial_monitor.stop()
                self.serial_monitor.wait()
                
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
                self.serial_port = None
                return True
                
        except Exception as e:
            logger.error(f"Error closing serial port: {e}")
            return False 