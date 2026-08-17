export interface Bounds {
  left: number;
  top: number;
  right: number;
  bottom: number;
}

export interface Point {
  x: number;
  y: number;
}

export interface UIElement {
  id: string;
  text: string | null;
  content_description: string | null;
  resource_id: string | null;
  class_name: string | null;
  package_name: string | null;
  bounds: Bounds;
  center: Point;
  clickable: boolean;
  enabled: boolean;
  visible: boolean;
  focused: boolean;
  selected: boolean;
  checked: boolean;
  scrollable: boolean;
  long_clickable: boolean;
  checkable: boolean;
  password: boolean;
  parent_id: string | null;
  children: string[];
  depth: number;
  index: number;
  role: string | null;
  ocr_text: string | null;
  visual_confidence: number | null;
  source: string[];
}

export interface ElementTreeDTO {
  rotation: number;
  count: number;
  elements: UIElement[];
}

export interface InspectionSnapshot {
  package_name: string;
  activity: string;
  screen_width: number;
  screen_height: number;
  timestamp: number;
  screenshot_png_base64: string;
  hierarchy: ElementTreeDTO;
}

export interface WSSnapshotMessage extends InspectionSnapshot {
  type: "snapshot";
}

export interface WSErrorMessage {
  type: "error";
  message: string;
}

export type WSMessage = WSSnapshotMessage | WSErrorMessage;
