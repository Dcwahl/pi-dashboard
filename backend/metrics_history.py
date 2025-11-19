from collections import deque
from datetime import datetime, timedelta
import asyncio
import time
from typing import Dict, List
from database import insert_metric, insert_docker_metric, get_metrics_range, get_docker_metrics_range

class MetricsHistory:
    """Manages in-memory metrics buffer and database persistence"""

    def __init__(self, buffer_size: int = 450):  # 15 min at 2-sec intervals
        self.buffer_size = buffer_size
        self.metrics_buffer: Dict[str, deque] = {
            'cpu': deque(maxlen=buffer_size),
            'memory': deque(maxlen=buffer_size),
            'disk': deque(maxlen=buffer_size),
            'temperature': deque(maxlen=buffer_size),
            'network': deque(maxlen=buffer_size),
        }
        self.docker_buffer: Dict[str, deque] = {}  # container_name -> deque
        self.lock = asyncio.Lock()
        self.last_flush = time.time()
        self.flush_interval = 60  # Flush to DB every 60 seconds
        # Track last flushed timestamp to avoid duplicates
        self.last_flushed_timestamp: Dict[str, float] = {}
        self.last_flushed_docker_timestamp: Dict[str, float] = {}

    async def add_metric(self, metric_type: str, data: dict, timestamp: float = None):
        """Add a metric to the in-memory buffer"""
        if timestamp is None:
            timestamp = datetime.now().timestamp()

        async with self.lock:
            if metric_type in self.metrics_buffer:
                self.metrics_buffer[metric_type].append({
                    'timestamp': timestamp,
                    'data': data
                })

    async def add_docker_metric(self, container_name: str, data: dict, timestamp: float = None):
        """Add a Docker metric to the in-memory buffer"""
        if timestamp is None:
            timestamp = datetime.now().timestamp()

        async with self.lock:
            if container_name not in self.docker_buffer:
                self.docker_buffer[container_name] = deque(maxlen=self.buffer_size)

            self.docker_buffer[container_name].append({
                'timestamp': timestamp,
                'data': data
            })

    async def get_recent_metrics(self, metric_type: str, minutes: int = 15) -> List[dict]:
        """Get recent metrics from in-memory buffer"""
        cutoff_time = (datetime.now() - timedelta(minutes=minutes)).timestamp()

        async with self.lock:
            if metric_type not in self.metrics_buffer:
                return []

            return [
                entry for entry in self.metrics_buffer[metric_type]
                if entry['timestamp'] >= cutoff_time
            ]

    async def get_recent_docker_metrics(self, container_name: str, minutes: int = 15) -> List[dict]:
        """Get recent Docker metrics from in-memory buffer"""
        cutoff_time = (datetime.now() - timedelta(minutes=minutes)).timestamp()

        async with self.lock:
            if container_name not in self.docker_buffer:
                return []

            return [
                entry for entry in self.docker_buffer[container_name]
                if entry['timestamp'] >= cutoff_time
            ]

    async def get_historical_metrics(self, metric_type: str, range_minutes: int) -> List[dict]:
        """Get historical metrics, combining in-memory and database"""
        now = datetime.now()
        start_time = (now - timedelta(minutes=range_minutes)).timestamp()

        # For ranges <= 15 minutes, use in-memory buffer
        if range_minutes <= 15:
            return await self.get_recent_metrics(metric_type, range_minutes)

        # For longer ranges, query database
        db_results = get_metrics_range(metric_type, start_time)

        # If we have recent data in memory that's not in DB yet, append it
        recent_buffer = await self.get_recent_metrics(metric_type, 5)
        if recent_buffer and db_results:
            last_db_time = db_results[-1]['timestamp']
            newer_buffer = [entry for entry in recent_buffer if entry['timestamp'] > last_db_time]
            db_results.extend(newer_buffer)
        elif recent_buffer and not db_results:
            # No DB results, just return buffer
            return recent_buffer

        return db_results

    async def get_historical_docker_metrics(self, container_name: str, range_minutes: int) -> List[dict]:
        """Get historical Docker metrics, combining in-memory and database"""
        now = datetime.now()
        start_time = (now - timedelta(minutes=range_minutes)).timestamp()

        # For ranges <= 15 minutes, use in-memory buffer
        if range_minutes <= 15:
            return await self.get_recent_docker_metrics(container_name, range_minutes)

        # For longer ranges, query database
        db_results = get_docker_metrics_range(container_name, start_time)

        # If we have recent data in memory that's not in DB yet, append it
        recent_buffer = await self.get_recent_docker_metrics(container_name, 5)
        if recent_buffer and db_results:
            last_db_time = db_results[-1]['timestamp']
            newer_buffer = [entry for entry in recent_buffer if entry['timestamp'] > last_db_time]
            db_results.extend(newer_buffer)
        elif recent_buffer and not db_results:
            # No DB results, just return buffer
            return recent_buffer

        return db_results

    async def flush_to_database(self):
        """Flush old buffer entries to database"""
        current_time = time.time()

        # Only flush if enough time has passed
        if current_time - self.last_flush < self.flush_interval:
            return

        async with self.lock:
            flush_cutoff = (datetime.now() - timedelta(minutes=5)).timestamp()

            # Flush system metrics
            for metric_type, buffer in self.metrics_buffer.items():
                if len(buffer) > 0:
                    # Get last flushed timestamp for this metric type
                    last_flushed = self.last_flushed_timestamp.get(metric_type, 0)
                    max_flushed_timestamp = last_flushed

                    for entry in buffer:
                        # Only flush if: older than 5 min AND newer than last flush
                        if entry['timestamp'] < flush_cutoff and entry['timestamp'] > last_flushed:
                            insert_metric(metric_type, entry['data'], entry['timestamp'])
                            max_flushed_timestamp = max(max_flushed_timestamp, entry['timestamp'])

                    # Update last flushed timestamp
                    if max_flushed_timestamp > last_flushed:
                        self.last_flushed_timestamp[metric_type] = max_flushed_timestamp

            # Flush Docker metrics
            for container_name, buffer in self.docker_buffer.items():
                if len(buffer) > 0:
                    # Get last flushed timestamp for this container
                    last_flushed = self.last_flushed_docker_timestamp.get(container_name, 0)
                    max_flushed_timestamp = last_flushed

                    for entry in buffer:
                        # Only flush if: older than 5 min AND newer than last flush
                        if entry['timestamp'] < flush_cutoff and entry['timestamp'] > last_flushed:
                            # Extract container_id from data if available
                            container_id = entry['data'].get('id', '')
                            insert_docker_metric(container_id, container_name, entry['data'], entry['timestamp'])
                            max_flushed_timestamp = max(max_flushed_timestamp, entry['timestamp'])

                    # Update last flushed timestamp
                    if max_flushed_timestamp > last_flushed:
                        self.last_flushed_docker_timestamp[container_name] = max_flushed_timestamp

            self.last_flush = current_time

    async def get_all_container_names(self) -> List[str]:
        """Get list of all containers in the buffer"""
        async with self.lock:
            return list(self.docker_buffer.keys())


# Global instance
metrics_history = MetricsHistory()