"""
Aria Async Task Queue
"""

from __future__ import annotations

import asyncio
from contextlib import suppress
from typing import Any, Awaitable, Callable, Generic, TypeVar


_STOP = object()
TTask = TypeVar("TTask")


TaskHandler = Callable[[TTask], Awaitable[Any]]


class TaskQueue(Generic[TTask]):
    def __init__(self, max_workers: int = 5):
        if not isinstance(max_workers, int) or max_workers < 1:
            raise ValueError("max_workers must be a positive integer")

        self.queue: asyncio.Queue[TTask | object] = asyncio.Queue()
        self.max_workers = max_workers
        self.workers: list[asyncio.Task[None]] = []
        self.running = False

    async def add_task(self, task: TTask) -> None:
        if not self.running:
            raise RuntimeError(
                "TaskQueue is not running. Call start() before add_task().")
        await self.queue.put(task)

    async def worker(self, handler: TaskHandler[TTask]) -> None:
        while True:
            task = await self.queue.get()
            try:
                if task is _STOP:
                    return
                await handler(task)
            except Exception as e:
                print("[Queue error]", e)
            finally:
                self.queue.task_done()

    async def start(self, handler: TaskHandler[TTask]) -> None:
        if self.running:
            return
        self.running = True
        for _ in range(self.max_workers):
            self.workers.append(asyncio.create_task(self.worker(handler)))

    async def stop(self) -> None:
        if not self.running:
            return
        self.running = False
        for _ in self.workers:
            await self.queue.put(_STOP)
        await self.queue.join()
        for w in self.workers:
            w.cancel()
            with suppress(asyncio.CancelledError):
                await w
        self.workers.clear()

    async def join(self) -> None:
        """Wait until all queued work is processed."""
        await self.queue.join()

    def pending_count(self) -> int:
        return self.queue.qsize()
