from __future__ import annotations

import itertools
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .backends import BackendUnavailable, CrackBackend, get_backend


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


def crack_file(
    target: Path,
    wordlist: Path,
    workers: int = 4,
    encoding: str = "utf-8",
    force_format: str | None = None,
    chunk_size: int = 512,
) -> CrackResult:
    target = target.expanduser().resolve()
    wordlist = wordlist.expanduser().resolve()
    if not target.exists():
        raise FileNotFoundError(f"目标文件不存在：{target}")
    if not wordlist.exists():
        raise FileNotFoundError(f"字典文件不存在：{wordlist}")

    backend = get_backend(target, force_format=force_format)
    stop_event = threading.Event()
    attempts = 0
    start = time.perf_counter()

    try:
        with ThreadPoolExecutor(max_workers=max(workers, 1)) as executor:
            passwords = load_wordlist(wordlist, encoding=encoding)
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
                    batch_attempts = futures.pop(future)
                    attempts += batch_attempts
                    password = future.result()
                    if password is not None:
                        stop_event.set()
                        elapsed = time.perf_counter() - start
                        return CrackResult(True, password, attempts, elapsed, backend.name)

            elapsed = time.perf_counter() - start
            return CrackResult(False, None, attempts, elapsed, backend.name)
    except BackendUnavailable as exc:
        elapsed = time.perf_counter() - start
        return CrackResult(False, None, attempts, elapsed, backend.name, error=str(exc))


def _try_batch(backend: CrackBackend, target: Path, passwords: list[str], stop_event: threading.Event) -> str | None:
    for password in passwords:
        if stop_event.is_set():
            return None
        if backend.verify(target, password):
            return password
    return None
