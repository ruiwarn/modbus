from datetime import datetime
import logging
from typing import Any, Dict, Optional, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class VariableInfo:
    """变量信息数据类"""
    name: str
    value: Any
    type: type
    description: str
    unit: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    format_str: str = "{:.1f}"

class InternalVariables:
    def __init__(self):
        # 初始化内部变量
        self._variables = {
            'timestamp': VariableInfo(
                name="时间戳",
                value=datetime.now(),
                type=datetime,
                description="Current timestamp",
                unit=None,
                format_str="%Y-%m-%d %H:%M:%S"
            ),
            'voltage': VariableInfo(
                name="电压",
                value=220.0,
                type=float,
                description="Current voltage",
                unit="V",
                min_value=0.0,
                max_value=380.0
            ),
            'current': VariableInfo(
                name="电流",
                value=0.0,
                type=float,
                description="Current amperage",
                unit="A",
                min_value=0.0,
                max_value=100.0
            ),
            'power': VariableInfo(
                name="功率",
                value=0.0,
                type=float,
                description="Active power",
                unit="kW",
                min_value=0.0,
                max_value=999999.9
            ),
            'energy': VariableInfo(
                name="电能",
                value=0.0,
                type=float,
                description="Total energy consumption",
                unit="kWh",
                min_value=0.0,
                max_value=999999.9
            )
        }
        
        # 寄存器到变量的映射
        self._register_mapping = {
            '0x1000': 'voltage',
            '0x1001': 'current',
            '0x1002': 'power',
            '0x1003': 'energy',
            '0x1004': 'timestamp'
        }
        
        self._observers = []

    def add_observer(self, observer):
        """添加观察者"""
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer):
        """移除观察者"""
        if observer in self._observers:
            self._observers.remove(observer)

    def notify_observers(self, var_name: str):
        """通知所有观察者变量更新"""
        for observer in self._observers:
            observer.on_variable_updated(var_name)

    def get_variable_info(self, name: str) -> Optional[VariableInfo]:
        """获取变量的完整信息"""
        return self._variables.get(name)

    def get_variable(self, name: str) -> Optional[Any]:
        """获取变量值"""
        var_info = self._variables.get(name)
        return var_info.value if var_info else None

    def get_formatted_value(self, name: str) -> Optional[str]:
        """获取格式化后的变量值"""
        var_info = self._variables.get(name)
        if not var_info:
            return None
            
        try:
            if isinstance(var_info.value, datetime):
                return var_info.value.strftime(var_info.format_str)
            return var_info.format_str.format(var_info.value)
        except Exception as e:
            logger.error(f"Error formatting value for {name}: {e}")
            return str(var_info.value)

    def set_variable(self, name: str, value: Any) -> bool:
        """设置变量值"""
        if name not in self._variables:
            logger.error(f"Variable {name} does not exist")
            return False

        try:
            var_info = self._variables[name]
            
            # 类型检查和转换
            if not isinstance(value, var_info.type):
                value = var_info.type(value)
            
            # 范围检查
            if var_info.min_value is not None and var_info.max_value is not None:
                if value < var_info.min_value or value > var_info.max_value:
                    logger.error(f"Value {value} out of range for {name}")
                    return False
            
            var_info.value = value
            self.notify_observers(name)
            return True
            
        except ValueError as e:
            logger.error(f"Error setting variable {name}: {e}")
            return False

    def get_all_variables(self) -> Dict[str, VariableInfo]:
        """获取所有变量信息"""
        return self._variables

    def get_all_formatted_values(self) -> Dict[str, str]:
        """获取所有变量的格式化值"""
        return {name: self.get_formatted_value(name) 
                for name in self._variables}

    def update_timestamp(self):
        """更新时间戳"""
        self.set_variable('timestamp', datetime.now())

    def get_register_value(self, register_addr: str) -> Optional[Any]:
        """通过寄存器地址获取对应的变量值"""
        if register_addr in self._register_mapping:
            var_name = self._register_mapping[register_addr]
            return self.get_variable(var_name)
        return None

    def get_variable_metadata(self) -> List[Dict[str, Any]]:
        """获取所有变量的元数据，用于UI显示"""
        metadata = []
        for name, info in self._variables.items():
            if name == 'timestamp':
                continue  # 时间戳单独处理
            metadata.append({
                'name': name,
                'display_name': info.name,
                'unit': info.unit,
                'min_value': info.min_value,
                'max_value': info.max_value,
                'placeholder': f"{info.min_value} - {info.max_value}"
            })
        return metadata

    def batch_update(self, updates: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """批量更新变量值"""
        success = True
        errors = []
        
        for name, value in updates.items():
            if not self.set_variable(name, value):
                success = False
                errors.append(name)
                
        return success, errors 