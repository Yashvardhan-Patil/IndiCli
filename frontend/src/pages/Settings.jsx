import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { forecastApi, datasetsApi } from "@/api/client";
import api from "@/api/client";
import Topbar from "@/components/ui/Topbar";
import { Card, Badge, Spinner, SectionHeader } from "@/components/ui";
import toast from "react-hot-toast";

export default function Settings() {
  const { data: health, refetch: refetchHealth, isLoading: loadHealth } = useQuery({
    queryKey: ["health"],
    queryFn:  () => api.get("/health").then((r) => r.data),
    staleTime: 30 * 1000,
  });

  const { data: meta } = useQuery({
    queryKey: ["dataset-meta"],
    queryFn:  () => datasetsApi.getMeta().then((r) => r.data),
    staleTime: Infinity,
  });

  const trainMut = useMutation({
    mutationFn: () => forecastApi.trainModels(),
    onSuccess:  () => toast.success("Model training started in background"),
    onError:    (e) => toast.error(e.message),
  });

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <Topbar title="Settings & Configuration" />
      <div className="flex-1 overflow-y-auto p-6 space-y-6">

        {/* API Health */}
        <Card>
          <SectionHeader title="API Health Check"
            action={
              <button onClick={refetchHealth} className="btn-secondary text-xs px-2 py-1">
                Refresh
              </button>
            } />
          {loadHealth ? <Spinner /> : health ? (
            <div className="space-y-2 text-sm">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                <span className="text-green-400 font-medium">API Operational</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Dataset rows loaded</span>
                <span className="font-mono">{health.dataset_rows?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Data coverage</span>
                <span className="font-mono">{health.date_range}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>API base URL</span>
                <span className="font-mono text-xs">
                  {import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"}
                </span>
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-red-400">
              <span className="w-2 h-2 rounded-full bg-red-500" />
              Backend unreachable — ensure FastAPI is running
            </div>
          )}
        </Card>

        {/* Dataset info */}
        {meta && (
          <Card>
            <SectionHeader title="Active Dataset" />
            <div className="space-y-2 text-sm text-slate-300">
              {Object.entries(meta).map(([k, v]) => (
                <div key={k} className="flex justify-between border-b border-surface-border pb-1">
                  <span className="text-slate-500 capitalize">{k.replace(/_/g, " ")}</span>
                  <span className="font-mono text-xs">{String(v)}</span>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Model training */}
        <Card>
          <SectionHeader title="AI Model Management"
            subtitle="Train XGBoost + LSTM models on the loaded dataset" />
          <div className="space-y-3">
            <p className="text-sm text-slate-400">
              Models are trained on India-level daily aggregates.
              Training runs in the background — check backend logs for progress.
            </p>
            <div className="flex items-center gap-4">
              <button
                onClick={() => trainMut.mutate()}
                disabled={trainMut.isPending}
                className="btn-primary flex items-center gap-2"
              >
                {trainMut.isPending ? <><Spinner size="sm" /> Starting...</> : "🤖 Train Models"}
              </button>
              <Badge variant="info">XGBoost + LSTM Ensemble</Badge>
            </div>
          </div>
        </Card>

        {/* Environment variables */}
        <Card>
          <SectionHeader title="Environment Variables" />
          <div className="space-y-2 text-sm font-mono">
            {[
              ["VITE_API_BASE_URL", import.meta.env.VITE_API_BASE_URL || "not set"],
              ["VITE_CESIUM_TOKEN", import.meta.env.VITE_CESIUM_TOKEN ? "✓ set" : "⚠️ not set"],
              ["MODE", import.meta.env.MODE],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between border-b border-surface-border/50 pb-1">
                <span className="text-slate-500">{k}</span>
                <span className={v?.includes("not set") || v?.includes("⚠️") ? "text-amber-400" : "text-green-400"}>
                  {v}
                </span>
              </div>
            ))}
          </div>
          <p className="text-xs text-slate-500 mt-3">
            Edit <code className="text-brand-400">frontend/.env</code> to configure tokens.
          </p>
        </Card>
      </div>
    </div>
  );
}
