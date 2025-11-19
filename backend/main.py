from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager

from metrics.collectors import (
    get_cpu_usage,
    get_memory_usage,
    get_disk_usage,
    get_temperature,
    get_network_stats,
    get_system_uptime
)
from metrics.docker_collectors import get_docker_containers, get_docker_images
from database import init_database, cleanup_old_data
from metrics_history import metrics_history
from service_health import service_health_checker


async def collect_metrics_task():
    """Background task to collect metrics every 2 seconds"""
    while True:
        try:
            timestamp = datetime.now().timestamp()

            # Collect system metrics
            cpu_data = get_cpu_usage()
            memory_data = get_memory_usage()
            disk_data = get_disk_usage()
            temp_data = get_temperature()
            network_data = get_network_stats()

            # Store in history
            await metrics_history.add_metric('cpu', cpu_data, timestamp)
            await metrics_history.add_metric('memory', memory_data, timestamp)
            await metrics_history.add_metric('disk', disk_data, timestamp)
            await metrics_history.add_metric('temperature', temp_data, timestamp)
            await metrics_history.add_metric('network', network_data, timestamp)

            # Collect Docker metrics
            docker_containers = get_docker_containers()
            if 'containers' in docker_containers:
                for container in docker_containers['containers']:
                    await metrics_history.add_docker_metric(
                        container['name'],
                        container,
                        timestamp
                    )

            # Flush to database periodically
            await metrics_history.flush_to_database()
        except Exception as e:
            print(f"Error collecting metrics: {e}")
        await asyncio.sleep(2)

async def check_service_health_task():
    """Background task to check service health every 10 seconds"""
    while True:
        try:
            await service_health_checker.check_all_services()
        except Exception as e:
            print(f"Error checking service health: {e}")
        await asyncio.sleep(10)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""

    # Startup
    init_database()
    print("Database initialized")

    # Start background metrics collection
    metrics_task = asyncio.create_task(collect_metrics_task())
    print("Metrics collection started")
    
    # Start background service health checks
    health_task = asyncio.create_task(check_service_health_task())
    print("Service health checks started")
    
    yield

    # Shutdown
    metrics_task.cancel()
    health_task.cancel()

    try:
        await metrics_task
    except asyncio.CancelledError:
        pass
    
    try:
        await health_task
    except asyncio.CancelledError:
        pass
    
    print("Background tasks stopped")

app = FastAPI(title="Pi Dashboard API", lifespan=lifespan)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175"],  # have some options
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Pi Dashboard API"}

@app.get("/api/metrics")
def get_metrics():
    return {
        "cpu": get_cpu_usage(),
        "memory": get_memory_usage(),
        "disk": get_disk_usage(),
        "temperature": get_temperature(),
        "network": get_network_stats(),
        "uptime": get_system_uptime()
    }

@app.get("/api/docker")
def get_docker_info():
    return {
        "containers": get_docker_containers(),
        "images": get_docker_images()
    }

@app.get("/api/metrics/cpu")
def get_cpu():
    return get_cpu_usage()

@app.get("/api/metrics/memory")
def get_memory():
    return get_memory_usage()

@app.get("/api/metrics/disk")
def get_disk():
    return get_disk_usage()

@app.get("/api/metrics/temperature")
def get_temp():
    return get_temperature()

@app.get("/api/metrics/network")
def get_network():
    return get_network_stats()

@app.get("/api/docker/containers")
def get_containers():
    return get_docker_containers()

@app.get("/api/docker/images")
def get_images():
    return get_docker_images()


# Historical metrics endpoints
@app.get("/api/metrics/history/{metric_type}")
async def get_metric_history(
    metric_type: str,
    range: int = Query(default=5, description="Time range in minutes (5, 15, 60, 360, 1440)")

):
    """Get historical data for a specific metric type"""
    valid_metrics = ['cpu', 'memory', 'disk', 'temperature', 'network']
    if metric_type not in valid_metrics:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid metric type. Must be one of: {valid_metrics}"
        )

    valid_ranges = [5, 15, 60, 360, 1440]
    if range not in valid_ranges:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid range. Must be one of: {valid_ranges}"
        )

    data = await metrics_history.get_historical_metrics(metric_type, range)

    return {
        "metric_type": metric_type,
        "range_minutes": range,
        "data": data
    }

@app.get("/api/docker/history/{container_name}")
async def get_docker_container_history(
    container_name: str,
    range: int = Query(default=5, description="Time range in minutes (5, 15, 60, 360, 1440)")
):
    """Get historical data for a specific Docker container"""
    valid_ranges = [5, 15, 60, 360, 1440]
    if range not in valid_ranges:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid range. Must be one of: {valid_ranges}"
        )

    data = await metrics_history.get_historical_docker_metrics(container_name, range)

    return {
        "container_name": container_name,
        "range_minutes": range,
        "data": data
    }


@app.get("/api/docker/containers/list")
async def get_container_names():
    """Get list of all tracked containers"""
    return {
        "containers": await metrics_history.get_all_container_names()
    }

@app.get("/api/services/health")
def get_services_health():
    """Get health status of all external services"""
    return {
        "services": service_health_checker.get_all_health_status()
    }

@app.post("/api/admin/cleanup")
def cleanup_old_metrics(days: int = Query(default=7, description="Delete data older than X days")):
    """Clean up old metrics data (admin endpoint)"""
    deleted = cleanup_old_data(days)
    return {
        "deleted_count": deleted,
        "days": days
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)