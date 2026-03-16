import { useCallback, useEffect, useRef } from "react";
import type { ThoughtEvent, NavigationStep } from "../types/navigation";

// ── Tiny synthesized audio cues via Web Audio API ──────────────────
function beep(
  ctx: AudioContext,
  freq: number,
  duration: number,
  type: OscillatorType = "sine",
  gain = 0.12,
) {
  const osc = ctx.createOscillator();
  const vol = ctx.createGain();
  osc.type = type;
  osc.frequency.value = freq;
  vol.gain.value = gain;
  osc.connect(vol).connect(ctx.destination);
  osc.start();
  vol.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
  osc.stop(ctx.currentTime + duration);
}

function playClick(ctx: AudioContext) {
  beep(ctx, 800, 0.08, "square", 0.06);
  setTimeout(() => beep(ctx, 1200, 0.06, "square", 0.04), 40);
}

function playFriction(ctx: AudioContext) {
  beep(ctx, 320, 0.15, "sawtooth", 0.08);
  setTimeout(() => beep(ctx, 260, 0.2, "sawtooth", 0.06), 100);
}

function playSuccess(ctx: AudioContext) {
  beep(ctx, 523, 0.12, "sine", 0.1);
  setTimeout(() => beep(ctx, 659, 0.12, "sine", 0.1), 120);
  setTimeout(() => beep(ctx, 784, 0.18, "sine", 0.1), 240);
}

function playScroll(ctx: AudioContext) {
  beep(ctx, 440, 0.05, "sine", 0.03);
}

function playType(ctx: AudioContext) {
  beep(ctx, 600 + Math.random() * 200, 0.04, "square", 0.03);
}

// ── Hook ───────────────────────────────────────────────────────────

interface UseAudioFeedbackOptions {
  narrationEnabled: boolean;
  cuesEnabled: boolean;
}

export function useAudioFeedback({
  narrationEnabled,
  cuesEnabled,
}: UseAudioFeedbackOptions) {
  const audioCtxRef = useRef<AudioContext | null>(null);
  const lastSpokenRef = useRef(0); // index of last spoken thought
  const utteranceQueueRef = useRef<SpeechSynthesisUtterance[]>([]);
  const isSpeakingRef = useRef(false);

  // Lazily init AudioContext (needs user gesture on some browsers)
  const getAudioCtx = useCallback(() => {
    if (!audioCtxRef.current) {
      audioCtxRef.current = new AudioContext();
    }
    if (audioCtxRef.current.state === "suspended") {
      audioCtxRef.current.resume();
    }
    return audioCtxRef.current;
  }, []);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      speechSynthesis.cancel();
      audioCtxRef.current?.close();
    };
  }, []);

  // Process utterance queue sequentially
  const processQueue = useCallback(() => {
    if (isSpeakingRef.current || utteranceQueueRef.current.length === 0) return;
    isSpeakingRef.current = true;
    const utt = utteranceQueueRef.current.shift()!;
    utt.onend = () => {
      isSpeakingRef.current = false;
      processQueue();
    };
    utt.onerror = () => {
      isSpeakingRef.current = false;
      processQueue();
    };
    speechSynthesis.speak(utt);
  }, []);

  // Speak new thoughts as they arrive
  const speakThoughts = useCallback(
    (thoughts: ThoughtEvent[]) => {
      if (!narrationEnabled) return;
      const newThoughts = thoughts.slice(lastSpokenRef.current);
      lastSpokenRef.current = thoughts.length;

      for (const t of newThoughts) {
        // Only narrate perceive and evaluate phases (plan/act are too rapid)
        if (t.phase !== "perceive" && t.phase !== "evaluate") continue;

        // Shorten the message for speech
        let text = t.message;
        if (text.length > 150) text = text.slice(0, 150);

        const utt = new SpeechSynthesisUtterance(text);
        utt.rate = 1.3;
        utt.pitch = t.phase === "evaluate" ? 0.9 : 1.0;
        utt.volume = 0.8;
        utteranceQueueRef.current.push(utt);
      }
      processQueue();
    },
    [narrationEnabled, processQueue],
  );

  // Play audio cue for a step's action
  const playStepCue = useCallback(
    (step: NavigationStep) => {
      if (!cuesEnabled) return;
      const ctx = getAudioCtx();
      const action = step.plan.action_type;
      const hasFriction = step.evaluation.friction_detected.length > 0;

      if (hasFriction) {
        playFriction(ctx);
      } else if (action === "click") {
        playClick(ctx);
      } else if (action === "scroll_down" || action === "scroll_up") {
        playScroll(ctx);
      } else if (action === "type") {
        playType(ctx);
      } else if (action === "done") {
        playSuccess(ctx);
      }
    },
    [cuesEnabled, getAudioCtx],
  );

  // Reset spoken index (for new sessions)
  const reset = useCallback(() => {
    lastSpokenRef.current = 0;
    speechSynthesis.cancel();
    utteranceQueueRef.current = [];
    isSpeakingRef.current = false;
  }, []);

  return { speakThoughts, playStepCue, reset };
}
