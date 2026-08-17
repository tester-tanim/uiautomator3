import type { InspectionSnapshot } from "./types";

const API_BASE = "http://127.0.0.1:17920";
const WS_BASE = "ws://127.0.0.1:17920";

export async function fetchDevices(): Promise<{ serial: string }[]> {
  const res = await fetch(`${API_BASE}/api/devices`);
  if (!res.ok) throw new Error(`Failed to list devices: ${res.status}`);
  return res.json();
}

export async function fetchInspect(serial?: string): Promise<InspectionSnapshot> {
  const url = new URL(`${API_BASE}/api/inspect`);
  if (serial) url.searchParams.set("serial", serial);
  const res = await fetch(url);
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || `Inspect failed: ${res.status}`);
  }
  return res.json();
}

export async function postClick(x: number, y: number, serial?: string): Promise<void> {
  const url = new URL(`${API_BASE}/api/click`);
  url.searchParams.set("x", String(Math.round(x)));
  url.searchParams.set("y", String(Math.round(y)));
  if (serial) url.searchParams.set("serial", serial);
  const res = await fetch(url, { method: "POST" });
  if (!res.ok) throw new Error(`Click failed: ${res.status}`);
}

export function inspectWebSocketUrl(serial?: string): string {
  const url = new URL(`${WS_BASE}/ws/inspect`);
  if (serial) url.searchParams.set("serial", serial);
  return url.toString();
}
