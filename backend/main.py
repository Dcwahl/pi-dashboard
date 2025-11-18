from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from metrics.collectors import (
    get_cpu_usage,
    get_memory_usage,
    get_disk_usage,
    get_temperature,
    get_network_stats,
    get_system_uptime
)
from metrics.docker_collectors import get_docker_containers, get_docker_images

app = FastAPI(title="Pi Dashboard API")

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)