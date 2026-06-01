"""
error_codes.py — 系统调用错误码定义

所有 sys_* 函数在出错时返回对应错误码。
返回值约定：
  - 成功：返回正常值（如 PID、exit_code）
  - 失败：返回对应错误码（负数或特殊字符串）
"""


class ErrorCode:
    """系统调用错误码"""

    # 成功
    SUCCESS = 0

    # 进程相关错误
    ECHILD = -1      # 没有子进程（waitpid 时没有可等待的子进程）
    EAGAIN = -2      # 资源限制，无法创建更多进程（fork bomb 防护）
    EINVAL = -3      # 无效参数（如 priority 超出范围）
    ESRCH = -4       # 进程不存在（指定的 PID 找不到）
    ENOMEM = -5      # 内存不足（物理帧耗尽且无法置换）
    EPERM = -6       # 权限不足（如试图 kill init 进程）

    # 特殊状态（非错误）
    BLOCKED = "BLOCKED"  # waitpid 阻塞中，父进程进入 SLEEPING 状态

    @classmethod
    def is_error(cls, value) -> bool:
        """判断返回值是否为错误码"""
        if isinstance(value, int):
            return value < 0
        return False

    @classmethod
    def to_string(cls, code: int) -> str:
        """将错误码转换为可读字符串"""
        error_map = {
            cls.SUCCESS: "SUCCESS (成功)",
            cls.ECHILD: "ECHILD (没有子进程)",
            cls.EAGAIN: "EAGAIN (资源限制，进程数已满)",
            cls.EINVAL: "EINVAL (无效参数)",
            cls.ESRCH: "ESRCH (进程不存在)",
            cls.ENOMEM: "ENOMEM (内存不足)",
            cls.EPERM: "EPERM (权限不足)",
        }
        return error_map.get(code, f"UNKNOWN ({code})")
