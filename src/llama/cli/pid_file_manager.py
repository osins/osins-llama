"""PID file manager for osins-llama server (JSON-only, production-grade)."""

import json
import os
import sys
import tempfile
import portalocker
import time
import re
import logging
from pathlib import Path
from typing import Optional, List
from contextlib import contextmanager
from src.llama.models.pid_data import PidData
import uuid
import hashlib


class PidFileError(Exception):
    pass


class PidFileManager:
    """Strict JSON-based PID file manager with atomic write and validation."""

    def __init__(self) -> None:
        self.logger = logging.getLogger("osins-llama.pid")
        
        pid_file_path_str = os.getenv("LLAMA_PID_FILE", "./llama.pid")
        self.strict_fs_check = os.getenv("LLAMA_PID_CHECK_FS", "1") == "1"

        if not pid_file_path_str:
            raise ValueError("LLAMA_PID_FILE cannot be empty")

        self.pid_file_path = Path(pid_file_path_str).expanduser()

        # 安全检查：不允许符号链接
        if self.pid_file_path.is_symlink():
            raise ValueError("PID file path cannot be a symbolic link")

        # 确保PID文件路径不指向系统关键位置 (修复：使用路径语义检查)
        abs_path = self.pid_file_path.resolve()
        dangerous_paths = ["/etc", "/usr", "/bin", "/sbin", "/boot", "/sys", "/proc", "/var/log"]
        for dangerous_path in dangerous_paths:
            dangerous_path_obj = Path(dangerous_path).resolve()
            # 使用路径语义检查，而非字符串前缀匹配
            if dangerous_path_obj in abs_path.parents or abs_path == dangerous_path_obj:
                raise ValueError(f"PID file path cannot be in system directory: {dangerous_path}")

        if self.pid_file_path.is_dir():
            raise ValueError("PID file path cannot be a directory")

    # ==========================================================
    # 敏感信息脱敏
    # ==========================================================

    def mask_sensitive(self, value: str, type_: str = "key") -> str:
        """脱敏敏感信息"""
        if not value:
            return ""
        if type_ == "key":
            parts = value.split(',')
            return ','.join([k[:4] + '*'*(len(k)-8) + k[-4:] if len(k) > 8 else '*'*len(k) for k in parts])
        elif type_ == "path":
            return Path(value).name
        return value

    # ==========================================================
    # 安全工具函数
    # ==========================================================

    def safe_shell_arg(self, value: str) -> str:
        """安全转义命令参数，防止命令注入"""
        if value is None:
            return ""

        # 移除控制字符和潜在危险字符，保留路径分隔符（包括反斜杠和正斜杠）
        clean_value = re.sub(r'[^\w\s\-\._/~:?#\[\]@!$&\'()*+,;=%\\]', '', value)
        # 移除可能的命令注入字符
        clean_value = clean_value.replace('"', '').replace("'", '').replace(';', '').replace('|', '').replace('&', '')
        # 移除零宽字符
        clean_value = ''.join(ch for ch in clean_value if ord(ch) >= 32 or ord(ch) in (9, 10, 13))
        # 限制长度
        return clean_value[:1024].strip()

    def _safe_cleanup_file(self, path: Path) -> bool:
        """安全清理文件，带重试机制"""
        if not path.exists():
            return True
            
        for attempt in range(3):
            try:
                path.unlink()
                return True
            except OSError as e:
                self.logger.debug(f"Attempt {attempt+1} to remove {path}: {str(e)}")
                time.sleep(0.05)  # 50ms delay
        return False

    def _safe_cleanup_lock_file(self) -> None:
        """清理锁文件"""
        lock_file_path = self.pid_file_path.with_suffix(self.pid_file_path.suffix + '.lock')
        self._safe_cleanup_file(lock_file_path)

    # ==========================================================
    # 校验逻辑（强类型 + 强约束）
    # ==========================================================

    def _validate_pid_data(self, data: dict) -> None:
        required_fields = ["host", "port"]

        for field in required_fields:
            if field not in data:
                raise PidFileError(f"Missing required field: {field}")

        if not isinstance(data["host"], str) or not data["host"]:
            raise PidFileError("Invalid host")

        if not isinstance(data["port"], int) or not (1 <= data["port"] <= 65535):
            raise PidFileError("Invalid port")

        int_fields = [
            "n_ctx",
            "n_threads",
            "n_gpu_layers",
            "n_batch",
            "max_concurrent_requests",
            "rate_limit_requests",
            "rate_limit_window",
        ]

        for field in int_fields:
            value = data.get(field)
            if value is not None:
                if not isinstance(value, int) or value < 0:
                    raise PidFileError(f"Invalid {field}")

        if data.get("api_keys") is not None:
            if not isinstance(data["api_keys"], str):
                raise PidFileError("Invalid api_keys")
            # 严格验证 API Keys 格式（支持逗号分隔的列表）
            if ',' in data["api_keys"]:
                keys = [k.strip() for k in data["api_keys"].split(',')]
                for key in keys:
                    if not re.match(r'^[A-Za-z0-9_\-]{16,128}$', key):
                        raise PidFileError("Invalid api_keys format")
            else:
                if not re.match(r'^[A-Za-z0-9_\-]{16,128}$', data["api_keys"]):
                    raise PidFileError("Invalid api_keys format")

        if data.get("model_path") is not None:
            if not isinstance(data["model_path"], str):
                raise PidFileError("Invalid model_path")
            
            # 增强对 model_path 的校验
            model_path = data["model_path"].strip()
            if not model_path:
                raise PidFileError("model_path cannot be empty or blank")
            
            # 检查是否包含换行符或其他控制字符
            if any(ord(c) < 32 for c in data["model_path"]):
                raise PidFileError("model_path contains invalid control characters")
        
        if data.get("debug") is not None and not isinstance(data["debug"], bool):
            raise PidFileError("Invalid debug flag")

        # 检查是否有意外的额外字段（除了内部使用的 _hash）
        allowed_fields = set([
            "model_path", "host", "port", "n_ctx", "n_threads",
            "n_gpu_layers", "n_batch",
            "api_keys", "max_concurrent_requests", "rate_limit_requests",
            "rate_limit_window", "debug", "format_version", "_hash"
        ])

        unexpected_fields = set(data.keys()) - allowed_fields
        if unexpected_fields:
            raise PidFileError(f"Unexpected fields in PID data: {unexpected_fields}")

    # ==========================================================
    # 跨平台锁优化（区分读写锁）
    # ==========================================================

    @contextmanager
    def _acquire_lock(self, write: bool = True):
        lock_file_path = self.pid_file_path.with_suffix(self.pid_file_path.suffix + '.lock')
        lock_file = None
        try:
            lock_file = open(str(lock_file_path), 'a+')
            # Windows ACL 权限强化（仅限 Windows）
            if sys.platform == 'win32':
                import ctypes
                FILE_ATTRIBUTE_HIDDEN = 0x02
                try:
                    ctypes.windll.kernel32.SetFileAttributesW(str(lock_file_path), FILE_ATTRIBUTE_HIDDEN)
                except Exception as e:
                    self.logger.warning(f"Failed to set hidden attribute on lock file {lock_file_path}: {str(e)}")
            else:
                try:
                    os.chmod(lock_file_path, 0o600)
                except (OSError, NotImplementedError) as e:
                    self.logger.warning(f"Failed to set permissions on lock file {lock_file_path}: {str(e)}")
            
            portalocker.lock(
                lock_file, 
                portalocker.LOCK_EX if write else portalocker.LOCK_SH
            )
            yield
        except Exception as e:
            op_type = "WRITE" if write else "READ"
            self.logger.error(f"[LOCK-{op_type}] Error acquiring lock on {lock_file_path}: {str(e)}")
            raise
        finally:
            if lock_file:
                try:
                    portalocker.unlock(lock_file)
                except Exception as e:
                    op_type = "WRITE" if write else "READ"
                    self.logger.warning(f"[LOCK-{op_type}] Error unlocking lock file {lock_file_path}: {str(e)}")
                finally:
                    lock_file.close()
                    # 只在写操作时清理锁文件
                    if write:
                        self._safe_cleanup_file(lock_file_path)

    # ==========================================================
    # TOCTOU 安全目录检查强化（UUID 校验）
    # ==========================================================

    def _create_uuid_file(self) -> Path:
        """在父目录创建 UUID 文件，用于验证目录未被篡改"""
        uuid_file = self.pid_file_path.parent / f".{self.pid_file_path.name}_uuid"
        if not uuid_file.exists():
            with open(uuid_file, 'w', encoding="utf-8") as f:
                f.write(str(uuid.uuid4()))
        return uuid_file

    def _verify_parent_dir_safe(self) -> str:
        """验证父目录安全性并返回目录的标识符（路径或inode）"""
        # 如果禁用了严格文件系统检查，返回简化标识
        if not self.strict_fs_check:
            return str(self.pid_file_path.parent.resolve())

        parent_dir = self.pid_file_path.parent

        # 检查是否为符号链接
        if parent_dir.is_symlink():
            raise PidFileError(f"Parent directory is a symbolic link: {parent_dir}")

        # 检查 UUID 文件是否存在且未被篡改
        uuid_file = self._create_uuid_file()
        if not uuid_file.exists():
            raise PidFileError(f"UUID file missing: {uuid_file}")

        # 读取 UUID 并检查 mtime
        uuid_content = uuid_file.read_text().strip()
        stat_info = uuid_file.stat()

        # 在 Windows 上使用路径字符串和时间戳进行比较
        if sys.platform == 'win32':
            return f"{os.path.realpath(parent_dir)}:{stat_info.st_ctime}:{stat_info.st_mtime}:{uuid_content}"
        else:
            # Unix 系统使用 inode + UUID
            dir_fd = os.open(str(parent_dir), os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
            try:
                dir_stat = os.fstat(dir_fd)
                return f"{dir_stat.st_ino}:{uuid_content}:{stat_info.st_mtime}"
            finally:
                os.close(dir_fd)

    # ==========================================================
    # 原子写入增强
    # ==========================================================

    @contextmanager
    def _atomic_write(self):
        # 先确保父目录存在
        self.pid_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 验证父目录安全性
        expected_identifier = self._verify_parent_dir_safe()
        
        # 使用临时文件，确保唯一性
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=self.pid_file_path.parent,
            prefix=self.pid_file_path.name + '.tmp.'
        )
        
        try:
            with os.fdopen(tmp_fd, 'w', encoding="utf-8") as tmp:
                yield tmp
                tmp.flush()
                os.fsync(tmp.fileno())

            # 再次验证父目录未被篡改（如果启用了严格检查）
            if self.strict_fs_check:
                current_identifier = self._verify_parent_dir_safe()
                if current_identifier != expected_identifier:
                    raise PidFileError("Parent directory changed during write operation")

            # 原子替换
            os.replace(tmp_path, self.pid_file_path)

            # 设置权限（在Windows上可能无效，但不影响功能）
            try:
                os.chmod(self.pid_file_path, 0o600)
            except (OSError, NotImplementedError):
                # 在Windows等系统上可能不支持此操作，记录警告但继续
                self.logger.warning(f"[WRITE] Failed to set permissions on PID file {self.pid_file_path}")

            if self.strict_fs_check:
                try:
                    # Windows 上跳过目录同步，因为可能不支持或导致错误
                    if sys.platform != 'win32':
                        dir_fd = os.open(str(self.pid_file_path.parent), os.O_RDONLY)
                        os.fsync(dir_fd)
                        os.close(dir_fd)
                    else:
                        # 在 Windows 上，我们可以通过刷新父目录句柄来达到类似效果
                        # 但在 Python 中，这通常由底层操作系统自动处理
                        pass
                except (OSError, AttributeError):
                    # 在某些系统上可能不支持，非致命错误
                    self.logger.warning(f"[WRITE] Failed to fsync parent directory for {self.pid_file_path}")

        except Exception as e:
            self.logger.error(f"[WRITE] Error during atomic write: {str(e)}")
            raise
        finally:
            try:
                if os.path.exists(tmp_path):
                    for attempt in range(3):
                        try:
                            Path(tmp_path).unlink()
                            break
                        except OSError:
                            time.sleep(0.05)
            except Exception as e:
                self.logger.debug(f"[WRITE] Failed to cleanup temporary file {tmp_path}: {str(e)}")

    # ==========================================================
    # 读取（修复TOCTOU窗口，移除冗余检查）
    # ==========================================================

    def read(self, validate: bool = False) -> Optional[PidData]:
        with self._acquire_lock(write=False):
            # 移除冗余 exists() 检查，直接尝试打开文件
            try:
                # 使用 O_NOFOLLOW 防止符号链接攻击（仅在非Windows上）
                flags = os.O_RDONLY
                if sys.platform != 'win32' and hasattr(os, 'O_NOFOLLOW'):
                    flags |= os.O_NOFOLLOW
                
                fd = os.open(str(self.pid_file_path), flags)
                
                # 检查硬链接数量，防止TOCTOU攻击
                stat_info = os.fstat(fd)
                # 在 Windows 上跳过硬链接检查，因为 Windows 的硬链接行为不同
                if sys.platform != 'win32' and stat_info.st_nlink != 1:
                    os.close(fd)
                    raise PidFileError("PID file has multiple hard links")
                
                try:
                    with os.fdopen(fd, 'r', encoding="utf-8") as f:
                        content = f.read().strip()
                        
                    # 对 Windows 增加文件大小和 hash 检查
                    if sys.platform == 'win32':
                        file_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
                        expected_size = stat_info.st_size
                        actual_size = len(content.encode('utf-8'))
                        
                        # 检查文件大小是否匹配
                        if expected_size != actual_size:
                            raise PidFileError("File size mismatch - possible tampering")
                        
                except OSError as e:
                    os.close(fd)
                    self.logger.error(f"[READ] Failed to read PID file {self.pid_file_path}: {str(e)}")
                    raise PidFileError(f"Failed to read PID file: {e}") from e
            except FileNotFoundError:
                # 文件不存在，返回 None
                return None
            except OSError as e:
                self.logger.error(f"[READ] Failed to open PID file {self.pid_file_path}: {str(e)}")
                raise PidFileError(f"Failed to open PID file: {e}") from e

            if not content:
                raise PidFileError("PID file is empty")

            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                # 限制日志中的内容长度
                content_preview = content[:200] + "..." if len(content) > 200 else content
                masked_content = content_preview
                if "api_keys" in content_preview:
                    # 脱敏日志中的敏感信息
                    masked_content = re.sub(r'"api_keys"\s*:\s*"([^"]*)"', f'"api_keys":"{self.mask_sensitive("MASKED", "key")}"', content_preview)
                self.logger.error(f"[READ] Invalid JSON in PID file {self.pid_file_path}: {str(e)}, content preview: {masked_content}")
                raise PidFileError("PID file is not valid JSON") from e

            if not isinstance(data, dict):
                self.logger.error(f"[READ] PID file {self.pid_file_path} does not contain a JSON object")
                raise PidFileError("PID JSON must be an object")

            # 从数据中临时移除 _hash 字段进行验证
            original_data = {k: v for k, v in data.items() if k != '_hash'}
            
            # 哈希校验（Windows及其他平台）
            expected_hash = data.get('_hash')
            if expected_hash is not None:  # 如果存在哈希字段，则进行校验
                actual_hash = hashlib.sha256(json.dumps(original_data, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()
                if expected_hash != actual_hash:
                    raise PidFileError("PID file hash mismatch - possible tampering")

            # 只有在需要时才进行数据验证
            if validate:
                self._validate_pid_data(original_data)

            pid_data = PidData(**original_data)
            self.logger.info(f"Read data from file: host={pid_data.host}, port={pid_data.port}")
            return pid_data

    # ==========================================================
    # 安全删除（修复双重close和路径级TOCTOU，移除冗余检查）
    # ==========================================================

    def delete(self) -> None:
        with self._acquire_lock(write=True):
            # 移除冗余 exists() 检查，直接尝试删除
            try:
                # 使用 O_NOFOLLOW 防止符号链接攻击（仅在非Windows上）
                flags = os.O_RDONLY
                if sys.platform != 'win32' and hasattr(os, "O_NOFOLLOW"):
                    flags |= os.O_NOFOLLOW

                fd = os.open(str(self.pid_file_path), flags)
                try:
                    stat_info = os.fstat(fd)
                    # 在 Windows 上跳过硬链接检查
                    if sys.platform != 'win32' and stat_info.st_nlink != 1:
                        raise PidFileError(
                            "PID file has multiple hard links, refusing to delete"
                        )
                finally:
                    os.close(fd)

                # 使用目录文件描述符删除文件，避免路径重新解析（仅在非Windows上）
                if sys.platform != 'win32':
                    parent = self.pid_file_path.parent
                    dir_fd = os.open(str(parent), os.O_RDONLY | os.O_DIRECTORY)
                    try:
                        os.unlink(self.pid_file_path.name, dir_fd=dir_fd)
                    finally:
                        os.close(dir_fd)
                else:
                    # Windows 上直接使用 Path.unlink 删除文件
                    pid_path = Path(self.pid_file_path)
                    if pid_path.exists():
                        pid_path.unlink()
            except FileNotFoundError:
                # 文件不存在，什么都不做
                return
            except OSError as e:
                for attempt in range(3):
                    try:
                        os.remove(self.pid_file_path)
                        break
                    except OSError:
                        time.sleep(0.05)
                else:
                    self.logger.error(f"[DELETE] Failed to delete PID file {self.pid_file_path}: {str(e)}")
                    raise PidFileError(f"Failed to delete PID file: {e}") from e

    # ==========================================================
    # 写入（增加深拷贝和哈希校验）
    # ==========================================================

    def write(self, pid_data: PidData) -> None:
        if not isinstance(pid_data, PidData):
            raise ValueError("pid_data must be PidData instance")

        # 深拷贝 PidData 对象防止外部修改
        import copy
        copied_data = copy.deepcopy(pid_data)
        data = copied_data.__dict__.copy()

        self._validate_pid_data(data)

        # 从数据中排除 _hash 字段来计算哈希
        original_data = {k: v for k, v in data.items() if k != '_hash'}
        json_content_without_hash = json.dumps(original_data, ensure_ascii=False, sort_keys=True)
        hash_value = hashlib.sha256(json_content_without_hash.encode('utf-8')).hexdigest()
        
        # 将真实的哈希值添加到数据中
        data['_hash'] = hash_value

        with self._acquire_lock(write=True):
            with self._atomic_write() as f:
                json.dump(data, f, ensure_ascii=False)

    # ==========================================================
    # 获取 PID
    # ==========================================================

    def get_pid(self) -> Optional[int]:
        # Since PID field has been removed, this method now always returns None
        return None

    # ==========================================================
    # 构造命令
    # ==========================================================

    def get_cmd(self, pid_data=None) -> Optional[List[str]]:
        try:
            if pid_data is None:
                pid_data = self.read()
            if not pid_data:
                return None

            def quote_arg(arg: str) -> str:
                safe_arg = self.safe_shell_arg(arg)
                if sys.platform == "win32":
                    # Windows上不加引号以避免路径问题
                    return safe_arg
                # 其他平台上加引号保证参数完整性
                return f'"{safe_arg}"'

            cmd = [
                sys.executable,
                "-m",
                "src.llama.api.server",
                "--host", pid_data.host,
                "--port", str(pid_data.port),
            ]

            optional_map = {
                "--n-ctx": pid_data.n_ctx,
                "--n-threads": pid_data.n_threads,
                "--n-gpu-layers": pid_data.n_gpu_layers,
                "--n-batch": pid_data.n_batch,
                "--max-concurrent-requests": pid_data.max_concurrent_requests,
                "--rate-limit-requests": pid_data.rate_limit_requests,
                "--rate-limit-window": pid_data.rate_limit_window,
            }

            for flag, value in optional_map.items():
                if value is not None:
                    cmd.extend([flag, str(value)])

            if pid_data.model_path:
                # 移除model_path开头和结尾的引号
                cleaned_model_path = re.sub(r'^["\']+|["\']+$', '', pid_data.model_path)
                cmd.extend(["--model-path", quote_arg(cleaned_model_path)])
            if pid_data.api_keys:
                cmd.extend(["--api-keys", quote_arg(pid_data.api_keys)])
            if pid_data.debug:
                cmd.append("--debug")

            return cmd
        except PidFileError as e:
            self.logger.warning(f"[GET_CMD] Failed to read PID data: {str(e)}")
            return None

    # ==========================================================
    # 更新 PID - 现在已废弃
    # ==========================================================

    def set_pid(self, pid: int) -> None:
        # Since PID field has been removed, this method is now deprecated
        pass
