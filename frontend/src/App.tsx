import { useEffect, useMemo, useState } from 'react'

type EventItem = {
  id: number
  event_type: string
  timestamp: string
  object_class?: string
  track_id?: number | null
  zone?: string | null
  confidence?: number
  severity?: string
  metadata?: Record<string, unknown>
  status?: string
  duration_seconds?: number | null
}

type Status = {
  status: string
  camera_status: string
  camera_error?: string | null
  fps: number | null
  inference_latency_ms: number | null
  frame_processing_time_ms: number | null
  object_count: number | null
  event_count: number
  ai_enabled: boolean
}

type MetricItem = {
  metric_name: string
  metric_value: number
  unit?: string
  timestamp?: string
}

const API_BASE = 'http://localhost:8000'

function App() {
  const [status, setStatus] = useState<Status | null>(null)
  const [events, setEvents] = useState<EventItem[]>([])
  const [zones, setZones] = useState<Array<{ id: string; name: string; type: string; polygon: number[][] }>>([])
  const [metrics, setMetrics] = useState<MetricItem[]>([])
  const [selectedEvent, setSelectedEvent] = useState<EventItem | null>(null)
  const [loading, setLoading] = useState(true)
  const [connectionError, setConnectionError] = useState<string | null>(null)
  const [eventFilter, setEventFilter] = useState('all')
  const [eventSummary, setEventSummary] = useState('')
  const [acknowledging, setAcknowledging] = useState(false)

  useEffect(() => {
    const load = async () => {
      try {
        const [statusRes, eventsRes, zonesRes, metricsRes] = await Promise.all([
          fetch(`${API_BASE}/api/system/status`),
          fetch(`${API_BASE}/api/events`),
          fetch(`${API_BASE}/api/zones`),
          fetch(`${API_BASE}/api/metrics`),
        ])

        const statusJson = statusRes.ok ? await statusRes.json() : null
        const eventsJson = eventsRes.ok ? await eventsRes.json() : []
        const zonesJson = zonesRes.ok ? await zonesRes.json() : []
        const metricsJson = metricsRes.ok ? await metricsRes.json() : []

        setStatus(statusJson)
        setEvents(eventsJson)
        setZones(zonesJson)
        setMetrics(metricsJson)
        setConnectionError(null)
        setSelectedEvent((current) => eventsJson.find((event: EventItem) => event.id === current?.id) ?? eventsJson[0] ?? null)
      } catch (error) {
        setConnectionError(error instanceof Error ? error.message : 'Unable to connect to the backend.')
      } finally {
        setLoading(false)
      }
    }

    void load()
    const timer = window.setInterval(() => void load(), 4000)
    return () => window.clearInterval(timer)
  }, [])

  const recentMetrics = useMemo(() => metrics.slice(0, 6), [metrics])
  const filteredEvents = useMemo(() => events.filter((event) => {
    if (eventFilter === 'all') return true
    if (eventFilter === 'unacknowledged') return event.status !== 'acknowledged'
    return event.severity === eventFilter
  }), [eventFilter, events])

  useEffect(() => {
    if (!selectedEvent) {
      setEventSummary('')
      return
    }
    let cancelled = false
    fetch(`${API_BASE}/api/events/${selectedEvent.id}/summary`)
      .then(async (response) => {
        if (!response.ok) throw new Error('Summary unavailable.')
        return response.json()
      })
      .then((payload) => { if (!cancelled) setEventSummary(payload.summary) })
      .catch(() => { if (!cancelled) setEventSummary('No summary available for this event.') })
    return () => { cancelled = true }
  }, [selectedEvent])

  const acknowledgeSelected = async () => {
    if (!selectedEvent) return
    setAcknowledging(true)
    try {
      const response = await fetch(`${API_BASE}/api/events/${selectedEvent.id}/acknowledge`, { method: 'POST' })
      if (!response.ok) throw new Error('Acknowledgement failed.')
      setEvents((current) => current.map((event) => event.id === selectedEvent.id ? { ...event, status: 'acknowledged' } : event))
      setSelectedEvent({ ...selectedEvent, status: 'acknowledged' })
    } catch (error) {
      setConnectionError(error instanceof Error ? error.message : 'Acknowledgement failed.')
    } finally {
      setAcknowledging(false)
    }
  }

  return (
    <div className="shell">
      <header className="topbar">
        <div>
          <div className="brand">VISIONOPS AI</div>
          <div className="status-dot-wrap">
            <span className={`status-dot ${status?.camera_status === 'online' ? 'live' : 'offline'}`} />
            {status?.camera_status === 'online' ? 'LIVE' : status?.camera_status?.toUpperCase() ?? 'CONNECTING'}
          </div>
        </div>
      </header>

      <main className="dashboard">
        <section className="video-panel card">
          <div className="panel-header">
            <h2>LIVE CAMERA</h2>
            <span className="chip">{status?.camera_status ?? 'unknown'}</span>
          </div>
            {status?.camera_status === 'online' ? (
              <img src={`${API_BASE}/api/video/stream`} alt="Live camera feed with detections and monitoring zones" className="camera-feed" />
            ) : (
              <div className="camera-unavailable" role="status">
                <strong>Camera feed unavailable</strong>
                <span>{status?.camera_error ?? 'Waiting for a local camera.'}</span>
              </div>
            )}
        </section>

          {connectionError && <div className="connection-error" role="alert">Backend connection issue: {connectionError}</div>}

        <aside className="sidebar">
          <div className="card small-card">
            <h3>System Status</h3>
            <ul>
              <li>Objects: {status?.camera_status === 'online' ? status.object_count ?? 'N/A' : 'N/A'}</li>
              <li>FPS: {status?.fps ?? 'N/A'}</li>
              <li>Inference latency: {status?.inference_latency_ms == null ? 'N/A' : `${status.inference_latency_ms.toFixed(1)} ms`}</li>
              <li>AI provider: {status?.ai_enabled ? 'configured' : 'local summaries'}</li>
            </ul>
          </div>
          <div className="card small-card">
            <h3>Zones</h3>
            {zones.length === 0 ? <p>No data available.</p> : zones.map((zone) => <p key={zone.id}>{zone.name}</p>)}
          </div>
        </aside>

        <section className="event-panel card">
          <div className="panel-header">
            <h2>Recent Events</h2>
            <label className="filter-label">
              <span>Filter</span>
              <select value={eventFilter} onChange={(event) => setEventFilter(event.target.value)}>
                <option value="all">All events</option>
                <option value="unacknowledged">Unacknowledged</option>
                <option value="high">High severity</option>
                <option value="medium">Medium severity</option>
                <option value="low">Low severity</option>
              </select>
            </label>
          </div>
          {loading ? <p>Loading…</p> : filteredEvents.length === 0 ? <p>No events match this filter.</p> : (
            <div className="event-list">
              {filteredEvents.map((event) => (
                <div key={event.id} className={`event-row ${selectedEvent?.id === event.id ? 'selected' : ''}`}>
                  <button className="event-item" onClick={() => setSelectedEvent(event)}>
                    <span className={`severity ${event.severity ?? 'medium'}`}>{event.event_type}</span>
                    <span>{event.object_class ?? 'Scene'}{event.track_id == null ? '' : ` #${event.track_id}`}</span>
                    <time>{new Date(event.timestamp).toLocaleTimeString()}</time>
                  </button>
                  <span className="event-state">{event.status ?? 'new'}</span>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="detail-panel card">
          <div className="panel-header">
            <h2>Event Details</h2>
            {selectedEvent && selectedEvent.status !== 'acknowledged' && (
              <button className="action-button" onClick={acknowledgeSelected} disabled={acknowledging}>
                {acknowledging ? 'Saving…' : 'Acknowledge'}
              </button>
            )}
          </div>
          {selectedEvent ? (
            <div className="detail-grid">
              <div><strong>Event type</strong><p>{selectedEvent.event_type}</p></div>
              <div><strong>Time</strong><p>{selectedEvent.timestamp}</p></div>
              <div><strong>Severity</strong><p>{selectedEvent.severity}</p></div>
              <div><strong>Object</strong><p>{selectedEvent.object_class ?? 'N/A'}</p></div>
              <div><strong>Track ID</strong><p>{selectedEvent.track_id ?? 'N/A'}</p></div>
              <div><strong>Confidence</strong><p>{selectedEvent.confidence ?? 'N/A'}</p></div>
              <div><strong>Zone</strong><p>{selectedEvent.zone ?? 'N/A'}</p></div>
              <div><strong>Duration</strong><p>{selectedEvent.duration_seconds ?? 'N/A'}</p></div>
              <div className="full"><strong>Evidence metadata</strong><p>{JSON.stringify(selectedEvent.metadata ?? {})}</p></div>
              <div className="full"><strong>Local event summary</strong><p>{eventSummary || 'Preparing summary…'}</p></div>
            </div>
          ) : <p>No data available.</p>}
        </section>

        <section className="metrics-panel card">
          <div className="panel-header">
            <h2>System Metrics</h2>
          </div>
          <div className="metrics-grid">
            {recentMetrics.length === 0 ? <p>No data available.</p> : recentMetrics.map((metric) => (
              <div className="metric-card" key={`${metric.metric_name}-${metric.timestamp}`}>
                <span>{metric.metric_name}</span>
                <strong>{metric.metric_value}</strong>
                <small>{metric.unit ?? 'value'}</small>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  )
}

export default App
