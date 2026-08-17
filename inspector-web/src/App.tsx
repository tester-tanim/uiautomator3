import { useEffect, useRef, useState } from "react";
import "./App.css";
import { fetchDevices, fetchInspect, inspectWebSocketUrl } from "./api";
import { ElementDetailsPanel } from "./components/ElementDetailsPanel";
import { ElementTreePanel } from "./components/ElementTreePanel";
import { LivePreview } from "./components/LivePreview";
import type { InspectionSnapshot, WSMessage } from "./types";

type ConnectionState = "connecting" | "connected" | "error" | "disconnected";

function App() {
  const [devices, setDevices] = useState<{ serial: string }[]>([]);
  const [serial, setSerial] = useState<string | undefined>(undefined);
  const [snapshot, setSnapshot] = useState<InspectionSnapshot | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [status, setStatus] = useState<ConnectionState>("connecting");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [live, setLive] = useState(true);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    fetchDevices()
      .then(setDevices)
      .catch(() => setDevices([]));
  }, []);

  useEffect(() => {
    if (!live) return;

    setStatus("connecting");
    const ws = new WebSocket(inspectWebSocketUrl(serial));
    wsRef.current = ws;

    ws.onopen = () => setStatus("connected");
    ws.onclose = () => setStatus("disconnected");
    ws.onerror = () => setStatus("error");
    ws.onmessage = (evt) => {
      const message: WSMessage = JSON.parse(evt.data);
      if (message.type === "snapshot") {
        setSnapshot(message);
        setErrorMessage(null);
      } else {
        setErrorMessage(message.message);
      }
    };

    return () => ws.close();
  }, [serial, live]);

  async function refreshOnce() {
    setStatus("connecting");
    try {
      const result = await fetchInspect(serial);
      setSnapshot(result);
      setErrorMessage(null);
      setStatus("connected");
    } catch (e) {
      setErrorMessage(e instanceof Error ? e.message : String(e));
      setStatus("error");
    }
  }

  const tree = snapshot?.hierarchy ?? null;
  const selectedElement = selectedId ? (tree?.elements.find((e) => e.id === selectedId) ?? null) : null;

  return (
    <div className="app">
      <header className="app-header">
        <h1>UIAutomator 3.0</h1>
        <div className="header-controls">
          <select value={serial ?? ""} onChange={(e) => setSerial(e.target.value || undefined)}>
            <option value="">Default device</option>
            {devices.map((d) => (
              <option key={d.serial} value={d.serial}>
                {d.serial}
              </option>
            ))}
          </select>
          <span className={`status-dot status-${status}`} />
          <span className="status-label">{status}</span>
          <label className="live-toggle">
            <input type="checkbox" checked={live} onChange={(e) => setLive(e.target.checked)} />
            Live
          </label>
          {!live && (
            <button className="refresh-btn" onClick={refreshOnce}>
              Refresh
            </button>
          )}
          {snapshot && (
            <span className="app-info">
              {snapshot.package_name} / {snapshot.activity}
            </span>
          )}
        </div>
      </header>

      {errorMessage && <div className="error-banner">{errorMessage}</div>}

      <main className="app-body">
        <ElementTreePanel
          tree={tree}
          selectedId={selectedId}
          hoveredId={hoveredId}
          onSelect={setSelectedId}
          onHover={setHoveredId}
        />
        <LivePreview
          screenshotBase64={snapshot?.screenshot_png_base64 ?? null}
          screenWidth={snapshot?.screen_width ?? 0}
          screenHeight={snapshot?.screen_height ?? 0}
          tree={tree}
          selectedId={selectedId}
          hoveredId={hoveredId}
          onSelect={setSelectedId}
          onHover={setHoveredId}
        />
        <ElementDetailsPanel element={selectedElement} tree={tree} />
      </main>
    </div>
  );
}

export default App;
