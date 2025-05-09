import yaml

class ConfigManager:
    def __init__(self) -> None:
        self.path: str = ""
        self.config: dict = {}
    
    def load_config(self, file_path: str) -> None:
        self.path = file_path
        with open(self.path, "r") as file:
            self.config = yaml.load(file, Loader=yaml.FullLoader)
    
    def get_value(self, key_path: str, default_value = None):
        keys = key_path.split(".")
        config = self.config
        for key in keys[:-1]:
            config = config.get(key, {})
        return config.get(keys[-1], default_value)
    
    def get_path(self) -> None:
        return self.path
