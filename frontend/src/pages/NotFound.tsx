import { Link } from "react-router-dom";
import { Compass, ArrowLeft } from "lucide-react";
import Layout from "../components/ui/Layout";

export default function NotFound() {
  return (
    <Layout>
      <div className="flex flex-col items-center justify-center py-24 px-4">
        <div className="p-3 rounded-xl bg-surface-100 mb-4">
          <Compass className="w-10 h-10 text-surface-400" />
        </div>
        <h1 className="text-2xl font-bold text-surface-900 mb-2">
          Page Not Found
        </h1>
        <p className="text-surface-500 text-sm mb-6 text-center max-w-md">
          The page you're looking for doesn't exist or the session has expired.
        </p>
        <Link
          to="/"
          className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-primary-600 to-primary-700 text-white rounded-xl font-medium text-sm hover:from-primary-700 hover:to-primary-800 transition-all shadow-lg shadow-primary-600/25"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Home
        </Link>
      </div>
    </Layout>
  );
}
