"use client"

import "./PlantDetails.css"
import { useState, useEffect } from "react"
import axios from "axios"

// API Gateway endpoint - will be set automatically during deployment
const API_ENDPOINT =
  process.env.REACT_APP_API_ENDPOINT || "https://your-api-id.execute-api.us-east-1.amazonaws.com/dev/plant"

const PlantDetails = ({ plantId = "Plant-001" }) => {
  const [plantData, setPlantData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)

  useEffect(() => {
    fetchPlantData()
    // Refresh data every 30 seconds
    const interval = setInterval(fetchPlantData, 30000)
    return () => clearInterval(interval)
  }, [plantId])

  /**
   * Fetch plant data from API Gateway
   * Currently returns: AI evaluation + image URL
   */
  const fetchPlantData = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await axios.get(`${API_ENDPOINT}/${plantId}`, {
        timeout: 10000,
        headers: {
          "Content-Type": "application/json",
        },
      })

      setPlantData(response.data)
      setLastUpdated(new Date())
      setLoading(false)
    } catch (err) {
      console.error("Error fetching plant data:", err)
      setError(err.response?.data?.error || "Failed to fetch plant data")
      setLoading(false)
    }
  }

  if (loading && !plantData) {
    return (
      <div className="plant-details loading">
        <div className="spinner"></div>
        <p>Loading plant data...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="plant-details error">
        <h3>Error</h3>
        <p>{error}</p>
        <button onClick={fetchPlantData}>Retry</button>
      </div>
    )
  }

  if (!plantData) {
    return null
  }

  const { metrics, image_url, timestamp } = plantData

  return (
    <div className="plant-details">
      <div className="plant-header">
        <h2>Plant Monitor - {plantId}</h2>
        <div className="last-updated">Last updated: {lastUpdated?.toLocaleTimeString()}</div>
        <button onClick={fetchPlantData} disabled={loading}>
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      <div className="plant-content">
        {/* Plant Image from S3 via Pre-signed URL */}
        <div className="plant-image-section">
          <h3>Current Image</h3>
          {image_url ? (
            <img
              src={image_url || "/placeholder.svg"}
              alt={`Plant ${plantId}`}
              className="plant-image"
              onError={(e) => {
                e.target.src = "/placeholder-plant.png"
                e.target.alt = "Image not available"
              }}
            />
          ) : (
            <div className="no-image">
              <p>No image available</p>
            </div>
          )}
          <p className="image-timestamp">Captured: {new Date(timestamp).toLocaleString()}</p>
        </div>

        {/* AI Health Assessment from S3 */}
        <div className="plant-metrics-section">
          <h3>AI Health Assessment</h3>

          <div className="ai-evaluation-main">
            <div className={`health-status status-${getHealthStatusClass(metrics?.ai_evaluation)}`}>
              <div className="status-icon">{getHealthIcon(metrics?.ai_evaluation)}</div>
              <div className="status-text">
                <h2>{metrics?.ai_evaluation || "Unknown"}</h2>
                <p className="status-subtitle">Based on latest image analysis</p>
              </div>
            </div>
          </div>

          {/* Sensor Data Section */}
          <div className="sensors-info">
            <h4>📊 Sensor Readings</h4>
            {metrics?.soil_moisture !== undefined || metrics?.rain !== undefined || metrics?.light !== undefined ? (
              <div className="sensor-grid">
                <div className="sensor-card">
                  <div className="sensor-icon">💧</div>
                  <div className="sensor-data">
                    <span className="sensor-label">Soil Moisture:  </span>
                    <span className="sensor-value">
                      {metrics?.soil_moisture !== undefined ? `${metrics.soil_moisture}%` : "N/A"}
                    </span>
                  </div>
                </div>

                <div className="sensor-card">
                  <div className="sensor-icon">🌧️</div>
                  <div className="sensor-data">
                    <span className="sensor-label">Rain Sensor:  </span>
                    <span className="sensor-value">
                      {metrics?.rain !== undefined ? (metrics.rain ? "Raining" : "Dry") : "N/A"}
                    </span>
                  </div>
                </div>

                <div className="sensor-card">
                  <div className="sensor-icon">☀️</div>
                  <div className="sensor-data">
                    <span className="sensor-label">Light Level:  </span>
                    <span className="sensor-value">
                      {metrics?.light !== undefined ? `${metrics.light} lux` : "N/A"}
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="sensor-placeholder">
                <p className="info-text">Sensor data will appear here once your IoT device starts sending readings.</p>
                <p className="info-text">Expected metrics: Soil Moisture, Rain Sensor, Light Level</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// Health Status Icon
const getHealthIcon = (evaluation) => {
  if (!evaluation) return "❓"
  const evalLower = evaluation.toLowerCase()
  if (evalLower.includes("healthy") && !evalLower.includes("unhealthy")) {
    return "✅"
  } else if (evalLower.includes("unhealthy")) {
    return "⚠️"
  }
  return "❓"
}

// Health Status Class
const getHealthStatusClass = (evaluation) => {
  if (!evaluation) return "unknown"
  const evalLower = evaluation.toLowerCase()
  if (evalLower.includes("healthy") && !evalLower.includes("unhealthy")) {
    return "healthy"
  } else if (evalLower.includes("unhealthy")) {
    return "unhealthy"
  }
  return "unknown"
}

export default PlantDetails
