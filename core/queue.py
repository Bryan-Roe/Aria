"""
Aria Async Task Queue
"""

import asyncio

class TaskQueue:
    def __init__(self, max_workers=5):
        self.queue = asyncio.Queue()
        self.max_workers = max_workers
        self.workers = []
        self.running = False

    async def add_task(self, task):
        await self.queue.put(task)

    async def worker(self, handler):
        while self.running:
            task = await self.queue.get()
            try:
                await handler(task)
            except Exception as e:
                print("[Queue error]", e)
            finally:
                self.queue.task_done()

    async def start(self, handler):
        self.running = True
        for _ in range(self.max_workers):
            self.workers.append(asyncio.create_task(self.worker(handler)))

    async def stop(self):
        self.running = False
        await self.queue.join()
        for w in self.workers:
            w.cancel()
