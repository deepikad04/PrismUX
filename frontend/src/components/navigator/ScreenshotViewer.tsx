import { useRef, useState } from "react";
import { Monitor } from "lucide-react";
import type { NavigationStep } from "../../types/navigation";
import OverlayCanvas from "./OverlayCanvas";
import type { FrictionMarker } from "./OverlayCanvas";

interface Props {
  step: NavigationStep | null;
  isPreClick: boolean;
}

export default function ScreenshotViewer({ step, isPreClick }: Props) {
  const [showAfter, setShowAfter] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  if (!step) {
    return (
      <div>
        {/* Browser chrome */}
        <div className="bg-surface-800 rounded-t-xl px-4 py-2 flex items-center gap-2">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-red-500/60" />
            <div className="w-3 h-3 rounded-full bg-yellow-500/60" />
            <div className="w-3 h-3 rounded-full bg-green-500/60" />
          </div>
          <div className="flex-1 bg-surface-700 rounded-md px-3 py-1 text-xs text-surface-500 font-mono ml-2">
            Waiting...
          </div>
        </div>
        <div className="aspect-video bg-surface-100 rounded-b-lg flex items-center justify-center text-surface-400">
          <div className="text-center">
            <Monitor className="w-10 h-10 mx-auto mb-2 text-surface-300" />
            <div className="text-sm">Waiting for navigation to start...</div>
          </div>
        </div>
      </div>
    );
  }

  const screenshotB64 = showAfter
    ? step.screenshot_after_b64
    : step.screenshot_before_b64;
  const screenshotUrl = showAfter
    ? step.screenshot_after_url
    : step.screenshot_before_url;
  // Prefer base64 (live session), fall back to GCS URL (persisted replay)
  const imgSrc = screenshotB64
    ? `data:image/png;base64,${screenshotB64}`
    : screenshotUrl || "";
  const candidates = step.plan.candidates || [];
  const elements = step.perception?.elements || [];

  // Build spatial friction markers at the click coordinates when friction was detected
  const frictionMarkers: FrictionMarker[] = [];
  if (showAfter && step.plan.coordinates && step.evaluation?.friction_items?.length) {
    const [fx, fy] = step.plan.coordinates;
    for (const fi of step.evaluation.friction_items) {
      frictionMarkers.push({
        x: fx,
        y: fy,
        category: fi.category,
        severity: fi.severity,
        description: fi.description,
        evidence: fi.evidence || undefined,
      });
    }
  }

  return (
    <div className="space-y-2">
      {/* Browser chrome */}
      <div className="bg-surface-800 rounded-t-xl px-4 py-2 flex items-center gap-2">
        <div className="flex gap-1.5">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <div className="w-3 h-3 rounded-full bg-yellow-500" />
          <div className="w-3 h-3 rounded-full bg-green-500" />
        </div>
        <div className="flex-1 bg-surface-700 rounded-md px-3 py-1 text-xs text-surface-400 font-mono truncate ml-2">
          {step.action_result.url_after || "Loading..."}
        </div>
        <div className="bg-surface-700 text-surface-400 text-xs px-2 py-0.5 rounded font-mono">
          Step {step.step_number}
        </div>
      </div>

      {/* Screenshot */}
      <div
        ref={containerRef}
        className="relative aspect-video bg-black rounded-b-lg overflow-hidden -mt-2"
      >
        {imgSrc ? (
          <img
            ref={imgRef}
            src={imgSrc}
            alt={`Step ${step.step_number} screenshot`}
            className="w-full h-full object-contain"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center text-surface-500">
            <div className="text-center">
              <Monitor className="w-8 h-8 mx-auto mb-1 text-surface-600" />
              <div className="text-xs">Screenshot not available</div>
              <div className="text-[10px] text-surface-600 mt-0.5">
                {step.plan.action_type} {step.plan.target_element || ""}
              </div>
            </div>
          </div>
        )}
        {!showAfter ? (
          <OverlayCanvas candidates={candidates} elements={elements} isPreClick={isPreClick} />
        ) : frictionMarkers.length > 0 ? (
          <OverlayCanvas candidates={[]} elements={[]} isPreClick={false} frictionMarkers={frictionMarkers} />
        ) : null}
      </div>

      {/* Before/After toggle */}
      <div className="flex gap-1 justify-center">
        <button
          onClick={() => setShowAfter(false)}
          className={`px-3 py-1 text-xs rounded-full transition-colors ${
            !showAfter
              ? "bg-primary-600 text-white"
              : "bg-surface-100 text-surface-600 hover:bg-surface-200"
          }`}
        >
          Before
        </button>
        <button
          onClick={() => setShowAfter(true)}
          className={`px-3 py-1 text-xs rounded-full transition-colors ${
            showAfter
              ? "bg-primary-600 text-white"
              : "bg-surface-100 text-surface-600 hover:bg-surface-200"
          }`}
        >
          After
        </button>
      </div>
    </div>
  );
}
