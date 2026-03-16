import { StrictMode, Suspense, lazy } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import "./index.css";
import Home from "./pages/Home";
import NotFound from "./pages/NotFound";

// Code-split heavy pages — only loaded when navigated to
const Session = lazy(() => import("./pages/Session"));
const Comparison = lazy(() => import("./pages/Comparison"));
const Report = lazy(() => import("./pages/Report"));
const Replay = lazy(() => import("./pages/Replay"));
const History = lazy(() => import("./pages/History"));

function PageLoader() {
  return (
    <div className="flex items-center justify-center py-24 text-surface-500">
      Loading…
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/session/:sessionId" element={<Session />} />
          <Route path="/compare" element={<Comparison />} />
          <Route path="/report/:sessionId" element={<Report />} />
          <Route path="/replay/:sessionId" element={<Replay />} />
          <Route path="/history" element={<History />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  </StrictMode>,
);
