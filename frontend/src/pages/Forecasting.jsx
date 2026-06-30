import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { forecastApi } from "@/api/client";
import useStore from "@/store/useStore";
import Topbar from "@/components/ui/Topbar";
import { Card, StatCard, Spinner, Badge, SectionHeader } from "@/components/ui";
import { ForecastChart } from "@/components/charts/ClimateCharts";
import toast from "react-hot-toast";

const MODEL_OPTIONS = [
  { value: "ensemble", label: "Hybrid Ensemble (XGBoost + LSTM)" },
  { value: "xgboost",  label: "XGBoost Only" },
  { value: "lstm",     label: "LSTM Only" },
];

export default function Forecasting() {
  const { selectedLat, selectedLon } = useStore();
  const [lat, setLat]           = useState(selectedLat || 20.59);
  const [lon, setLon]           = useState(selectedLon || 78.96);
  const [horizon, setHorizon]   = useState(30);
  const [model, setModel]       = useState("ensemble");
  const [variable, setVariable] = useState("rainfall");

  const { mutate, data: result, isPending } = useMutation({
    mutationFn: () =>
      forecastApi.pointForecast({ latitude: lat, longitude: lon,
        horizon_days: horizon, model }).then((r) => r.data),
    onError: (e) => toast.error(e.message),
  });

  const forecasts = result?.forecasts || [];
  const avgConf   = forecasts.length
    ? (forecasts.reduce((a, f) => a + f.confidence, 0) / forecasts.length * 100).toFixed(1)
    : null;

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <Topbar title="AI Forecasting Engine" />
      <div className="flex-1 overflow-y-auto p-6 space-y-6">

        {/* Controls */}
        <Card>
          <SectionHeader title="Forecast Configuration"
            subtitle="Hybrid XGBoost + LSTM ensemble with confidence scoring" />
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 items-end">
            <div>
              <label className="text-xs text-slate-400">Latitude</label>
              <input type="number" value={lat} step="0.25"
                onChange={(e) => setLat(parseFloat(e.target.value))}
                className="input text-sm" />
            </div>
            <div>
              <label className="text-xs text-slate-400">Longitude</label>
              <input type="number" value={lon} step="0.25"
                onChange={(e) => setLon(parseFloat(e.target.value))}
                className="input text-sm" />
            </div>
            <div>
              <label className="text-xs text-slate-400">Horizon (days)</label>
              <input type="number" value={horizon} min={1} max={90}
                onChange={(e) => setHorizon(parseInt(e.target.value))}
                className="input text-sm" />
            </div>
            <div>
              <label className="text-xs text-slate-400">Model</label>
              <select value={model} onChange={(e) => setModel(e.target.value)} className="input text-sm">
                {MODEL_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
            <button
              onClick={() => mutate()}
              disabled={isPending}
              className="btn-primary flex items-center gap-2 justify-center"
            >
              {isPending ? <><Spinner size="sm" /> Running...</> : "▶ Run Forecast"}
            </button>
          </div>
        </Card>

        {result && (
          <>
            {/* Summary stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard label="Model" value={result.model} icon="🤖" />
              <StatCard label="Horizon" value={horizon} unit="days" icon="📅" />
              <StatCard label="Avg Confidence" value={avgConf} unit="%" icon="🎯" color="safe" />
              <StatCard label="Location"
                value={`${lat.toFixed(2)}°N, ${lon.toFixed(2)}°E`} icon="📍" />
            </div>

            {/* Variable tabs */}
            <Card>
              <SectionHeader title="Forecast Output" />
              <div className="flex gap-2 mb-4">
                {["rainfall", "max_temp", "min_temp"].map((v) => (
                  <button key={v}
                    onClick={() => setVariable(v)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                      variable === v ? "bg-brand-700 text-white" : "btn-secondary"
                    }`}
                  >
                    {v === "rainfall" ? "🌧️ Rainfall"
                      : v === "max_temp" ? "🌡️ Max Temp" : "❄️ Min Temp"}
                  </button>
                ))}
              </div>
              <ForecastChart data={forecasts} variable={variable} height={280} />
            </Card>

            {/* Forecast table */}
            <Card>
              <SectionHeader title="Forecast Table" subtitle="First 14 days" />
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-slate-300">
                  <thead>
                    <tr className="border-b border-surface-border">
                      <th className="text-left py-2 text-slate-500">Date</th>
                      <th className="text-right py-2 text-blue-400">Rainfall (mm)</th>
                      <th className="text-right py-2 text-red-400">Max Temp (°C)</th>
                      <th className="text-right py-2 text-cyan-400">Min Temp (°C)</th>
                      <th className="text-right py-2 text-green-400">Confidence</th>
                    </tr>
                  </thead>
                  <tbody>
                    {forecasts.slice(0, 14).map((f, i) => (
                      <tr key={i} className="border-b border-surface-border/50 hover:bg-surface-card/50">
                        <td className="py-1.5 font-mono">{f.target_date}</td>
                        <td className="text-right font-mono">{f.rainfall_pred?.toFixed(2)}</td>
                        <td className="text-right font-mono">{f.max_temp_pred?.toFixed(2)}</td>
                        <td className="text-right font-mono">{f.min_temp_pred?.toFixed(2)}</td>
                        <td className="text-right">
                          <Badge variant={f.confidence > 0.6 ? "success" : f.confidence > 0.4 ? "warning" : "danger"}>
                            {(f.confidence * 100).toFixed(0)}%
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}
