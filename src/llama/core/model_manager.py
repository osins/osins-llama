from llama_cpp import Llama
from pathlib import Path
import threading
from src.llama.config.config import Config


class ModelManager:
    """
    模型管理器
    负责模型的加载、管理和生命周期控制
    """

    _instance = None
    _lock = threading.Lock()

    def __init__(self, config: Config = None):
        """
        初始化模型管理器
        """
        self.config = config or Config.from_env()
        self.model_path = self.config.model.path
        self.model = None
        self._load_model()

    def _load_model(self):
        """
        加载模型
        """
        if self.model_path is None or self.model_path == "":
            raise ValueError("Model path is not set")

        if (not Path(self.model_path).exists()) is True:
            raise FileNotFoundError(f"Model file not found: {self.model_path}")

        print(f"Loading model: {Path(self.model_path).name}")

        self.model = Llama(
            model_path=self.model_path,
            n_ctx=self.config.model.n_ctx,
            n_threads=self.config.model.n_threads,
            verbose=self.config.model.verbose
        )

        print(f"Model loaded successfully: {Path(self.model_path).name}")

    @classmethod
    def get_instance(cls, config: Config = None):
        """
        获取模型管理器单例实例
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(config)
        return cls._instance

    def get_model(self):
        """
        获取模型实例
        """
        return self.model

    def reload_model(self, model_path: str = None):
        """
        重新加载模型
        """
        if model_path is not None and model_path != "":
            self.model_path = model_path
            self.config.model.path = model_path

        self._load_model()