import type { ElementTreeDTO, UIElement } from "./types";

export interface LocatorCandidate {
  strategy: string;
  locator: string;
  pythonCode: string;
  score: number;
  uniqueness: number;
  recommendation: "best" | "alternative";
}

function countMatches(tree: ElementTreeDTO, predicate: (e: UIElement) => boolean): number {
  let count = 0;
  for (const e of tree.elements) {
    if (predicate(e)) count += 1;
  }
  return count;
}

function uniquenessScore(matches: number): number {
  if (matches <= 0) return 0;
  return 1 / matches;
}

function escapePy(value: string): string {
  return value.replace(/\\/g, "\\\\").replace(/'/g, "\\'");
}

/**
 * Generate candidate locators for one element, scored by uniqueness within
 * the current tree snapshot. Deterministic, rule-based (Phase 5 will move
 * this logic server-side into uiautomator3.locator with a fuller stability
 * model); this client-side version is enough for Phase 4's inspector panel.
 */
export function generateLocators(element: UIElement, tree: ElementTreeDTO): LocatorCandidate[] {
  const candidates: LocatorCandidate[] = [];

  if (element.resource_id) {
    const matches = countMatches(tree, (e) => e.resource_id === element.resource_id);
    candidates.push({
      strategy: "resource_id",
      locator: element.resource_id,
      pythonCode: `d(resourceId='${escapePy(element.resource_id)}')`,
      uniqueness: uniquenessScore(matches),
      score: 0.99 * uniquenessScore(matches),
      recommendation: "alternative",
    });
  }

  if (element.content_description) {
    const matches = countMatches(tree, (e) => e.content_description === element.content_description);
    candidates.push({
      strategy: "content_description",
      locator: element.content_description,
      pythonCode: `d(description='${escapePy(element.content_description)}')`,
      uniqueness: uniquenessScore(matches),
      score: 0.96 * uniquenessScore(matches),
      recommendation: "alternative",
    });
  }

  if (element.text) {
    const matches = countMatches(tree, (e) => e.text === element.text);
    candidates.push({
      strategy: "text",
      locator: element.text,
      pythonCode: `d(text='${escapePy(element.text)}')`,
      uniqueness: uniquenessScore(matches),
      score: 0.97 * uniquenessScore(matches),
      recommendation: "alternative",
    });
  }

  if (element.class_name) {
    const matches = countMatches(tree, (e) => e.class_name === element.class_name);
    candidates.push({
      strategy: "class_name",
      locator: element.class_name,
      pythonCode: `d(className='${escapePy(element.class_name)}')`,
      uniqueness: uniquenessScore(matches),
      score: 0.6 * uniquenessScore(matches),
      recommendation: "alternative",
    });

    if (element.text) {
      const comboMatches = countMatches(
        tree,
        (e) => e.class_name === element.class_name && e.text === element.text,
      );
      candidates.push({
        strategy: "class_and_text",
        locator: `${element.class_name}[text='${element.text}']`,
        pythonCode: `d(className='${escapePy(element.class_name)}', text='${escapePy(element.text)}')`,
        uniqueness: uniquenessScore(comboMatches),
        score: 0.85 * uniquenessScore(comboMatches),
        recommendation: "alternative",
      });
    }
  }

  const xpath = buildXPath(element, tree);
  candidates.push({
    strategy: "xpath",
    locator: xpath,
    pythonCode: `d.xpath('${escapePy(xpath)}')`,
    uniqueness: 1,
    score: 0.75,
    recommendation: "alternative",
  });

  candidates.push({
    strategy: "coordinate",
    locator: `(${element.center.x}, ${element.center.y})`,
    pythonCode: `d.click(${element.center.x}, ${element.center.y})`,
    uniqueness: 1,
    score: 0.45,
    recommendation: "alternative",
  });

  candidates.sort((a, b) => b.score - a.score);
  if (candidates.length > 0) {
    candidates[0] = { ...candidates[0], recommendation: "best" };
  }
  return candidates;
}

function simpleClassName(className: string | null): string {
  if (!className) return "*";
  return className;
}

function buildXPath(element: UIElement, tree: ElementTreeDTO): string {
  const byId = new Map(tree.elements.map((e) => [e.id, e]));
  const segments: string[] = [];
  let current: UIElement | undefined = element;

  while (current) {
    const cls = simpleClassName(current.class_name);
    const parent: UIElement | undefined = current.parent_id ? byId.get(current.parent_id) : undefined;
    if (parent) {
      const siblingsOfSameClass = parent.children
        .map((id) => byId.get(id))
        .filter((e): e is UIElement => !!e && e.class_name === current!.class_name);
      if (siblingsOfSameClass.length > 1) {
        const position = siblingsOfSameClass.findIndex((e) => e.id === current!.id) + 1;
        segments.unshift(`${cls}[${position}]`);
      } else {
        segments.unshift(cls);
      }
    } else {
      segments.unshift(cls);
    }
    current = parent;
  }

  return "//" + segments.join("/");
}
