import { useState, useEffect } from 'react'
import axios from 'axios'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

const API_URL = import.meta.env.PROD ? '' : 'http://localhost:8000'

function CPUChart() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [currentCPU, setCurrentCPU] = useState(null)

  useEffect(() => {
    const fetchCPUHistory = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/metrics/history/cpu?range=5`)

        // Transform the data for recharts
        const chartData = response.data.data.map(entry => ({
          time: new Date(entry.timestamp * 1000).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
          }),
          cpu: entry.data.percent,
          timestamp: entry.timestamp
        }))

        setData(chartData)

        // Set current CPU value (latest data point)
        if (chartData.length > 0) {
          setCurrentCPU(chartData[chartData.length - 1].cpu)
        }

        setLoading(false)
      } catch (err) {
        console.error('CPU history fetch error:', err)
        setError(err.message)
        setLoading(false)
      }
    }

    // Fetch immediately
    fetchCPUHistory()

    // Then fetch every 5 seconds
    const interval = setInterval(fetchCPUHistory, 5000)

    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="metric-card cpu-chart-card">
        <h2>CPU Usage</h2>
        <div className="metric-value">Loading...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="metric-card cpu-chart-card">
        <h2>CPU Usage</h2>
        <div className="metric-value">Error: {error}</div>
      </div>
    )
  }

  return (
    <div className="metric-card cpu-chart-card">
      <h2>CPU Usage</h2>
      {currentCPU !== null && (
        <div className="metric-value">{currentCPU.toFixed(1)}%</div>
      )}
      <div className="chart-container">
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis
              dataKey="time"
              tick={{ fill: '#aaa', fontSize: 10 }}
              interval="preserveStartEnd"
              minTickGap={50}
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fill: '#aaa', fontSize: 12 }}
              label={{ value: '%', angle: -90, position: 'insideLeft', fill: '#aaa' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1a1a1a',
                border: '1px solid #333',
                borderRadius: '4px'
              }}
              labelStyle={{ color: '#aaa' }}
              itemStyle={{ color: '#61dafb' }}
              formatter={(value) => [`${value.toFixed(1)}%`, 'CPU']}
            />
            <Line
              type="monotone"
              dataKey="cpu"
              stroke="#61dafb"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export default CPUChart
