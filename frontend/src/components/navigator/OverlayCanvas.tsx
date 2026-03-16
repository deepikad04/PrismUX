import type { CandidateElement, DetectedElement } from "../../types/navigation";

const CHOSEN_COLOR = "#4c6ef5";
const ALT_COLOR = "#f59f00";

const ELEMENT_TYPE_COLORS: Record<string, string> = {
  button: "#2563eb",
  link: "#7c3aed",
  input: "#059669",
  form: "#059669",
  heading: "#dc2626",
  navigation: "#0891b2",
  modal: "#dc2626",
  image: "#d97706",
  text: "#6b7280",
  dropdown: "#2563eb",
};

export interface FrictionMarker {
  x: number;
  y: number;
  category: string;
  severity: string;
  description: string;
  evidence?: string;
}

const SEVERITY_MARKER_COLORS: Record<string, string> = {
  critical: "#dc2626",
  high: "#ef4444",
  medium: "#f59e0b",
  low: "#3b82f6",
};

interface Props {
  candidates: CandidateElement[];
  elements?: DetectedElement[];
  isPreClick: boolean;
  frictionMarkers?: FrictionMarker[];
}

/**
 * SVG overlay that draws bounding boxes on the screenshot.
 * Uses a fixed 960x540 viewBox matching the backend screenshot dimensions.
 * preserveAspectRatio="xMidYMid meet" ensures correct scaling at any container size.
 */
export default function OverlayCanvas({ candidates, elements = [], isPreClick, frictionMarkers = [] }: Props) {
  if (!candidates.length && !elements.length && !frictionMarkers.length) return null;

  return (
    <svg
      className="absolute inset-0 w-full h-full pointer-events-none"
      viewBox="0 0 960 540"
      preserveAspectRatio="xMidYMid meet"
    >
      {/* Element count badge */}
      {elements.length > 0 && (
        <g>
          <rect x="10" y="10" width="150" height="26" rx="13" fill="rgba(0,0,0,0.7)" />
          <text x="75" y="27" textAnchor="middle" fontSize="12" fill="white" fontWeight="600" fontFamily="system-ui">
            {elements.length} elements detected
          </text>
          <circle cx="145" cy="23" r="4" fill="#22c55e">
            <animate attributeName="opacity" values="1;0.3;1" dur="2s" repeatCount="indefinite" />
          </circle>
        </g>
      )}
      {/* Alternate candidates: faded dashed */}
      {candidates
        .filter((c) => !c.is_chosen)
        .map((c, i) => (
          <g key={`alt-${i}`}>
            <rect
              x={c.bbox.x}
              y={c.bbox.y}
              width={c.bbox.width}
              height={c.bbox.height}
              fill="none"
              stroke={ALT_COLOR}
              strokeWidth={2}
              strokeDasharray="6 4"
              opacity={0.5}
            />
            <text
              x={c.bbox.x + c.bbox.width}
              y={Math.max(c.bbox.y - 4, 12)}
              fontSize={11}
              fill={ALT_COLOR}
              textAnchor="end"
              opacity={0.7}
              fontFamily="monospace"
            >
              {c.confidence.toFixed(2)}
            </text>
          </g>
        ))}

      {/* Chosen element: solid with pulse */}
      {candidates
        .filter((c) => c.is_chosen)
        .map((c, i) => {
          const badgeY = Math.max(c.bbox.y - 22, 2);
          return (
            <g key={`chosen-${i}`}>
              {/* Pulse ring for pre-click */}
              {isPreClick && (
                <rect
                  x={c.bbox.x - 4}
                  y={c.bbox.y - 4}
                  width={c.bbox.width + 8}
                  height={c.bbox.height + 8}
                  fill="none"
                  stroke={CHOSEN_COLOR}
                  strokeWidth={3}
                  rx={4}
                  className="animate-pulse-ring"
                />
              )}
              {/* Main bbox */}
              <rect
                x={c.bbox.x}
                y={c.bbox.y}
                width={c.bbox.width}
                height={c.bbox.height}
                fill={`${CHOSEN_COLOR}15`}
                stroke={CHOSEN_COLOR}
                strokeWidth={2.5}
                rx={3}
              />
              {/* Confidence badge */}
              <rect
                x={c.bbox.x}
                y={badgeY}
                width={42}
                height={18}
                rx={4}
                fill={CHOSEN_COLOR}
              />
              <text
                x={c.bbox.x + 21}
                y={badgeY + 13}
                fontSize={11}
                fill="white"
                textAnchor="middle"
                fontWeight="600"
                fontFamily="monospace"
              >
                {c.confidence.toFixed(2)}
              </text>
              {/* Label */}
              <text
                x={c.bbox.x + 48}
                y={badgeY + 12}
                fontSize={11}
                fill={CHOSEN_COLOR}
                fontWeight="500"
                fontFamily="sans-serif"
              >
                {c.label}
              </text>
            </g>
          );
        })}
      {/* Element type labels on detected elements (faint, only show top 8) */}
      {elements.slice(0, 8).map((el, i) => {
        const color = ELEMENT_TYPE_COLORS[el.element_type] || "#6b7280";
        return (
          <g key={`el-${i}`} opacity={0.5}>
            <rect
              x={el.bbox.x}
              y={el.bbox.y}
              width={el.bbox.width}
              height={el.bbox.height}
              fill="none"
              stroke={color}
              strokeWidth={1}
              strokeDasharray="3 2"
            />
            <rect
              x={el.bbox.x}
              y={el.bbox.y - 14}
              width={el.element_type.length * 6.5 + 8}
              height={14}
              rx={3}
              fill={color}
              opacity={0.8}
            />
            <text
              x={el.bbox.x + 4}
              y={el.bbox.y - 3}
              fontSize={9}
              fill="white"
              fontFamily="monospace"
              fontWeight="500"
            >
              {el.element_type}
            </text>
          </g>
        );
      })}
      {/* Spatial friction markers — pulsing circles at click coordinates */}
      {frictionMarkers.map((fm, i) => {
        const color = SEVERITY_MARKER_COLORS[fm.severity] || "#ef4444";
        const descText = fm.description.length > 40 ? fm.description.slice(0, 37) + "..." : fm.description;
        const hasEvidence = !!fm.evidence;
        const evidenceText = fm.evidence && fm.evidence.length > 35 ? fm.evidence.slice(0, 32) + "..." : fm.evidence;
        const labelWidth = Math.min(fm.category.length * 7 + descText.length * 5.5 + 16, 300);
        const tooltipHeight = hasEvidence ? 34 : 20;
        return (
          <g key={`friction-${i}`}>
            {/* Outer pulse ring */}
            <circle cx={fm.x} cy={fm.y} r="28" fill="none" stroke={color} strokeWidth="2" opacity="0.4">
              <animate attributeName="r" values="20;35;20" dur="2s" repeatCount="indefinite" />
              <animate attributeName="opacity" values="0.5;0.1;0.5" dur="2s" repeatCount="indefinite" />
            </circle>
            {/* Inner glow */}
            <circle cx={fm.x} cy={fm.y} r="14" fill={color} opacity="0.25" />
            {/* Center dot */}
            <circle cx={fm.x} cy={fm.y} r="6" fill={color} opacity="0.9" />
            {/* Exclamation icon */}
            <text x={fm.x} y={fm.y + 4} textAnchor="middle" fontSize="9" fill="white" fontWeight="bold">!</text>
            {/* Label tooltip */}
            <rect
              x={fm.x + 16}
              y={fm.y - 10}
              width={labelWidth}
              height={tooltipHeight}
              rx="4"
              fill="rgba(0,0,0,0.85)"
            />
            <text
              x={fm.x + 22}
              y={fm.y + 4}
              fontSize="9"
              fill={color}
              fontWeight="700"
              fontFamily="monospace"
            >
              {fm.category.toUpperCase()}
            </text>
            <text
              x={fm.x + 22 + fm.category.length * 7 + 6}
              y={fm.y + 4}
              fontSize="9"
              fill="white"
              fontFamily="system-ui"
            >
              {descText}
            </text>
            {/* Evidence line — measured data backing the finding */}
            {hasEvidence && (
              <text
                x={fm.x + 22}
                y={fm.y + 18}
                fontSize="8"
                fill="#93c5fd"
                fontFamily="monospace"
                fontWeight="500"
              >
                {evidenceText}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}
