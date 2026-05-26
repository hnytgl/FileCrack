from __future__ import annotations

import itertools
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .backends import BackendUnavailable, CrackBackend, get_backend


WEAK_PASSWORDS = [
    "123456",
    "123456789",
    "12345678",
    "111111",
    "000000",
    "password",
    "admin",
    "qwerty",
    "abc123",
    "123123",
    "iloveyou",
    "letmein",
    "welcome",
    "root",
    "passw0rd",
    "p@ssw0rd",
    "password1",
    "888888",
    "666666",
    "1q2w3e4r",
    "qwer1234",
    "abcd1234",
    "1234567890",
]


@dataclass(frozen=True)
class CrackResult:
    found: bool
    password: str | None
    attempts: int
    elapsed_seconds: float
    backend: str
    error: str | None = None

    @property
    def speed(self) -> float:
        if self.elapsed_seconds <= 0:
            return 0.0
        return self.attempts / self.elapsed_seconds


def load_wordlist(path: Path, encoding: str = "utf-8") -> Iterable[str]:
    with path.open("r", encoding=encoding, errors="ignore") as handle:
        for line in handle:
            password = line.rstrip("\r\n")
            if password:
                yield password


def build_candidates(
    single_password: str | None = None,
    weak_check: bool = False,
    wordlist: Path | None = None,
    encoding: str = "utf-8",
) -> Iterable[str]:
    seen: set[str] = set()

    def emit(passwords: Iterable[str]) -> Iterable[str]:
        for password in passwords:
            if password not in seen:
                seen.add(password)
                yield password

    if single_password is not None:
        yield from emit([single_password])
    if weak_check:
        yield from emit(WEAK_PASSWORDS)
    if wordlist is not None:
        yield from emit(load_wordlist(wordlist, encoding=encoding))


def crack_file(
    target: Path,
    wordlist: Path | None = None,
    workers: int = 4,
    encoding: str = "utf-8",
    force_format: str | None = None,
    chunk_size: int = 512,
    single_password: str | None = None,
    weak_check: bool = False,
) -> CrackResult:
    target = target.expanduser().resolve()
    if not target.exists():
        raise FileNotFoundError(f"目标文件不存在：{target}")
    if wordlist is not None:
        wordlist = wordlist.expanduser().resolve()
        if not wordlist.exists():
            raise FileNotFoundError(f"字典文件不存在：{wordlist}")
    if single_password is None and not weak_check and wordlist is None:
        raise ValueError("请至少提供 --password、--weak-check 或 --wordlist 中的一种密码来源。")

    backend = get_backend(target, force_format=force_format)
    stop_event = threading.Event()
    attempts = 0
    start = time.perf_counter()

    try:
        with ThreadPoolExecutor(max_workers=max(workers, 1)) as executor:
            passwords = build_candidates(
                single_password=single_password,
                weak_check=weak_check,
                wordlist=wordlist,
                encoding=encoding,
            )
            futures = {}

            while not stop_event.is_set():
                while len(futures) < max(workers, 1) * chunk_size:
                    batch = list(itertools.islice(passwords, chunk_size))
                    if not batch:
                        break
                    future = executor.submit(_try_batch, backend, target, batch, stop_event)
                    futures[future] = len(batch)

                if not futures:
                    break

                done, _ = wait(futures, return_when=FIRST_COMPLETED)
                for future in done:
                    futures.pop(future)
                    password, batch_attempts = future.result()
                    attempts += batch_attempts
                    if password is not None:
                        stop_event.set()
                        elapsed = time.perf_counter() - start
                        return CrackResult(True, password, attempts, elapsed, backend.name)

            elapsed = time.perf_counter() - start
            return CrackResult(False, None, attempts, elapsed, backend.name)
    except BackendUnavailable as exc:
        elapsed = time.perf_counter() - start
        return CrackResult(False, None, attempts, elapsed, backend.name, error=str(exc))


def _try_batch(
    backend: CrackBackend,
    target: Path,
    passwords: list[str],
    stop_event: threading.Event,
) -> tuple[str | None, int]:
    attempts = 0
    for password in passwords:
        if stop_event.is_set():
            return None, attempts
        attempts += 1
        if backend.verify(target, password):
            return password, attempts
    return None, attempts
