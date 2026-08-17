import { useRef, useState } from "react";
import type { ElementTreeDTO, UIElement } from "../types";

interface Props {
  screenshotBase64: string | null;
  screenWidth: number;
  screenHeight: number;
  tree: ElementTreeDTO | null;
  selectedId: string | null;
  hoveredId: string | null;
  onSelect: (id: string) => void;
  onHover: (id: string | null) => void;
}

function pickDeepestAt(elements: UIElement[], x: number, y: number): UIElement | null {
  let best: UIElement | null = null;
  for (const e of elements) {
    const { left, top, right, bottom } = e.bounds;
    if (x >= left && x < right && y >= top && y < bottom) {
      if (!best || e.depth > best.depth) best = e;
    }
  }
  return best;
}

export function LivePreview({
  screenshotBase64,
  screenWidth,
  screenHeight,
  tree,
  selectedId,
  hoveredId,
  onSelect,
  onHover,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [touchPoint, setTouchPoint] = useState<{ x: number; y: number } | null>(null);

  const elements = tree?.elements ?? [];
  const byId = new Map(elements.map((e) => [e.id, e]));
  const selected = selectedId ? byId.get(selectedId) : null;
  const hovered = hoveredId ? byId.get(hoveredId) : null;

  function toDeviceCoords(evt: React.MouseEvent): { x: number; y: number } | null {
    const el = containerRef.current;
    if (!el || screenWidth === 0) return null;
    const rect = el.getBoundingClientRect();
    const scaleX = screenWidth / rect.width;
    const scaleY = screenHeight / rect.height;
    return {
      x: (evt.clientX - rect.left) * scaleX,
      y: (evt.clientY - rect.top) * scaleY,
    };
  }

  function handleMouseMove(evt: React.MouseEvent) {
    const point = toDeviceCoords(evt);
    if (!point) return;
    setTouchPoint(point);
    const hit = pickDeepestAt(elements, point.x, point.y);
    onHover(hit?.id ?? null);
  }

  function handleClick(evt: React.MouseEvent) {
    const point = toDeviceCoords(evt);
    if (!point) return;
    const hit = pickDeepestAt(elements, point.x, point.y);
    if (hit) onSelect(hit.id);
  }

  const aspectRatio = screenWidth && screenHeight ? screenWidth / screenHeight : 9 / 19.5;

  function overlayStyle(e: UIElement): React.CSSProperties {
    return {
      left: `${(e.bounds.left / screenWidth) * 100}%`,
      top: `${(e.bounds.top / screenHeight) * 100}%`,
      width: `${((e.bounds.right - e.bounds.left) / screenWidth) * 100}%`,
      height: `${((e.bounds.bottom - e.bounds.top) / screenHeight) * 100}%`,
    };
  }

  return (
    <div className="panel preview-panel">
      <div className="panel-header">
        Live Device Preview
        {touchPoint && (
          <span className="touch-coords">
            x: {Math.round(touchPoint.x)} y: {Math.round(touchPoint.y)}
          </span>
        )}
      </div>
      <div
        className="preview-frame"
        style={{ aspectRatio }}
        ref={containerRef}
        onMouseMove={handleMouseMove}
        onMouseLeave={() => onHover(null)}
        onClick={handleClick}
      >
        {screenshotBase64 ? (
          <img className="preview-image" src={`data:image/png;base64,${screenshotBase64}`} alt="Device screen" />
        ) : (
          <div className="empty-state">No screenshot yet</div>
        )}
        {hovered && hovered.id !== selectedId && (
          <div className="overlay-box overlay-hover" style={overlayStyle(hovered)} />
        )}
        {selected && <div className="overlay-box overlay-selected" style={overlayStyle(selected)} />}
      </div>
    </div>
  );
}
