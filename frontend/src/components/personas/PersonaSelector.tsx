import { useEffect, useState } from "react";
import type { PersonaConfig } from "../../types/navigation";
import {
  Zap,
  Shield,
  Accessibility,
  Globe,
  Sparkles,
} from "lucide-react";
import CustomPersonaBuilder from "./CustomPersonaBuilder";

const PERSONA_ICONS: Record<string, typeof Zap> = {
  impatient: Zap,
  cautious: Shield,
  accessibility: Accessibility,
  non_native_english: Globe,
};

interface Props {
  selected: string | null;
  onSelect: (key: string | null) => void;
}

export default function PersonaSelector({ selected, onSelect }: Props) {
  const [personas, setPersonas] = useState<PersonaConfig[]>([]);
  const [showBuilder, setShowBuilder] = useState(false);

  function refreshPersonas() {
    fetch("/api/personas")
      .then((r) => r.json())
      .then(setPersonas)
      .catch(() => {});
  }

  useEffect(() => {
    refreshPersonas();
  }, []);

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-surface-700">
        Persona Mode
      </label>
      <div className="grid grid-cols-2 gap-2">
        <button
          onClick={() => onSelect(null)}
          className={`p-3 rounded-lg border text-left text-sm transition-all ${
            selected === null
              ? "border-primary-500 bg-primary-50 ring-1 ring-primary-500"
              : "border-surface-200 hover:border-surface-300"
          }`}
        >
          <div className="font-medium">Default</div>
          <div className="text-surface-500 text-xs mt-0.5">No persona bias</div>
        </button>
        {personas.map((p) => {
          const Icon = PERSONA_ICONS[p.key] || Sparkles;
          const isCustom = p.key.startsWith("custom_");
          return (
            <button
              key={p.key}
              onClick={() => onSelect(p.key)}
              className={`p-3 rounded-lg border text-left text-sm transition-all ${
                selected === p.key
                  ? "border-primary-500 bg-primary-50 ring-1 ring-primary-500"
                  : isCustom
                    ? "border-purple-200 hover:border-purple-300"
                    : "border-surface-200 hover:border-surface-300"
              }`}
            >
              <div className="flex items-center gap-1.5 font-medium">
                <Icon className="w-3.5 h-3.5" />
                {p.name}
                {isCustom && (
                  <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-purple-100 text-purple-600">
                    Custom
                  </span>
                )}
              </div>
              <div className="text-surface-500 text-xs mt-0.5 line-clamp-1">
                {p.description}
              </div>
            </button>
          );
        })}
        {/* Create custom persona button */}
        {!showBuilder && (
          <button
            onClick={() => setShowBuilder(true)}
            className="p-3 rounded-lg border border-dashed border-primary-300 text-left text-sm hover:bg-primary-50/50 transition-all"
          >
            <div className="flex items-center gap-1.5 font-medium text-primary-600">
              <Sparkles className="w-3.5 h-3.5" />
              Create Custom
            </div>
            <div className="text-surface-500 text-xs mt-0.5">
              Build your own persona
            </div>
          </button>
        )}
      </div>
      {showBuilder && (
        <CustomPersonaBuilder
          onCreated={(key) => {
            setShowBuilder(false);
            refreshPersonas();
            onSelect(key);
          }}
          onCancel={() => setShowBuilder(false)}
        />
      )}
    </div>
  );
}
