import Layout from "../components/ui/Layout";
import ArchitectureDiagram from "../components/ui/ArchitectureDiagram";

export default function Architecture() {
  return (
    <Layout>
      <div className="max-w-5xl mx-auto px-4 py-10">
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-primary-700 to-primary-500 bg-clip-text text-transparent">
            System Architecture
          </h1>
          <p className="mt-3 text-surface-600 max-w-xl mx-auto">
            PrismUX uses a Perceive-Plan-Act-Evaluate (PPAE) loop powered by
            Gemini 2.0 Flash multimodal vision and Google ADK to autonomously
            navigate and evaluate web UIs.
          </p>
        </div>

        <div className="glass rounded-2xl p-6 shadow-lg">
          <ArchitectureDiagram />
        </div>

        {/* Tech highlights */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
          {[
            {
              title: "Multimodal AI Vision",
              description:
                "Gemini 2.0 Flash analyzes screenshots at 1280x720 resolution, detecting UI elements, bounding boxes, and accessibility issues in a single API call.",
              color: "border-t-red-400",
            },
            {
              title: "Google ADK Agent",
              description:
                "Built with google-adk LlmAgent and LoopAgent for autonomous tool-calling navigation. Playwright actions exposed as FunctionTools.",
              color: "border-t-blue-400",
            },
            {
              title: "Persona-Based Testing",
              description:
                "4 distinct personas (elderly, low-vision, non-native speaker, impatient) evaluate UIs through different friction lenses simultaneously.",
              color: "border-t-purple-400",
            },
          ].map((card) => (
            <div
              key={card.title}
              className={`bg-white rounded-xl border border-surface-200 border-t-2 ${card.color} p-5 shadow-sm`}
            >
              <h3 className="font-semibold text-surface-800 mb-2">
                {card.title}
              </h3>
              <p className="text-sm text-surface-600 leading-relaxed">
                {card.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </Layout>
  );
}
