import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Loader2, AlertTriangle, FileText, ArrowLeft } from "lucide-react";
import Layout from "../components/ui/Layout";
import SessionReplay from "../components/navigator/SessionReplay";
import type { NavigationStep } from "../types/navigation";

export default function Replay() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [steps, setSteps] = useState<NavigationStep[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    fetch(`/api/navigate/${sessionId}/steps`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setSteps)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [sessionId]);

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center py-24">
          <Loader2 className="w-6 h-6 animate-spin text-primary-600" />
          <span className="ml-2 text-surface-600">Loading session...</span>
        </div>
      </Layout>
    );
  }

  if (error || !steps.length) {
    const isExpired = error === "HTTP 404";
    return (
      <Layout>
        <div className="max-w-2xl mx-auto px-4 py-16 text-center">
          <AlertTriangle
            className={`w-8 h-8 mx-auto mb-3 ${isExpired ? "text-amber-500" : "text-red-500"}`}
          />
          <p className={isExpired ? "text-amber-700 font-medium" : "text-red-600"}>
            {isExpired
              ? "Session expired — navigation data is no longer in memory."
              : error || "No steps found for this session."}
          </p>
          {isExpired && (
            <p className="text-surface-500 text-sm mt-2">
              Sessions are kept in memory while the server is running. Restart a
              new navigation to generate fresh replay data.
            </p>
          )}
          <Link
            to="/history"
            className="inline-flex items-center gap-1.5 mt-6 px-4 py-2 text-sm bg-surface-100 hover:bg-surface-200 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to History
          </Link>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto px-4 py-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-xl font-bold">Session Replay</h1>
            <p className="text-xs text-surface-500 font-mono">{sessionId}</p>
          </div>
          <div className="flex items-center gap-2">
            <Link
              to={`/report/${sessionId}`}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-surface-300 rounded-lg hover:bg-surface-50 transition-colors"
            >
              <FileText className="w-3.5 h-3.5" />
              Report
            </Link>
            <Link
              to="/history"
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-surface-300 rounded-lg hover:bg-surface-50 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              History
            </Link>
          </div>
        </div>
        <SessionReplay steps={steps} />
      </div>
    </Layout>
  );
}
