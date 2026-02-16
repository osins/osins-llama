"""守护进程模块测试"""
import unittest
import os
import time
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.llama.services.guardian import GuardianService, GuardianConfig
from src.llama.cli.process import ProcessManager
from src.llama.models.pid_data import PidData


class TestGuardianConfig(unittest.TestCase):
    """测试守护进程配置类"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'test_config.yaml')
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_default_config(self):
        """测试默认配置"""
        config = GuardianConfig(config_path=None)
        
        # 验证默认值
        self.assertEqual(config.max_restarts, 5)
        self.assertEqual(config.check_interval, 5)
        self.assertEqual(config.restart_interval, 5)
        self.assertTrue(config.gpu_monitoring)
    
    def test_custom_config(self):
        """测试自定义配置"""
        config_content = """
max_restarts: 10
check_interval: 10
log_level: DEBUG
gpu_monitoring: false
"""
        with open(self.config_path, 'w') as f:
            f.write(config_content)
        
        config = GuardianConfig(config_path=self.config_path)
        
        self.assertEqual(config.max_restarts, 10)
        self.assertEqual(config.check_interval, 10)
        self.assertEqual(config.log_level, 'DEBUG')
        self.assertFalse(config.gpu_monitoring)


class TestGuardianService(unittest.TestCase):
    """测试守护服务类"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.pid_file = os.path.join(self.temp_dir, 'test.pid')
        
        # 创建测试用的PID数据
        self.pid_data = PidData(
            pid=1234,
            model_path="/path/to/model",
            host="127.0.0.1",
            port=31301,
            n_ctx=2048,
            n_threads=8,
            api_keys="test_key_12345678",
            max_concurrent_requests=10,
            rate_limit_requests=60,
            rate_limit_window=60,
            debug=False
        )
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    @patch('src.llama.cli.process.ProcessManager')
    @patch('src.llama.cli.pid_file_manager.PidFileManager')
    def test_initialization(self, mock_pid_manager, mock_process_manager):
        """测试初始化"""
        mock_pid_manager_instance = MagicMock()
        mock_pid_manager.return_value = mock_pid_manager_instance
        
        guardian = GuardianService()
        
        self.assertIsInstance(guardian, GuardianService)
        self.assertIsNotNone(guardian.logger)
        self.assertIsNotNone(guardian.process_manager)
        self.assertIsNotNone(guardian.pid_manager)
    
    @patch('src.llama.cli.process.ProcessManager')
    @patch('src.llama.cli.pid_file_manager.PidFileManager')
    def test_exponential_backoff_delay(self, mock_pid_manager, mock_process_manager):
        """测试指数退避延迟"""
        guardian = GuardianService()
        
        # 初始延迟应为基本重启间隔
        delay = guardian.exponential_backoff_delay()
        self.assertEqual(delay, guardian.config.restart_interval)
        
        # 模拟第一次重启
        guardian.restart_count = 1
        delay = guardian.exponential_backoff_delay()
        expected_delay = guardian.config.restart_interval * (guardian.config.exponential_backoff_factor ** 1)
        self.assertEqual(delay, min(expected_delay, guardian.config.max_backoff_time))
        
        # 模拟多次重启，验证不会超过最大退避时间
        guardian.restart_count = 10
        delay = guardian.exponential_backoff_delay()
        self.assertLessEqual(delay, guardian.config.max_backoff_time)
    
    @patch('src.llama.cli.process.ProcessManager')
    @patch('src.llama.cli.pid_file_manager.PidFileManager')
    @patch('src.llama.services.guardian.time.sleep')
    def test_perform_restart(self, mock_sleep, mock_pid_manager, mock_process_manager):
        """测试执行重启"""
        # Mock PID manager
        mock_pid_manager_instance = MagicMock()
        mock_pid_manager_instance.read.return_value = self.pid_data
        mock_pid_manager.return_value = mock_pid_manager_instance
        
        # Mock process manager
        mock_process_manager_instance = MagicMock()
        mock_process_manager_instance.stop.return_value = True
        mock_process_manager_instance.start_detached.return_value = True
        mock_process_manager.return_value = mock_process_manager_instance
        
        guardian = GuardianService()
        guardian.pid_manager = mock_pid_manager_instance
        guardian.process_manager = mock_process_manager_instance
        
        # 执行重启
        guardian._perform_restart()
        
        # 验证方法调用
        mock_process_manager_instance.stop.assert_called_once()
        mock_process_manager_instance.start_detached.assert_called_once_with(self.pid_data)
        self.assertEqual(guardian.restart_count, 1)
    
    @patch('src.llama.cli.process.ProcessManager')
    @patch('src.llama.cli.pid_file_manager.PidFileManager')
    def test_get_status(self, mock_pid_manager, mock_process_manager):
        """测试获取状态"""
        # Mock process manager
        mock_process_manager_instance = MagicMock()
        mock_process_manager_instance.is_running.return_value = True
        mock_process_manager_instance.get_pid.return_value = 1234
        mock_process_manager.return_value = mock_process_manager_instance
        
        guardian = GuardianService()
        guardian.process_manager = mock_process_manager_instance
        guardian.running = True
        
        status = guardian.get_status()
        
        self.assertEqual(status['guardian_running'], True)
        self.assertEqual(status['main_service_running'], True)
        self.assertEqual(status['main_service_pid'], 1234)
        self.assertIn('config', status)


class TestProcessManagerExtensions(unittest.TestCase):
    """测试 ProcessManager 扩展功能"""
    
    def setUp(self):
        self.process_manager = ProcessManager(expected_cmd_keyword="test")
    
    @patch('subprocess.Popen')
    def test_start_detached(self, mock_popen):
        """测试分离模式启动"""
        mock_process = MagicMock()
        mock_process.pid = 1234
        mock_popen.return_value = mock_process
        
        pid_data = PidData(
            pid=1234,
            model_path="/path/to/model",
            host="127.0.0.1",
            port=31301,
            n_ctx=2048,
            n_threads=8
        )
        
        result = self.process_manager.start_detached(pid_data=pid_data)
        
        # 验证 subprocess.Popen 被调用两次（一次用于启动，一次用于启动进程）
        # 实际上只需要验证启动时没有捕获输出
        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        # 确认启动时没有捕获输出
        self.assertNotIn('stdout', kwargs)  # 不应该设置stdout捕获
        self.assertNotIn('stderr', kwargs)  # 不应该设置stderr捕获


if __name__ == '__main__':
    unittest.main()