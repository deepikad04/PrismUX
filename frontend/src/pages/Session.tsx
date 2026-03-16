import { useEffect, useState, useRef, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import {
  Clock,
  Footprints,
  CheckCircle2,
  XCircle,
  Loader2,
  FileText,
  Play,
  Volume2,
  VolumeX,
  Music,
  Send,
  MessageSquare,
} from "lucide-react";
import Layout from "../components/ui/Layout";
import ScreenshotViewer from "../components/navigator/ScreenshotViewer";
import StepLog from "../components/navigator/StepLog";
import ThoughtStream from "../components/navigator/ThoughtStream";
import { useSSE } from "../hooks/useSSE";
import { useAudioFeedback } from "../hooks/useAudioFeedback";

const MAX_STEPS = 30;

export default function Session() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { steps, thoughts, status, metrics, error, start } = useSSE();
  const [selectedStep, setSelectedStep] = useState<number | null>(null);
  const [isPreClick, setIsPreClick] = useState(true);
  const [narrationOn, setNarrationOn] = useState(true);
  const [cuesOn, setCuesOn] = useState(true);
  const [hint, setHint] = useState("");
  const [hints, setHints] = useState<string[]>([]);
  const prevStepCountRef = useRef(0);

  const sendHint = useCallback(async () => {
    const text = hint.trim();
    if (!text || !sessionId) return;
    setHint("");
    setHints((prev) => [...prev, text]);
    try {
      await fetch(`/api/navigate/${sessionId}/hint`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ hint: text }),
      });
    } catch {
      // Best-effort — agent may have already finished
    }
  }, [hint, sessionId]);

  const { speakThoughts, playStepCue, reset } = useAudioFeedback({
    narrationEnabled: narrationOn,
    cuesEnabled: cuesOn,
  });

  useEffect(() => {
    if (sessionId && status === "idle") {
      reset();
      start(sessionId);
    }
  }, [sessionId, status, start, reset]);

  // Narrate new thoughts
  useEffect(() => {
    speakThoughts(thoughts);
  }, [thoughts, speakThoughts]);

  // Play audio cues for new steps
  useEffect(() => {
    if (steps.length > prevStepCountRef.current) {
      const newStep = steps[steps.length - 1];
      playStepCue(newStep);
      prevStepCountRef.current = steps.length;
    }
  }, [steps, playStepCue]);

  // Auto-select latest step
  useEffect(() => {
    if (steps.length > 0) {
      setSelectedStep(steps[steps.length - 1].step_number);
      setIsPreClick(true);
      const timer = setTimeout(() => setIsPreClick(false), 1500);
      return () => clearTimeout(timer);
    }
  }, [steps.length]);

  const currentStep =
    steps.find((s) => s.step_number === selectedStep) || null;

  const isActive = status === "running" || status === "connecting";
  const progress = Math.min((steps.length / MAX_STEPS) * 100, 100);

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 py-4">
        {/* Top status bar */}
        <div className={`rounded-xl px-4 py-3 mb-4 shadow-sm transition-all duration-500 ${
          isActive
            ? "bg-gradient-to-r from-primary-600/10 via-purple-500/10 to-primary-600/10 border border-primary-200"
            : "glass"
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {isActive ? (
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-primary-500" />
                </span>
              ) : status === "completed" ? (
                <CheckCircle2 className="w-4 h-4 text-green-600" />
              ) : status === "error" ? (
                <XCircle className="w-4 h-4 text-red-600" />
              ) : (
                <Loader2 className="w-4 h-4 text-surface-400" />
              )}
              <span
                className={`text-sm font-medium ${
                  isActive
                    ? "text-primary-600"
                    : status === "completed"
                      ? "text-green-600"
                      : status === "error"
                        ? "text-red-600"
                        : "text-surface-500"
                }`}
              >
                {isActive
                  ? "Navigating..."
                  : status === "completed"
                    ? "Completed"
                    : status === "error"
                      ? "Error"
                      : "Initializing..."}
              </span>
              <span className="text-xs text-surface-400 font-mono">
                {sessionId}
              </span>
            </div>
            <div className="flex items-center gap-4 text-sm text-surface-600">
              {/* Audio toggles */}
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setNarrationOn((v) => !v)}
                  className={`p-1.5 rounded-lg transition-colors ${narrationOn ? "bg-primary-100 text-primary-700" : "text-surface-400 hover:text-surface-600"}`}
                  title={narrationOn ? "Mute narration" : "Enable narration"}
                >
                  {narrationOn ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
                </button>
                <button
                  onClick={() => setCuesOn((v) => !v)}
                  className={`p-1.5 rounded-lg transition-colors ${cuesOn ? "bg-primary-100 text-primary-700" : "text-surface-400 hover:text-surface-600"}`}
                  title={cuesOn ? "Mute sound cues" : "Enable sound cues"}
                >
                  <Music className={`w-3.5 h-3.5 ${cuesOn ? "" : "opacity-50"}`} />
                </button>
              </div>
              <span className="flex items-center gap-1">
                <Footprints className="w-4 h-4" />
                Step {steps.length} / {MAX_STEPS}
              </span>
              {metrics && (
                <span className="flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  {metrics.time_seconds.toFixed(1)}s
                </span>
              )}
              {status === "completed" && sessionId && (
                <>
                  <Link
                    to={`/replay/${sessionId}`}
                    className="flex items-center gap-1 text-surface-600 hover:text-primary-600 font-medium"
                  >
                    <Play className="w-4 h-4" />
                    Replay
                  </Link>
                  <Link
                    to={`/report/${sessionId}`}
                    className="flex items-center gap-1 text-primary-600 hover:text-primary-700 font-medium"
                  >
                    <FileText className="w-4 h-4" />
                    View Report
                  </Link>
                </>
              )}
            </div>
          </div>
          {/* Progress bar */}
          {isActive && (
            <div className="mt-2 h-1 bg-surface-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-primary-500 to-primary-400 rounded-full transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
          )}
        </div>

        {error && (
          <div className="mb-4 text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">
            {error}
          </div>
        )}

        {/* Main content: screenshot + thought stream + step log */}
        <div className="grid grid-cols-1 lg:grid-cols-7 gap-4">
          <div className={`lg:col-span-3 rounded-xl transition-shadow duration-700 ${
            isActive ? "shadow-[0_0_30px_-5px_rgba(76,110,245,0.3)]" : ""
          }`}>
            <ScreenshotViewer step={currentStep} isPreClick={isPreClick} />
          </div>
          <div className="lg:col-span-2 flex flex-col gap-3">
            <div className="glass rounded-xl p-3 shadow-sm flex-1">
              <h3 className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <span className="relative flex h-2 w-2">
                  {isActive && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75" />}
                  <span className={`relative inline-flex rounded-full h-2 w-2 ${isActive ? "bg-purple-500" : "bg-surface-300"}`} />
                </span>
                Agent Thoughts
              </h3>
              <ThoughtStream thoughts={thoughts} />
            </div>

            {/* Mid-navigation hint input */}
            {isActive && (
              <div className="glass rounded-xl p-3 shadow-sm animate-fade-in">
                <h3 className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <MessageSquare className="w-3 h-3" />
                  Guide the Agent
                </h3>
                {hints.length > 0 && (
                  <div className="space-y-1 mb-2">
                    {hints.map((h, i) => (
                      <div key={i} className="text-xs bg-primary-50 text-primary-700 rounded-lg px-2 py-1 flex items-center gap-1.5">
                        <Send className="w-3 h-3 shrink-0" />
                        {h}
                      </div>
                    ))}
                  </div>
                )}
                <form
                  onSubmit={(e) => { e.preventDefault(); sendHint(); }}
                  className="flex gap-2"
                >
                  <input
                    type="text"
                    value={hint}
                    onChange={(e) => setHint(e.target.value)}
                    placeholder="Try the hamburger menu..."
                    className="flex-1 text-xs px-3 py-2 rounded-lg border border-surface-300 focus:outline-none focus:ring-2 focus:ring-primary-400"
                  />
                  <button
                    type="submit"
                    disabled={!hint.trim()}
                    className="px-3 py-2 rounded-lg bg-primary-600 text-white text-xs font-medium disabled:opacity-40 hover:bg-primary-700 transition-colors"
                  >
                    <Send className="w-3.5 h-3.5" />
                  </button>
                </form>
              </div>
            )}
          </div>
          <div className="lg:col-span-2">
            <StepLog
              steps={steps}
              selectedStep={selectedStep}
              onSelectStep={(n) => {
                setSelectedStep(n);
                setIsPreClick(false);
              }}
            />
          </div>
        </div>

        {/* Metrics summary on completion */}
        {metrics && status === "completed" && (
          <div className="mt-6 grid grid-cols-2 md:grid-cols-6 gap-3">
            {[
              { label: "Steps", value: metrics.total_steps },
              { label: "Retries", value: metrics.retries },
              { label: "Backtracks", value: metrics.backtracks },
              {
                label: "Time",
                value: `${metrics.time_seconds.toFixed(1)}s`,
              },
              { label: "Friction", value: metrics.friction_count },
              { label: "Outcome", value: metrics.outcome },
            ].map((m, i) => (
              <div
                key={m.label}
                className="bg-white rounded-xl border border-surface-200 border-t-2 border-t-primary-400 p-3 text-center shadow-sm hover-lift animate-count-up"
                style={{ animationDelay: `${i * 100}ms` }}
              >
                <div className="text-xs text-surface-500 uppercase tracking-wider">
                  {m.label}
                </div>
                <div className="text-lg font-semibold mt-1">{m.value}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
