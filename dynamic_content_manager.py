import asyncio
import time
from typing import Callable, Dict, Any

class DynamicContentManager:
    def __init__(self):
        self.content: Dict[str, Any] = {}
        self.update_functions: Dict[str, Callable] = {}
        self.update_intervals: Dict[str, int] = {}
        self.last_update_time: Dict[str, float] = {}

    async def add_content(self, key: str, update_function: Callable, update_interval: int):
        """Add a new piece of content to manage."""
        self.update_functions[key] = update_function
        self.update_intervals[key] = update_interval
        self.last_update_time[key] = 0
        await self.update_content(key)

    async def update_content(self, key: str):
        """Update a specific piece of content."""
        try:
            self.content[key] = await self.update_functions[key]()
            self.last_update_time[key] = time.time()
        except Exception as e:
            print(f"Error updating content for {key}: {e}")

    async def get_content(self, key: str):
        """Get content, updating it if necessary."""
        current_time = time.time()
        if current_time - self.last_update_time.get(key, 0) > self.update_intervals[key]:
            await self.update_content(key)
        return self.content.get(key)

    async def run_updates(self):
        """Continuously update all content at their specified intervals."""
        while True:
            for key in self.update_functions.keys():
                if time.time() - self.last_update_time.get(key, 0) > self.update_intervals[key]:
                    await self.update_content(key)
            await asyncio.sleep(60)  # Check every minute