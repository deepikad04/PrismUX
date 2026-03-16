import { useState, useEffect, useRef, useCallback } from "react";
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Rewind,
  FastForward,
} from "lucide-react";
import type { NavigationStep, CategorizedFriction } from "../../types/navigation";
import OverlayCanvas from "./OverlayCanvas";

interface Props {
  steps: NavigationStep[];
}

const SPEEDS = [0.5, 1, 1.5, 2];

export default function SessionReplay({ steps }: Props) {
  const [currentIdx, setCurrentIdx] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [showAfter, setShowAfter] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const step = steps[currentIdx] || null;
  const total = steps.length;

  const advance = useCallback(() => {
    setCurrentIdx((prev) => {
      if (prev >= total - 1) {
        setPlaying(false);
        return prev;
      }
      // Show before screenshot first, then after
      if (!showAfter) {
        setShowAfter(true);
        return prev;
      }
      setShowAfter(false);
      return prev + 1;
    });
  }, [total, showAfter]);

  useEffect(() => {
    if (playing && total > 0) {
      const delay = showAfter ? 1200 / speed : 2400 / speed;
      timerRef.current = setTimeout(advance, delay);
    }
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [playing, currentIdx, showAfter, speed, advance, total]);

  if (!step) return null;

  const screenshot = showAfter
    ? step.screenshot_after_b64
    : step.screenshot_before_b64;
  const frictionItems: CategorizedFriction[] =
    step.evaluation?.friction_items || [];
  const progress = ((currentIdx + (showAfter ? 0.5 : 0)) / Math.max(total, 1)) * 100;

  return (
    <div className="space-y-3">
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
          Step {step.step_number + 1}/{total}
        </div>
      </div>

      {/* Screenshot with overlay */}
      <div className="relative aspect-video bg-black rounded-b-lg overflow-hidden -mt-3">
        {screenshot && (
          <img
            src={`data:image/png;base64,${screenshot}`}
            alt={`Step ${step.step_number}`}
            className="w-full h-full object-contain transition-opacity duration-300"
          />
        )}
        {!showAfter && (
          <OverlayCanvas
            candidates={step.plan.candidates || []}
            elements={step.perception?.elements || []}
            isPreClick={!showAfter}
          />
        )}
        {/* Friction markers overlay */}
        {frictionItems.length > 0 && showAfter && (
          <div className="absolute top-3 right-3 space-y-1">
            {frictionItems.slice(0, 3).map((f, i) => (
              <div
                key={i}
                className="bg-red-500/90 text-white text-[10px] px-2 py-0.5 rounded-full backdrop-blur-sm animate-fade-in"
                style={{ animationDelay: `${i * 150}ms` }}
              >
                {f.category}: {f.description.slice(0, 50)}
              </div>
            ))}
          </div>
        )}
        {/* Phase label */}
        <div className="absolute bottom-3 left-3">
          <span
            className={`text-xs font-mono font-semibold px-2 py-1 rounded backdrop-blur-sm ${
              showAfter
                ? "bg-green-500/80 text-white"
                : "bg-blue-500/80 text-white"
            }`}
          >
            {showAfter ? "AFTER" : "BEFORE"}
          </span>
        </div>
      </div>

      {/* Progress bar */}
      <div
        className="h-1.5 bg-surface-200 rounded-full overflow-hidden cursor-pointer"
        onClick={(e) => {
          const rect = e.currentTarget.getBoundingClientRect();
          const pct = (e.clientX - rect.left) / rect.width;
          const idx = Math.min(Math.floor(pct * total), total - 1);
          setCurrentIdx(idx);
          setShowAfter(false);
        }}
      >
        <div
          className="h-full bg-gradient-to-r from-primary-500 to-primary-400 rounded-full transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Controls */}
      <div className="flex items-center justify-center gap-3">
        <button
          onClick={() => {
            setCurrentIdx(0);
            setShowAfter(false);
          }}
          className="p-1.5 rounded-lg hover:bg-surface-100 text-surface-500 transition-colors"
          title="Start"
        >
          <Rewind className="w-4 h-4" />
        </button>
        <button
          onClick={() => {
            setCurrentIdx((p) => Math.max(0, p - 1));
            setShowAfter(false);
          }}
          className="p-1.5 rounded-lg hover:bg-surface-100 text-surface-500 transition-colors"
          title="Previous"
        >
          <SkipBack className="w-4 h-4" />
        </button>
        <button
          onClick={() => setPlaying((p) => !p)}
          className="p-2.5 rounded-full bg-primary-600 text-white hover:bg-primary-700 transition-colors shadow-md"
        >
          {playing ? (
            <Pause className="w-5 h-5" />
          ) : (
            <Play className="w-5 h-5 ml-0.5" />
          )}
        </button>
        <button
          onClick={() => {
            setCurrentIdx((p) => Math.min(total - 1, p + 1));
            setShowAfter(false);
          }}
          className="p-1.5 rounded-lg hover:bg-surface-100 text-surface-500 transition-colors"
          title="Next"
        >
          <SkipForward className="w-4 h-4" />
        </button>
        <button
          onClick={() => {
            setCurrentIdx(total - 1);
            setShowAfter(true);
          }}
          className="p-1.5 rounded-lg hover:bg-surface-100 text-surface-500 transition-colors"
          title="End"
        >
          <FastForward className="w-4 h-4" />
        </button>
        {/* Speed selector */}
        <div className="ml-2 flex items-center gap-1">
          {SPEEDS.map((s) => (
            <button
              key={s}
              onClick={() => setSpeed(s)}
              className={`text-xs px-1.5 py-0.5 rounded ${
                speed === s
                  ? "bg-primary-100 text-primary-700 font-semibold"
                  : "text-surface-400 hover:text-surface-600"
              }`}
            >
              {s}x
            </button>
          ))}
        </div>
      </div>

      {/* Reasoning narration */}
      {step && (
        <div className="bg-surface-50 rounded-lg border border-surface-200 p-3 animate-fade-in">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono font-semibold text-primary-600 uppercase">
              {step.plan.action_type}
            </span>
            {step.plan.target_element && (
              <span className="text-xs text-surface-500">
                → {step.plan.target_element}
              </span>
            )}
            <span className="ml-auto text-xs font-mono text-surface-400">
              {step.plan.confidence.toFixed(2)}
            </span>
          </div>
          <p className="text-sm text-surface-700">{step.plan.reasoning}</p>
          {step.evaluation?.description && showAfter && (
            <p className="text-xs text-surface-500 mt-1 italic">
              {step.evaluation.description}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
