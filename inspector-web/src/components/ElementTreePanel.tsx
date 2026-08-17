import { useMemo, useState } from "react";
import type { ElementTreeDTO, UIElement } from "../types";

interface Props {
  tree: ElementTreeDTO | null;
  selectedId: string | null;
  hoveredId: string | null;
  onSelect: (id: string) => void;
  onHover: (id: string | null) => void;
}

function label(element: UIElement): string {
  const cls = element.class_name?.split(".").pop() ?? "Node";
  const bits = [cls];
  if (element.text) bits.push(`"${element.text}"`);
  else if (element.content_description) bits.push(`desc:"${element.content_description}"`);
  else if (element.resource_id) bits.push(`#${element.resource_id.split("/").pop()}`);
  return bits.join(" ");
}

export function ElementTreePanel({ tree, selectedId, hoveredId, onSelect, onHover }: Props) {
  const [query, setQuery] = useState("");

  const byId = useMemo(() => new Map((tree?.elements ?? []).map((e) => [e.id, e])), [tree]);
  const roots = useMemo(() => (tree?.elements ?? []).filter((e) => e.parent_id === null), [tree]);

  const matchesQuery = (e: UIElement): boolean => {
    if (!query.trim()) return true;
    const q = query.toLowerCase();
    return (
      (e.text ?? "").toLowerCase().includes(q) ||
      (e.resource_id ?? "").toLowerCase().includes(q) ||
      (e.class_name ?? "").toLowerCase().includes(q) ||
      (e.content_description ?? "").toLowerCase().includes(q)
    );
  };

  const anyDescendantMatches = (e: UIElement): boolean => {
    if (matchesQuery(e)) return true;
    return e.children.some((cid) => {
      const child = byId.get(cid);
      return child ? anyDescendantMatches(child) : false;
    });
  };

  function renderNode(element: UIElement): React.ReactNode {
    if (query.trim() && !anyDescendantMatches(element)) return null;
    const children = element.children.map((id) => byId.get(id)).filter((e): e is UIElement => !!e);
    const isSelected = element.id === selectedId;
    const isHovered = element.id === hoveredId;

    return (
      <div key={element.id} style={{ marginLeft: 12 }}>
        <div
          className={`tree-node${isSelected ? " tree-node-selected" : ""}${isHovered ? " tree-node-hovered" : ""}`}
          onClick={(evt) => {
            evt.stopPropagation();
            onSelect(element.id);
          }}
          onMouseEnter={() => onHover(element.id)}
          onMouseLeave={() => onHover(null)}
        >
          <span className={`role-badge role-${element.role ?? "container"}`}>{element.role ?? "?"}</span>
          <span className="tree-node-label">{label(element)}</span>
        </div>
        {children.map(renderNode)}
      </div>
    );
  }

  return (
    <div className="panel tree-panel">
      <div className="panel-header">Device Tree</div>
      <input
        className="search-input"
        placeholder="Search elements..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <div className="tree-scroll">
        {tree ? roots.map(renderNode) : <div className="empty-state">No hierarchy loaded</div>}
      </div>
    </div>
  );
}
