# Pi Dashboard - Architecture Notes

## Current Architecture

### Background Tasks

1. **Metrics Collection** (every 2 seconds)
   - Collects: CPU, memory, disk, temperature, network
   - Stores in in-memory buffer + SQLite database
   - **Why**: Historical data is used by CPUChart component and future time-range charts
   - Database flush: every 60 seconds

2. **Service Health Checks** (every 10 seconds)
   - Checks external services defined in `backend/services.json`
   - Results are cached and returned via `/api/services/health`

### API Endpoints (polled by frontend every 5 seconds)

- `/api/metrics` - Real-time system metrics (fresh collection)
- `/api/docker` - Docker containers/images (fast, stats disabled)
- `/api/services/health` - Cached health check results

## Design Decisions

### Why collect metrics in background AND on API calls?
- **Background task**: Builds historical database for charts
- **API endpoint**: Returns fresh data for real-time display
- These serve different purposes and both are needed

### Why are Docker stats disabled?
- `container.stats()` is extremely slow (1-2 seconds per container)
- Caused request stacking even at 5-second intervals
- User doesn't need per-container CPU/memory/network stats currently
- Can be re-enabled in `backend/metrics/docker_collectors.py` lines 22-38 if needed

### Why use 172.17.0.1 for external services?
- Backend runs in Docker container
- `localhost` inside container != host machine
- `172.17.0.1` is Docker bridge gateway to reach host services

## Future Plans

### Time Range Buttons
- Add UI controls for: Now / 5min / 15min / 1hr / 6hr / 24hr
- Backend already supports this via `/api/metrics/history/{metric_type}?range={minutes}`
- Valid ranges: 5, 15, 60, 360, 1440 (minutes)

### Potential Improvements
- Cache system metrics from background task instead of fresh collection on API calls
- Add more charts for memory, disk, temperature, network
- Optional Docker stats with longer cache TTL (if needed later)

## Performance Notes

- Docker stats collection was the main bottleneck (removed)
- Historical metrics are essential for charts - don't remove background task
- Frontend polling at 5 seconds is reasonable for real-time monitoring
