from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import __version__
from .backends import UnsupportedFormat
from .core import crack_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="filecrack",
        description="授权场景下的常见加密文件密码恢复工具，支持单密码、弱密码、字典和多线程尝试。",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("target", help="需要恢复密码的文件路径。")
    parser.add_argument("-p", "--password", help="单个密码尝试。")
    parser.add_argument("-w", "--wordlist", help="密码字典路径，每行一个候选密码。")
    parser.add_argument("--weak-check", action="store_true", help="启用内置弱密码检查。")
    parser.add_argument("-t", "--threads", type=int, default=os.cpu_count() or 4, help="线程数，默认使用 CPU 核心数。")
    parser.add_argument("--encoding", default="utf-8", help="字典文件编码，默认 utf-8。")
    parser.add_argument("--format", help="默认自动识别格式；必要时可强制指定 zip、rar、7z、pdf、docx、xlsx。")
    parser.add_argument("--chunk-size", type=int, default=512, help="每个任务批量尝试的密码数量。")
    parser.add_argument("--quiet", action="store_true", help="只输出找到的密码，便于脚本调用。")
    return parser


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        result = crack_file(
            Path(args.target),
            Path(args.wordlist) if args.wordlist else None,
            workers=args.threads,
            encoding=args.encoding,
            force_format=args.format,
            chunk_size=args.chunk_size,
            single_password=args.password,
            weak_check=args.weak_check,
        )
    except (FileNotFoundError, ValueError, UnsupportedFormat) as exc:
        parser.error(str(exc))

    if args.quiet:
        if result.found and result.password is not None:
            print(result.password)
        return 0 if result.found else 1

    print(f"格式后端：{result.backend}")
    print(f"尝试次数：{result.attempts}")
    print(f"耗时：{result.elapsed_seconds:.2f}s")
    print(f"速度：{result.speed:.2f} passwords/s")

    if result.error:
        print(f"错误：{result.error}")
        return 2

    if result.found:
        print(f"密码找到：{result.password}")
        return 0

    print("未在字典中找到密码。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
