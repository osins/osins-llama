"""Tests for the CLI config commands."""
import unittest
import tempfile
import os
from pathlib import Path
import json
from unittest.mock import patch, mock_open
from src.llama.cli.config import load_config, save_config, execute_show, execute_set, execute_reset


class TestConfigCommands(unittest.TestCase):

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temp_dir.name) / "test_config.json"

    def tearDown(self):
        """清理测试环境"""
        self.temp_dir.cleanup()

    def test_load_config_empty_file(self):
        """测试加载空配置文件"""
        # 当配置文件不存在时，应返回空字典
        config = load_config(self.config_path)
        self.assertEqual(config, {})

    def test_load_config_existing_file(self):
        """测试加载现有配置文件"""
        # 创建一个配置文件
        test_config = {"key1": "value1", "key2": "value2"}
        with open(self.config_path, 'w') as f:
            json.dump(test_config, f)
        
        config = load_config(self.config_path)
        self.assertEqual(config, test_config)

    def test_save_config_success(self):
        """测试成功保存配置"""
        test_config = {"key1": "value1", "key2": "value2"}
        
        save_config(test_config, self.config_path)
        
        # 验证配置文件被正确创建
        self.assertTrue(self.config_path.exists())
        
        # 验证配置内容正确
        with open(self.config_path, 'r') as f:
            saved_config = json.load(f)
        self.assertEqual(saved_config, test_config)

    def test_save_config_atomic_operation(self):
        """测试保存配置的原子性操作"""
        test_config = {"key1": "value1"}
        
        # 模拟保存过程中的异常
        with patch('builtins.open', side_effect=[OSError("Disk full"), mock_open()]):
            with self.assertRaises(OSError):
                save_config(test_config, self.config_path)
        
        # 验证配置文件不应该存在
        self.assertFalse(self.config_path.exists())

    def test_execute_set_valid_key(self):
        """测试设置有效键名"""
        key = "valid_key"
        value = "valid_value"
        
        execute_set(key, value, self.config_path)
        
        # 验证配置被正确设置
        with open(self.config_path, 'r') as f:
            config = json.load(f)
        self.assertIn(key, config)
        self.assertEqual(config[key], value)

    def test_execute_set_invalid_key(self):
        """测试设置无效键名"""
        invalid_keys = ["", "key with space", "key\nwith\nnewline", "key\twith\ttab", "key/with/slash", "key\\with\\backslash"]
        
        for key in invalid_keys:
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    execute_set(key, "some_value", self.config_path)

    def test_execute_show_with_config(self):
        """测试显示有内容的配置"""
        test_config = {"key1": "value1", "key2": "value2"}
        with open(self.config_path, 'w') as f:
            json.dump(test_config, f)
        
        # 捕获execute_show的输出
        import io
        import sys
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        execute_show(self.config_path)
        
        # 恢复stdout
        sys.stdout = sys.__stdout__
        
        output = captured_output.getvalue().strip()
        
        # 验证输出包含配置项
        for key, value in test_config.items():
            self.assertIn(f"{key} = {value}", output)

    def test_execute_show_empty_config(self):
        """测试显示空配置"""
        import io
        import sys
        from unittest.mock import patch
        
        # 捕获日志输出
        with patch('logging.Logger.info') as mock_logger_info:
            captured_output = io.StringIO()
            sys.stdout = captured_output
            
            execute_show(self.config_path)
            
            sys.stdout = sys.__stdout__
            
            # 验证输出包含"Configuration is empty"
            self.assertIn("Configuration is empty", captured_output.getvalue())
            
            # 验证记录了"Configuration is empty"
            mock_logger_info.assert_called_with("Configuration is empty")

    def test_execute_reset_existing_config(self):
        """测试重置现有配置"""
        # 创建一个配置文件
        test_config = {"key1": "value1"}
        with open(self.config_path, 'w') as f:
            json.dump(test_config, f)
        
        # 确保文件存在
        self.assertTrue(self.config_path.exists())
        
        # 执行重置
        execute_reset(self.config_path)
        
        # 验证文件已被删除
        self.assertFalse(self.config_path.exists())

    def test_execute_reset_nonexistent_config(self):
        """测试重置不存在的配置"""
        # 确保文件不存在
        self.assertFalse(self.config_path.exists())
        
        # 捕获日志输出
        from unittest.mock import patch
        with patch('logging.Logger.info') as mock_logger_info:
            import io
            import sys
            captured_output = io.StringIO()
            sys.stdout = captured_output
            
            execute_reset(self.config_path)
            
            sys.stdout = sys.__stdout__
            
            # 验证输出包含"Configuration file does not exist, nothing to reset"
            self.assertIn("Configuration file does not exist, nothing to reset", captured_output.getvalue())
            
            # 验证记录了"Configuration file does not exist, nothing to reset"
            mock_logger_info.assert_called_with("Configuration file does not exist, nothing to reset")

    def test_save_config_with_custom_path(self):
        """测试使用自定义路径保存配置"""
        custom_path = Path(self.temp_dir.name) / "custom_config.json"
        test_config = {"key1": "value1"}
        
        save_config(test_config, custom_path)
        
        # 验证配置文件在自定义路径被创建
        self.assertTrue(custom_path.exists())
        
        # 验证配置内容正确
        with open(custom_path, 'r') as f:
            saved_config = json.load(f)
        self.assertEqual(saved_config, test_config)

    def test_path_security_validation(self):
        """测试路径安全校验"""
        # 测试包含父目录遍历的路径
        dangerous_path = Path(self.temp_dir.name) / ".." / "dangerous_config.json"
        
        test_config = {"key1": "value1"}
        
        with self.assertRaises(ValueError):
            save_config(test_config, dangerous_path)

    def test_config_override(self):
        """测试配置覆盖"""
        # 初始配置
        initial_config = {"key1": "initial_value"}
        with open(self.config_path, 'w') as f:
            json.dump(initial_config, f)
        
        # 覆盖配置
        override_config = {"key1": "override_value", "key2": "new_value"}
        save_config(override_config, self.config_path)
        
        # 验证配置被正确覆盖
        with open(self.config_path, 'r') as f:
            final_config = json.load(f)
        
        self.assertEqual(final_config, override_config)
