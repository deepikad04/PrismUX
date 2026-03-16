import { useState } from "react";
import { Plus, Sparkles, X } from "lucide-react";

const TRAIT_SUGGESTIONS = [
  "Skips reading long text",
  "Keyboard-only navigation",
  "Dislikes popups and modals",
  "Security-conscious",
  "Prefers simple language",
  "Impatient with loading times",
  "Needs high contrast",
  "Avoids sharing personal data",
];

const FOCUS_AREAS = [
  "navigation",
  "contrast",
  "affordance",
  "copy",
  "error",
  "performance",
  "accessibility",
];

interface Props {
  onCreated: (personaKey: string) => void;
  onCancel: () => void;
}

export default function CustomPersonaBuilder({ onCreated, onCancel }: Props) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [traits, setTraits] = useState<string[]>([]);
  const [customTrait, setCustomTrait] = useState("");
  const [focusAreas, setFocusAreas] = useState<string[]>([]);
  const [instructions, setInstructions] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function toggleTrait(t: string) {
    setTraits((prev) =>
      prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t],
    );
  }

  function addCustomTrait() {
    const t = customTrait.trim();
    if (t && !traits.includes(t)) {
      setTraits((prev) => [...prev, t]);
      setCustomTrait("");
    }
  }

  function toggleFocus(f: string) {
    setFocusAreas((prev) =>
      prev.includes(f) ? prev.filter((x) => x !== f) : [...prev, f],
    );
  }

  async function handleCreate() {
    if (!name.trim() || !description.trim()) return;
    setLoading(true);
    setError(null);

    try {
      const res = await fetch("/api/personas/custom", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name.trim(),
          description: description.trim(),
          behavioral_traits: traits,
          focus_areas: focusAreas,
          custom_instructions: instructions.trim(),
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const persona = await res.json();
      onCreated(persona.key);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create persona");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-white rounded-xl border border-primary-200 p-5 shadow-sm space-y-4 animate-slide-up">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold flex items-center gap-1.5">
          <Sparkles className="w-4 h-4 text-primary-600" />
          Custom Persona Builder
        </h3>
        <button onClick={onCancel} className="text-surface-400 hover:text-surface-600">
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-surface-600 mb-1">
            Persona Name
          </label>
          <input
            type="text"
            placeholder="e.g. Elderly User"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-surface-300 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-surface-600 mb-1">
            Description
          </label>
          <input
            type="text"
            placeholder="e.g. User with low vision who needs large text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-surface-300 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
      </div>

      <div>
        <label className="block text-xs font-medium text-surface-600 mb-2">
          Behavioral Traits
        </label>
        <div className="flex flex-wrap gap-1.5 mb-2">
          {TRAIT_SUGGESTIONS.map((t) => (
            <button
              key={t}
              onClick={() => toggleTrait(t)}
              className={`text-xs px-2.5 py-1 rounded-full border transition-all ${
                traits.includes(t)
                  ? "border-primary-500 bg-primary-50 text-primary-700"
                  : "border-surface-300 text-surface-500 hover:border-surface-400"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Add custom trait..."
            value={customTrait}
            onChange={(e) => setCustomTrait(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && addCustomTrait()}
            className="flex-1 px-3 py-1.5 rounded-lg border border-surface-300 text-xs focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
          <button
            onClick={addCustomTrait}
            className="px-2 py-1.5 rounded-lg border border-surface-300 text-surface-500 hover:bg-surface-50 text-xs"
          >
            <Plus className="w-3.5 h-3.5" />
          </button>
        </div>
        {traits.filter((t) => !TRAIT_SUGGESTIONS.includes(t)).length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {traits
              .filter((t) => !TRAIT_SUGGESTIONS.includes(t))
              .map((t) => (
                <span
                  key={t}
                  className="text-xs px-2 py-0.5 rounded-full bg-primary-50 text-primary-700 border border-primary-200 flex items-center gap-1"
                >
                  {t}
                  <button onClick={() => toggleTrait(t)} className="hover:text-red-500">
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
          </div>
        )}
      </div>

      <div>
        <label className="block text-xs font-medium text-surface-600 mb-2">
          Focus Areas
        </label>
        <div className="flex flex-wrap gap-1.5">
          {FOCUS_AREAS.map((f) => (
            <button
              key={f}
              onClick={() => toggleFocus(f)}
              className={`text-xs px-2.5 py-1 rounded-full border capitalize transition-all ${
                focusAreas.includes(f)
                  ? "border-primary-500 bg-primary-50 text-primary-700"
                  : "border-surface-300 text-surface-500 hover:border-surface-400"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-xs font-medium text-surface-600 mb-1">
          Additional Instructions (optional)
        </label>
        <textarea
          rows={2}
          placeholder="Any specific instructions for how this persona should navigate..."
          value={instructions}
          onChange={(e) => setInstructions(e.target.value)}
          className="w-full px-3 py-2 rounded-lg border border-surface-300 text-xs focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
        />
      </div>

      {error && (
        <div className="text-xs text-red-600 bg-red-50 rounded-lg px-3 py-2">
          {error}
        </div>
      )}

      <button
        onClick={handleCreate}
        disabled={loading || !name.trim() || !description.trim()}
        className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-primary-600 to-primary-700 text-white rounded-xl font-medium text-sm hover:from-primary-700 hover:to-primary-800 transition-all shadow-lg shadow-primary-600/25 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? (
          <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
        ) : (
          <Sparkles className="w-4 h-4" />
        )}
        {loading ? "Creating..." : "Create Persona"}
      </button>
    </div>
  );
}
