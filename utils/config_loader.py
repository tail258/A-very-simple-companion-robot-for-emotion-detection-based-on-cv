import yaml
import os

class ConfigLoader:
    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
            cls._instance.load_config()
        return cls._instance

    def load_config(self, path="config.yaml"):
        if not os.path.exists(path):
            raise FileNotFoundError(f"配置文件 {path} 未找到！请检查路径。")
        
        with open(path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)
            print(f">>> [Config] Loaded configuration from {path}")

    def get(self, key_path):
        """
        支持用点号获取深层配置，例如: get('vision.pid_kp')
        """
        keys = key_path.split('.')
        value = self._config
        try:
            for k in keys:
                value = value[k]
            return value
        except KeyError:
            print(f"[Config Error] Key '{key_path}' not found!")
            return None

# 全局单例，方便其他模块直接 import
global_config = ConfigLoader()