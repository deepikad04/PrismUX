import { useCallback, useEffect, useRef, useState } from "react";
import { Camera, Download, Loader2, ChevronLeft, ChevronRight } from "lucide-react";
import type { FrictionItem } from "../../types/navigation";

interface StepData {
  step_number: number;
  screenshot_after_b64?: string;
  screenshot_after_url?: string;
}

interface Props {
  sessionId: string;
  frictionItems: FrictionItem[];
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: "#dc2626",
  high: "#f97316",
  medium: "#f59e0b",
  low: "#3b82f6",
};

export default function AnnotatedScreenshots({ sessionId, frictionItems }: Props) {
  const [steps, setSteps] = useState<StepData[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentIdx, setCurrentIdx] = useState(0);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Fetch step screenshots
  useEffect(() => {
    fetch(`/api/navigate/${sessionId}/steps`)
      .then((r) => r.ok ? r.json() : [])
      .then((data: StepData[]) => {
        // Only keep steps that have friction
        const frictionStepNums = new Set(frictionItems.map((f) => f.evidence_step));
        const relevant = data.filter((s) => frictionStepNums.has(s.step_number));
        setSteps(relevant.length > 0 ? relevant : data.slice(0, 3));
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [sessionId, frictionItems]);

  const currentStep = steps[currentIdx];

  // Draw annotated screenshot on canvas
  const drawAnnotated = useCallback(
    (canvas: HTMLCanvasElement, step: StepData) => {
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      const img = new Image();
      const src = step.screenshot_after_b64
        ? `data:image/png;base64,${step.screenshot_after_b64}`
        : step.screenshot_after_url || "";

      if (!src) return;

      img.onload = () => {
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);

        // Get friction items for this step
        const stepFriction = frictionItems.filter(
          (f) => f.evidence_step === step.step_number,
        );

        if (stepFriction.length === 0) {
          // No specific friction for this step — add a general label
          drawBanner(ctx, canvas.width, `Step ${step.step_number}`, "#6366f1");
          return;
        }

        // Draw friction annotations
        const margin = 12;
        let yOffset = 10;

        // Top banner
        drawBanner(
          ctx,
          canvas.width,
          `Step ${step.step_number} — ${stepFriction.length} issue${stepFriction.length > 1 ? "s" : ""} detected`,
          "#dc2626",
        );

        // Issue labels on the right side
        yOffset = 50;
        for (const item of stepFriction) {
          const color = SEVERITY_COLORS[item.severity] || "#6366f1";
          const text = `[${item.severity.toUpperCase()}] ${item.category}: ${item.description}`;
          const maxWidth = canvas.width - margin * 2;
          const lines = wrapText(ctx, text, maxWidth - 20);

          const boxHeight = lines.length * 18 + 16;

          // Background
          ctx.fillStyle = "rgba(0,0,0,0.75)";
          roundRect(ctx, margin, yOffset, canvas.width - margin * 2, boxHeight, 8);
          ctx.fill();

          // Color bar on left
          ctx.fillStyle = color;
          roundRect(ctx, margin, yOffset, 4, boxHeight, 2);
          ctx.fill();

          // Text
          ctx.fillStyle = "#ffffff";
          ctx.font = "bold 13px system-ui, sans-serif";
          lines.forEach((line, i) => {
            ctx.fillText(line, margin + 14, yOffset + 18 + i * 18);
          });

          // Suggestion
          if (item.improvement_suggestion) {
            yOffset += boxHeight + 4;
            const sugLines = wrapText(ctx, `Fix: ${item.improvement_suggestion}`, maxWidth - 20);
            const sugHeight = sugLines.length * 16 + 12;

            ctx.fillStyle = "rgba(245,158,11,0.15)";
            roundRect(ctx, margin, yOffset, canvas.width - margin * 2, sugHeight, 6);
            ctx.fill();

            ctx.fillStyle = "#fbbf24";
            ctx.font = "12px system-ui, sans-serif";
            sugLines.forEach((line, i) => {
              ctx.fillText(line, margin + 14, yOffset + 14 + i * 16);
            });
            yOffset += sugHeight + 8;
          } else {
            yOffset += boxHeight + 8;
          }
        }

        // Watermark
        ctx.fillStyle = "rgba(255,255,255,0.6)";
        ctx.font = "bold 11px system-ui, sans-serif";
        ctx.fillText("PrismUX — AI-Powered UX Analysis", margin, canvas.height - 10);
      };

      img.src = src;
    },
    [frictionItems],
  );

  // Redraw when step changes
  useEffect(() => {
    if (canvasRef.current && currentStep) {
      drawAnnotated(canvasRef.current, currentStep);
    }
  }, [currentStep, drawAnnotated]);

  const downloadCurrent = useCallback(() => {
    if (!canvasRef.current || !currentStep) return;
    const link = document.createElement("a");
    link.download = `prismux-annotated-step${currentStep.step_number}.png`;
    link.href = canvasRef.current.toDataURL("image/png");
    link.click();
  }, [currentStep]);

  const downloadAll = useCallback(async () => {
    const offscreen = document.createElement("canvas");
    for (const step of steps) {
      await new Promise<void>((resolve) => {
        drawAnnotated(offscreen, step);
        // Wait for image to load
        setTimeout(() => {
          const link = document.createElement("a");
          link.download = `prismux-annotated-step${step.step_number}.png`;
          link.href = offscreen.toDataURL("image/png");
          link.click();
          resolve();
        }, 300);
      });
    }
  }, [steps, drawAnnotated]);

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-surface-400 py-4">
        <Loader2 className="w-4 h-4 animate-spin" />
        Loading screenshots...
      </div>
    );
  }

  if (steps.length === 0) return null;

  return (
    <div className="bg-white rounded-xl border border-surface-200 p-5 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-surface-700 flex items-center gap-1.5">
          <Camera className="w-4 h-4 text-primary-600" />
          Annotated Screenshots
        </h3>
        <div className="flex items-center gap-2">
          <button
            onClick={downloadCurrent}
            className="flex items-center gap-1 text-xs px-2.5 py-1.5 rounded-lg border border-surface-300 hover:bg-surface-50 transition-colors"
          >
            <Download className="w-3 h-3" />
            This Step
          </button>
          {steps.length > 1 && (
            <button
              onClick={downloadAll}
              className="flex items-center gap-1 text-xs px-2.5 py-1.5 rounded-lg bg-primary-600 text-white hover:bg-primary-700 transition-colors"
            >
              <Download className="w-3 h-3" />
              All ({steps.length})
            </button>
          )}
        </div>
      </div>

      {/* Step navigation */}
      {steps.length > 1 && (
        <div className="flex items-center justify-center gap-3 mb-3">
          <button
            onClick={() => setCurrentIdx((i) => Math.max(0, i - 1))}
            disabled={currentIdx === 0}
            className="p-1 rounded-lg hover:bg-surface-100 disabled:opacity-30"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="text-xs text-surface-500 font-mono">
            Step {currentStep?.step_number} ({currentIdx + 1}/{steps.length})
          </span>
          <button
            onClick={() => setCurrentIdx((i) => Math.min(steps.length - 1, i + 1))}
            disabled={currentIdx === steps.length - 1}
            className="p-1 rounded-lg hover:bg-surface-100 disabled:opacity-30"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}

      <canvas
        ref={canvasRef}
        className="w-full rounded-lg border border-surface-200"
        style={{ imageRendering: "auto" }}
      />
    </div>
  );
}

// ── Canvas helpers ──────────────────────────────────────────────────

function drawBanner(ctx: CanvasRenderingContext2D, width: number, text: string, color: string) {
  ctx.fillStyle = color;
  ctx.fillRect(0, 0, width, 32);
  ctx.fillStyle = "#ffffff";
  ctx.font = "bold 14px system-ui, sans-serif";
  ctx.fillText(text, 12, 22);
}

function roundRect(
  ctx: CanvasRenderingContext2D,
  x: number, y: number, w: number, h: number, r: number,
) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}

function wrapText(ctx: CanvasRenderingContext2D, text: string, maxWidth: number): string[] {
  const words = text.split(" ");
  const lines: string[] = [];
  let line = "";

  ctx.font = "bold 13px system-ui, sans-serif";
  for (const word of words) {
    const test = line ? `${line} ${word}` : word;
    if (ctx.measureText(test).width > maxWidth && line) {
      lines.push(line);
      line = word;
    } else {
      line = test;
    }
  }
  if (line) lines.push(line);
  return lines;
}
