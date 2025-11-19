import docker
from docker.errors import DockerException

def get_docker_client():
    """Get Docker client"""
    try:
        return docker.from_env()
    except DockerException as e:
        return None

def get_docker_containers():
    """Get information about all Docker containers"""
    client = get_docker_client()
    if not client:
        return {"error": "Cannot connect to Docker daemon"}
    
    try:
        containers = client.containers.list(all=True)
        
        container_info = []
        for container in containers:
            # Stats collection commented out for performance - very slow on some systems
            # Uncomment if you need per-container CPU/memory/network stats
            # stats = None
            # if container.status == 'running':
            #     try:
            #         # Get stats without streaming
            #         stats_stream = container.stats(stream=False)
            #         stats = {
            #             "cpu_percent": calculate_cpu_percent(stats_stream),
            #             "memory_usage": stats_stream['memory_stats'].get('usage', 0),
            #             "memory_limit": stats_stream['memory_stats'].get('limit', 0),
            #             "memory_percent": calculate_memory_percent(stats_stream),
            #             "network_rx": get_network_rx(stats_stream),
            #             "network_tx": get_network_tx(stats_stream),
            #         }
            #     except Exception:
            #         stats = None

            container_info.append({
                "id": container.short_id,
                "name": container.name,
                "image": container.image.tags[0] if container.image.tags else "unknown",
                "status": container.status,
                "state": container.attrs['State'],
                "created": container.attrs['Created'],
                "stats": None  # Stats disabled for performance
            })
        
        return {
            "containers": container_info,
            "total": len(containers),
            "running": len([c for c in containers if c.status == 'running']),
            "stopped": len([c for c in containers if c.status == 'exited']),
        }
    except Exception as e:
        return {"error": str(e)}

def calculate_cpu_percent(stats):
    """Calculate CPU percentage from Docker stats"""
    try:
        cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                   stats['precpu_stats']['cpu_usage']['total_usage']
        system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                      stats['precpu_stats']['system_cpu_usage']
        
        if system_delta > 0 and cpu_delta > 0:
            cpu_percent = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100.0
            return round(cpu_percent, 2)
    except (KeyError, ZeroDivisionError):
        pass
    return 0.0

def calculate_memory_percent(stats):
    """Calculate memory percentage from Docker stats"""
    try:
        usage = stats['memory_stats'].get('usage', 0)
        limit = stats['memory_stats'].get('limit', 0)
        if limit > 0:
            return round((usage / limit) * 100, 2)
    except (KeyError, ZeroDivisionError):
        pass
    return 0.0

def get_network_rx(stats):
    """Get network received bytes"""
    try:
        networks = stats.get('networks', {})
        total_rx = sum(net.get('rx_bytes', 0) for net in networks.values())
        return total_rx
    except Exception:
        return 0

def get_network_tx(stats):
    """Get network transmitted bytes"""
    try:
        networks = stats.get('networks', {})
        total_tx = sum(net.get('tx_bytes', 0) for net in networks.values())
        return total_tx
    except Exception:
        return 0

def get_docker_images():
    """Get information about Docker images"""
    client = get_docker_client()
    if not client:
        return {"error": "Cannot connect to Docker daemon"}
    
    try:
        images = client.images.list()
        
        image_info = []
        for image in images:
            image_info.append({
                "id": image.short_id,
                "tags": image.tags,
                "size": image.attrs.get('Size', 0),
                "created": image.attrs.get('Created', ''),
            })
        
        return {
            "images": image_info,
            "total": len(images)
        }
    except Exception as e:
        return {"error": str(e)}