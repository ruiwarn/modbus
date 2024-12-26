import json
import os
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    def __init__(self):
        self.config = None
        self.protocols = {}
        
    def get_default_config(self):
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

    def load_config(self):
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                    logger.info("Configuration loaded successfully")
            else:
                logger.warning("Configuration file not found, creating default configuration")
                self.config = self.create_default_config()
                if self.config is None:
                    raise Exception("Failed to create default configuration")
                    
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self.config = self.get_default_config()

    def create_default_config(self):
        default_config = self.get_default_config()
        try:
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            logger.info("Created default configuration file")
            return default_config
        except Exception as e:
            logger.error(f"Error creating default config: {e}")
            return None

    def save_config(self):
        try:
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
                logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

    def load_protocols(self):
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if "protocols" in config:
                        self.protocols = config["protocols"]
                        logger.info("Protocol configurations loaded successfully")
                    else:
                        logger.warning("No protocols found in configuration")
            else:
                logger.warning("Configuration file not found")
                self.create_default_config()
                
        except Exception as e:
            logger.error(f"Error loading protocols: {e}") 