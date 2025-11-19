import { useState, useEffect } from 'react'
import axios from 'axios'
import './App.css'
import CPUChart from './components/CPUChart'

const API_URL = import.meta.env.PROD ? '' : 'http://localhost:8000'

function App() {
  const [metrics, setMetrics] = useState(null)
  const [dockerData, setDockerData] = useState(null)
  const [servicesHealth, setServicesHealth] = useState(null)
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

    const fetchDocker = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/docker`)
        setDockerData(response.data)
      } catch (err) {
        console.error('Docker fetch error:', err)
      }
    }

    const fetchServicesHealth = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/services/health`)
        setServicesHealth(response.data)
      } catch (err) {
        console.error('Services health fetch error:', err)
      }
    }

    // Fetch immediately
    fetchMetrics()
    fetchDocker()
    fetchServicesHealth()

    // Then fetch every 2 seconds
    const interval = setInterval(() => {
      fetchMetrics()
      fetchDocker()
      fetchServicesHealth()
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  if (loading) return <div>Loading...</div>
  if (error) return <div>Error: {error}</div>
  if (!metrics) return <div>No data</div>

  return (
    <div className="App">
      <h1>Raspberry Pi Dashboard</h1>

      <div className="metrics-grid">
        <CPUChart />

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

      {dockerData && (
        <div className="docker-section">
          <h2 className="section-title">Docker Status</h2>

          {/* Docker Overview */}
          <div className="docker-overview">
            <div className="metric-card">
              <h2>Containers</h2>
              <div className="metric-value">{dockerData.containers.running}/{dockerData.containers.total}</div>
              <div className="metric-detail">
                <span className="status-running">{dockerData.containers.running} running</span>
                {dockerData.containers.stopped > 0 && (
                  <span className="status-stopped"> • {dockerData.containers.stopped} stopped</span>
                )}
              </div>
            </div>

            <div className="metric-card">
              <h2>Images</h2>
              <div className="metric-value">{dockerData.images.total}</div>
              <div className="metric-detail">
                {(dockerData.images.images.reduce((acc, img) => acc + img.size, 0) / 1024 / 1024).toFixed(0)} MB total
              </div>
            </div>
          </div>

          {/* Container Cards */}
          {dockerData.containers.containers.length > 0 && (
            <>
              <h3 className="subsection-title">Containers</h3>
              <div className="containers-grid">
                {dockerData.containers.containers.map((container) => (
                  <div key={container.id} className="container-card">
                    <div className="container-header">
                      <div className="container-name">{container.name}</div>
                      <div className={`status-badge ${container.status}`}>
                        {container.status}
                      </div>
                    </div>

                    <div className="container-image">{container.image}</div>

                    {container.stats && (
                      <div className="container-stats">
                        <div className="stat-row">
                          <span className="stat-label">CPU:</span>
                          <span className="stat-value">{container.stats.cpu_percent.toFixed(1)}%</span>
                        </div>
                        <div className="stat-row">
                          <span className="stat-label">Memory:</span>
                          <span className="stat-value">{container.stats.memory_percent.toFixed(1)}%</span>
                        </div>
                        <div className="stat-row">
                          <span className="stat-label">Network RX:</span>
                          <span className="stat-value">
                            {(container.stats.network_rx / 1024 / 1024).toFixed(1)} MB
                          </span>
                        </div>
                        <div className="stat-row">
                          <span className="stat-label">Network TX:</span>
                          <span className="stat-value">
                            {(container.stats.network_tx / 1024).toFixed(1)} KB
                          </span>
                        </div>
                      </div>
                    )}

                    {container.state.Running && (
                      <div className="container-uptime">
                        Started: {new Date(container.state.StartedAt).toLocaleString()}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </>
          )}

          {/* Images List */}
          {dockerData.images.images.length > 0 && (
            <>
              <h3 className="subsection-title">Images</h3>
              <div className="images-list">
                {dockerData.images.images.map((image) => (
                  <div key={image.id} className="image-item">
                    <div className="image-tags">
                      {image.tags.map((tag, idx) => (
                        <span key={idx} className="image-tag">{tag}</span>
                      ))}
                    </div>
                    <div className="image-info">
                      <span className="image-size">{(image.size / 1024 / 1024).toFixed(1)} MB</span>
                      <span className="image-date">
                        {new Date(image.created).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {servicesHealth && servicesHealth.services.length > 0 && (
        <div className="services-section">
          <h2 className="section-title">External Services</h2>
          <div className="services-grid">
            {servicesHealth.services.map((service, idx) => (
              <div key={idx} className="service-card">
                <div className="service-header">
                  <div className="service-name">{service.name}</div>
                  <div className={`health-badge ${service.status}`}>
                    {service.status === 'healthy' ? '✓' : service.status === 'unhealthy' ? '✗' : '?'}
                  </div>
                </div>

                <div className="service-url">{service.url}</div>

                <div className="service-stats">
                  <div className="stat-row">
                    <span className="stat-label">Status:</span>
                    <span className={`stat-value status-${service.status}`}>
                      {service.status}
                    </span>
                  </div>
                  {service.response_time_ms && (
                    <div className="stat-row">
                      <span className="stat-label">Response:</span>
                      <span className="stat-value">{service.response_time_ms}ms</span>
                    </div>
                  )}
                  {service.error && (
                    <div className="stat-row">
                      <span className="stat-label">Error:</span>
                      <span className="stat-value error">{service.error}</span>
                    </div>
                  )}
                  <div className="stat-row">
                    <span className="stat-label">Last Check:</span>
                    <span className="stat-value">
                      {new Date(service.last_check).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default App