import { useState } from "react";
import { generateLocators } from "../locators";
import type { ElementTreeDTO, UIElement } from "../types";

interface Props {
  element: UIElement | null;
  tree: ElementTreeDTO | null;
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="detail-row">
      <span className="detail-label">{label}</span>
      <span className="detail-value">{value}</span>
    </div>
  );
}

export function ElementDetailsPanel({ element, tree }: Props) {
  const [copied, setCopied] = useState<string | null>(null);

  if (!element || !tree) {
    return (
      <div className="panel details-panel">
        <div className="panel-header">Element Details</div>
        <div className="empty-state">Select an element to inspect</div>
      </div>
    );
  }

  const locators = generateLocators(element, tree);
  const byId = new Map(tree.elements.map((e) => [e.id, e]));
  const parent = element.parent_id ? byId.get(element.parent_id) : null;
  const children = element.children.map((id) => byId.get(id)).filter((e): e is UIElement => !!e);
  const siblings = parent
    ? parent.children.map((id) => byId.get(id)).filter((e): e is UIElement => !!e && e.id !== element.id)
    : [];

  function copy(text: string, key: string) {
    navigator.clipboard?.writeText(text).catch(() => undefined);
    setCopied(key);
    setTimeout(() => setCopied(null), 1200);
  }

  return (
    <div className="panel details-panel">
      <div className="panel-header">Element Details</div>
      <div className="details-scroll">
        <section>
          <Row label="Text" value={element.text ?? "—"} />
          <Row label="Content Description" value={element.content_description ?? "—"} />
          <Row label="Resource ID" value={element.resource_id ?? "—"} />
          <Row label="Class" value={element.class_name ?? "—"} />
          <Row label="Package" value={element.package_name ?? "—"} />
          <Row
            label="Bounds"
            value={`[${element.bounds.left},${element.bounds.top}][${element.bounds.right},${element.bounds.bottom}]`}
          />
          <Row label="Center" value={`(${element.center.x}, ${element.center.y})`} />
          <Row label="Role" value={element.role ?? "—"} />
        </section>

        <section className="state-flags">
          {(["clickable", "enabled", "focused", "scrollable", "selected", "checked", "checkable"] as const).map(
            (flag) => (
              <span key={flag} className={`flag${element[flag] ? " flag-on" : ""}`}>
                {flag}
              </span>
            ),
          )}
        </section>

        <section>
          <div className="section-title">Relationships</div>
          <Row label="Parent" value={parent ? (parent.text || parent.class_name?.split(".").pop()) : "—"} />
          <Row label="Children" value={children.length} />
          <Row label="Siblings" value={siblings.length} />
        </section>

        <section>
          <div className="section-title">Generated Locators</div>
          <div className="locator-list">
            {locators.map((loc) => (
              <div key={loc.strategy} className={`locator-card${loc.recommendation === "best" ? " locator-best" : ""}`}>
                <div className="locator-card-header">
                  <span className="locator-strategy">{loc.strategy}</span>
                  <span className="locator-score">{Math.round(loc.score * 100)}%</span>
                </div>
                <code className="locator-code">{loc.pythonCode}</code>
                <button className="copy-btn" onClick={() => copy(loc.pythonCode, loc.strategy)}>
                  {copied === loc.strategy ? "Copied!" : "Copy Python"}
                </button>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
