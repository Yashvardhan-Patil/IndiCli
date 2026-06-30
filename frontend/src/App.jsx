import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";
import Sidebar from "@/components/ui/Sidebar";
import Dashboard   from "@/pages/Dashboard";
import ClimateTwin from "@/pages/ClimateTwin";
import Forecasting from "@/pages/Forecasting";
import Simulation  from "@/pages/Simulation";
import Analytics   from "@/pages/Analytics";
import Settings    from "@/pages/Settings";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 2 * 60 * 1000,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="flex h-screen bg-surface text-slate-100 overflow-hidden">
          <Sidebar />
          <main className="flex-1 flex flex-col overflow-hidden">
            <Routes>
              <Route path="/"            element={<Dashboard />} />
              <Route path="/twin"        element={<ClimateTwin />} />
              <Route path="/forecasting" element={<Forecasting />} />
              <Route path="/simulation"  element={<Simulation />} />
              <Route path="/analytics"   element={<Analytics />} />
              <Route path="/settings"    element={<Settings />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          style: { background: "#1e293b", color: "#f1f5f9", border: "1px solid #334155" },
        }}
      />
    </QueryClientProvider>
  );
}
