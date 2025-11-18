import { useState, useEffect } from 'react'
import axios from 'axios'
import './App.css'

const API_URL = import.meta.env.PROD ? '/api' : 'http://localhost:8000'

function App() {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/metrics`)
        setMetrics(response.data)
        setLoading(false)
      } catch (err) {
        setError(err.message)
        setLoading(false)
      }
    }

    // Fetch immediately
    fetchMetrics()

    // Then fetch every 2 seconds
    const interval = setInterval(fetchMetrics, 2000)

    return () => clearInterval(interval)
  }, [])

  if (loading) return <div>Loading...</div>
  if (error) return <div>Error: {error}</div>
  if (!metrics) return <div>No data</div>

  return (
    <div className="App">
      <h1>Raspberry Pi Dashboard</h1>
      
      <div className="metrics-grid">
        <div className="metric-card">
          <h2>CPU Usage</h2>
          <div className="metric-value">{metrics.cpu.percent.toFixed(1)}%</div>
        </div>

        <div className="metric-card">
          <h2>Memory</h2>
          <div className="metric-value">{metrics.memory.percent.toFixed(1)}%</div>
          <div className="metric-detail">
            {(metrics.memory.used / 1024 / 1024 / 1024).toFixed(2)} GB / 
            {(metrics.memory.total / 1024 / 1024 / 1024).toFixed(2)} GB
          </div>
        </div>

        <div className="metric-card">
          <h2>Disk Usage</h2>
          <div className="metric-value">{metrics.disk.percent.toFixed(1)}%</div>
          <div className="metric-detail">
            {(metrics.disk.used / 1024 / 1024 / 1024).toFixed(2)} GB / 
            {(metrics.disk.total / 1024 / 1024 / 1024).toFixed(2)} GB
          </div>
        </div>

        <div className="metric-card">
          <h2>Temperature</h2>
          {metrics.temperature.thermal_zones && metrics.temperature.thermal_zones.length > 0 ? (
            <div className="metric-value">
              {metrics.temperature.thermal_zones[0].temperature.toFixed(1)}°C
            </div>
          ) : (
            <div className="metric-value">N/A</div>
          )}
        </div>

        <div className="metric-card">
          <h2>Network</h2>
          <div className="metric-detail">
            ↓ {(metrics.network.bytes_recv / 1024 / 1024).toFixed(2)} MB
          </div>
          <div className="metric-detail">
            ↑ {(metrics.network.bytes_sent / 1024 / 1024).toFixed(2)} MB
          </div>
        </div>

        <div className="metric-card">
          <h2>Uptime</h2>
          <div className="metric-value">{metrics.uptime.uptime_formatted}</div>
        </div>
      </div>
    </div>
  )
}

export default App