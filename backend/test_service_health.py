#!/usr/bin/env python3
"""Quick test script to verify service health endpoint"""
import asyncio
from service_health import service_health_checker

async def test_health_check():
    print("Testing service health checker...")
    print(f"Loaded services: {[s['name'] for s in service_health_checker.services]}")
    
    # Run health checks
    await service_health_checker.check_all_services()
    
    # Get results
    results = service_health_checker.get_all_health_status()
    
    print("\nHealth Check Results:")
    for service in results:
        print(f"  {service['name']}: {service['status']}")
        if service['error']:
            print(f"    Error: {service['error']}")
        if service['response_time_ms']:
            print(f"    Response Time: {service['response_time_ms']}ms")
    
    return results

if __name__ == "__main__":
    asyncio.run(test_health_check())
