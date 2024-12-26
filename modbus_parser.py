import logging
from internal_variables import InternalVariables

logger = logging.getLogger(__name__)

class ModbusParser:
    def __init__(self):
        self.current_protocol = None
        self.internal_vars = InternalVariables()
        
    def set_protocol(self, protocol):
        self.current_protocol = protocol
        
    def parse_message(self, message):
        """
        Parse Modbus message and return parsed result
        Args:
            message: bytes object containing the Modbus message
        Returns:
            dict: Parsed message information or None if parsing fails
        """
        if not self.current_protocol:
            logger.error("No protocol loaded")
            return None
            
        try:
            # 检查消息长度
            if len(message) < 4:  # Modbus消息至少需要4字节
                logger.warning("Message too short")
                return None
                
            function_code = message[1]
            if function_code in self.current_protocol['function_codes']:
                result = {
                    'function_code': function_code,
                    'function_name': self.current_protocol['function_codes'][function_code]
                }
                
                register_addr = f"0x{message[2:4].hex().upper()}"
                if register_addr in self.current_protocol['registers']:
                    reg_info = self.current_protocol['registers'][register_addr]
                    result['register'] = {
                        'address': register_addr,
                        'name': reg_info['name'],
                        'description': reg_info['description']
                    }
                    
                    # 检查是否有变量映射
                    if 'variable_mapping' in reg_info:
                        var_mapping = reg_info['variable_mapping']
                        var_name = var_mapping['name']
                        var_value = self.internal_vars.get_variable(var_name)
                        
                        if var_value is not None:
                            # 应用转换规则
                            conversion = var_mapping.get('conversion', {})
                            read_conversion = conversion.get('read', 'value')
                            
                            try:
                                # 使用安全的eval执行转换表达式
                                converted_value = eval(
                                    read_conversion, 
                                    {"__builtins__": {}}, 
                                    {"value": var_value}
                                )
                                result['value'] = converted_value
                            except Exception as e:
                                logger.error(f"Error converting value: {e}")
                                result['value'] = var_value
                    
                    result['data'] = message[4:-2].hex().upper()
                    return result
                    
        except Exception as e:
            logger.error(f"Error parsing Modbus message: {e}")
            return None
            
    def format_parse_result(self, result):
        """
        Format parsed result into human readable string
        Args:
            result: dict containing parsed message information
        Returns:
            str: Formatted result string
        """
        if not result:
            return "无法解析消息"
            
        try:
            formatted_result = (
                f"解析结果:\n"
                f"功能码: {result.get('function_code', 'Unknown')} "
                f"({result.get('function_name', 'Unknown')})\n"
            )
            
            if 'register' in result:
                reg_info = result['register']
                formatted_result += (
                    f"寄存器地址: {reg_info['address']}\n"
                    f"寄存器名称: {reg_info['name']}\n"
                    f"描述: {reg_info['description']}\n"
                )
                
                if 'value' in result:
                    formatted_result += f"变量值: {result['value']}\n"
            
            if 'data' in result:
                formatted_result += f"原始数据: {result['data']}"
                
            return formatted_result
            
        except Exception as e:
            logger.error(f"Error formatting parse result: {e}")
            return "格式化解析结果时发生错误" 