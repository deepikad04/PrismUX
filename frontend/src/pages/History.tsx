import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Loader2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  FileText,
  Play,
  ExternalLink,
} from "lucide-react";
import Layout from "../components/ui/Layout";

interface SessionEntry {
  id: string;
  url: string;
  goal: string;
  persona: string | null;
  status: string;
  created_at: string;
  total_steps: number;
  completed: boolean;
}

const STATUS_CONFIG: Record<
  string,
  { icon: typeof CheckCircle2; color: string; label: string }
> = {
  completed: { icon: CheckCircle2, color: "text-green-600", label: "Completed" },
  abandoned: { icon: AlertTriangle, color: "text-amber-600", label: "Abandoned" },
  blocked: { icon: XCircle, color: "text-red-600", label: "Blocked" },
  error: { icon: XCircle, color: "text-red-600", label: "Error" },
  running: { icon: Loader2, color: "text-primary-600", label: "Running" },
  created: { icon: Clock, color: "text-surface-400", label: "Created" },
};

export default function History() {
  const [sessions, setSessions] = useState<SessionEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/sessions")
      .then((r) => r.json())
      .then((data: SessionEntry[]) => {
        // Sort by created_at descending
        data.sort(
          (a, b) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
        );
        setSessions(data);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center py-24">
          <Loader2 className="w-6 h-6 animate-spin text-primary-600" />
          <span className="ml-2 text-surface-600">Loading sessions...</span>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-5xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold">Session History</h1>
            <p className="text-surface-500 text-sm mt-1">
              {sessions.length} session{sessions.length !== 1 ? "s" : ""} recorded
            </p>
          </div>
          <Link
            to="/"
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-primary-600 to-primary-700 text-white rounded-xl font-medium text-sm hover:from-primary-700 hover:to-primary-800 transition-all shadow-lg shadow-primary-600/25"
          >
            <Play className="w-4 h-4" />
            New Session
          </Link>
        </div>

        {sessions.length === 0 ? (
          <div className="text-center py-20">
            <div className="relative inline-block mb-4">
              <div className="w-16 h-16 rounded-2xl bg-surface-100 flex items-center justify-center">
                <Clock className="w-8 h-8 text-surface-300" />
              </div>
              <div className="absolute -top-1 -right-1 w-6 h-6 rounded-full bg-primary-100 flex items-center justify-center">
                <Play className="w-3 h-3 text-primary-500" />
              </div>
            </div>
            <p className="text-surface-700 font-medium">No sessions yet</p>
            <p className="text-surface-400 text-sm mt-1">Start a navigation session from the home page to see results here.</p>
            <Link
              to="/"
              className="inline-flex items-center gap-2 mt-4 px-4 py-2 bg-gradient-to-r from-primary-600 to-purple-600 text-white rounded-xl font-medium text-sm hover:from-primary-700 hover:to-purple-700 transition-all shadow-lg shadow-primary-600/25"
            >
              <Play className="w-4 h-4" />
              Start First Session
            </Link>
          </div>
        ) : (
          <div className="space-y-2">
            {sessions.map((s) => {
              const cfg = STATUS_CONFIG[s.status] || STATUS_CONFIG.created;
              const StatusIcon = cfg.icon;
              const isFinished = ["completed", "abandoned", "blocked", "error"].includes(s.status);
              const date = new Date(s.created_at);
              const timeStr = date.toLocaleString(undefined, {
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              });

              return (
                <div
                  key={s.id}
                  className="bg-white rounded-xl border border-surface-200 p-4 shadow-sm hover-lift animate-slide-up"
                  style={{ animationDelay: `${sessions.indexOf(s) * 50}ms` }}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3 min-w-0 flex-1">
                      <StatusIcon
                        className={`w-5 h-5 mt-0.5 shrink-0 ${cfg.color} ${
                          s.status === "running" ? "animate-spin" : ""
                        }`}
                      />
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-sm font-semibold truncate max-w-md">
                            {s.goal}
                          </span>
                          <span
                            className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${
                              s.status === "completed"
                                ? "bg-green-100 text-green-700"
                                : s.status === "running"
                                  ? "bg-primary-100 text-primary-700"
                                  : s.status === "created"
                                    ? "bg-surface-100 text-surface-600"
                                    : "bg-red-100 text-red-700"
                            }`}
                          >
                            {cfg.label}
                          </span>
                        </div>
                        <div className="flex items-center gap-3 mt-1 text-xs text-surface-500">
                          <span className="flex items-center gap-1 truncate max-w-xs">
                            <ExternalLink className="w-3 h-3" />
                            {s.url}
                          </span>
                          {s.persona && (
                            <span className="px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 text-[10px] font-medium">
                              {s.persona}
                            </span>
                          )}
                          <span>{s.total_steps} steps</span>
                          <span>{timeStr}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-1.5 shrink-0">
                      {isFinished && (
                        <>
                          <Link
                            to={`/replay/${s.id}`}
                            className="flex items-center gap-1 px-2.5 py-1.5 text-xs border border-surface-300 rounded-lg hover:bg-surface-50 transition-colors"
                          >
                            <Play className="w-3 h-3" />
                            Replay
                          </Link>
                          <Link
                            to={`/report/${s.id}`}
                            className="flex items-center gap-1 px-2.5 py-1.5 text-xs border border-surface-300 rounded-lg hover:bg-surface-50 transition-colors"
                          >
                            <FileText className="w-3 h-3" />
                            Report
                          </Link>
                        </>
                      )}
                      {s.status === "running" && (
                        <Link
                          to={`/session/${s.id}`}
                          className="flex items-center gap-1 px-2.5 py-1.5 text-xs bg-primary-50 text-primary-700 border border-primary-200 rounded-lg hover:bg-primary-100 transition-colors"
                        >
                          Watch Live
                        </Link>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </Layout>
  );
}
