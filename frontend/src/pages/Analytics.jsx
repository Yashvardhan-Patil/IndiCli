import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/api/client";
import Topbar from "@/components/ui/Topbar";
import { Card, Spinner, Badge, SectionHeader, EmptyState } from "@/components/ui";
import { TimeseriesChart, AnomalyChart } from "@/components/charts/ClimateCharts";
import toast from "react-hot-toast";

const TABS = ["Trend", "Anomaly", "Risk", "Indicators"];

const RISK_COLOR = (v) =>
  v > 0.6 ? "text-red-400" : v > 0.3 ? "text-amber-400" : "text-green-400";

export default function Analytics() {
  const [tab, setTab]           = useState("Indicators");
  const [variable, setVariable] = useState("rainfall");
  const [start, setStart]       = useState("2025-01-01");
  const [end, setEnd]           = useState("2025-12-31");

  // Indicators (no form needed)
  const { data: indicators, isLoading: loadInd } = useQuery({
    queryKey: ["indicators", start, end],
    queryFn: () => analyticsApi.indicators(start, end).then((r) => r.data?.result),
    enabled: tab === "Indicators",
    staleTime: 5 * 60 * 1000,
  });

  const trendMut   = useMutation({ mutationFn: () => analyticsApi.trend({ analysis_type: "trend", variable, start_date: start, end_date: end }).then((r) => r.data?.result), onError: (e) => toast.error(e.message) });
  const anomMut    = useMutation({ mutationFn: () => analyticsApi.anomaly({ analysis_type: "anomaly", variable, start_date: start, end_date: end }).then((r) => r.data?.result), onError: (e) => toast.error(e.message) });
  const riskMut    = useMutation({ mutationFn: () => analyticsApi.risk({ analysis_type: "risk", variable, start_date: start, end_date: end }).then((r) => r.data?.result), onError: (e) => toast.error(e.message) });

  const payload = { variable, start_date: start, end_date: end };

  function run() {
    if (tab === "Trend")   trendMut.mutate();
    if (tab === "Anomaly") anomMut.mutate();
    if (tab === "Risk")    riskMut.mutate();
  }

  const isPending = trendMut.isPending || anomMut.isPending || riskMut.isPending;

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <Topbar title="Climate Analytics Engine" />
      <div className="flex-1 overflow-y-auto p-6 space-y-6">

        {/* Tabs */}
        <div className="flex gap-2">
          {TABS.map((t) => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                tab === t ? "bg-brand-700 text-white" : "btn-secondary"
              }`}>{t}</button>
          ))}
        </div>

        {/* Controls (not for Indicators) */}
        {tab !== "Indicators" && (
          <Card>
            <div className="flex flex-wrap gap-4 items-end">
              <div>
                <label className="text-xs text-slate-400">Variable</label>
                <select value={variable} onChange={(e) => setVariable(e.target.value)} className="input text-sm w-36">
                  <option value="rainfall">Rainfall</option>
                  <option value="max_temp">Max Temp</option>
                  <option value="min_temp">Min Temp</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-slate-400">Start Date</label>
                <input type="date" value={start} onChange={(e) => setStart(e.target.value)} className="input text-sm w-36" />
              </div>
              <div>
                <label className="text-xs text-slate-400">End Date</label>
                <input type="date" value={end} onChange={(e) => setEnd(e.target.value)} className="input text-sm w-36" />
              </div>
              <button onClick={run} disabled={isPending} className="btn-primary flex items-center gap-2">
                {isPending ? <><Spinner size="sm" /> Analyzing...</> : "▶ Run Analysis"}
              </button>
            </div>
          </Card>
        )}

        {/* ── Trend ─────────────────────────────────────────────────────────── */}
        {tab === "Trend" && (
          <Card>
            <SectionHeader title="Trend Analysis" subtitle="Linear trend with 30-day moving average" />
            {trendMut.data ? (
              <>
                <div className="flex gap-6 mb-4 text-sm">
                  <div><p className="text-slate-500 text-xs">Trend Slope</p>
                    <p className="font-mono text-brand-400">{trendMut.data.trend_slope}</p></div>
                  <div><p className="text-slate-500 text-xs">R²</p>
                    <p className="font-mono text-green-400">{trendMut.data.trend_r2}</p></div>
                  <div><p className="text-slate-500 text-xs">p-value</p>
                    <p className="font-mono text-amber-400">{trendMut.data.p_value}</p></div>
                </div>
                <TimeseriesChart
                  data={{ dates: trendMut.data.dates, [variable]: trendMut.data.values,
                          trend: trendMut.data.trend_line, moving_avg: trendMut.data.moving_avg_30d }}
                  variables={[variable, "moving_avg"]}
                  height={280}
                />
              </>
            ) : <EmptyState icon="📈" message="Configure and run analysis above" />}
          </Card>
        )}

        {/* ── Anomaly ────────────────────────────────────────────────────────── */}
        {tab === "Anomaly" && (
          <Card>
            <SectionHeader title="Anomaly Detection" subtitle="Z-score based anomaly flagging" />
            {anomMut.data ? (
              <>
                <div className="flex gap-6 mb-4 text-sm">
                  <div><p className="text-slate-500 text-xs">Anomalies Found</p>
                    <p className="font-mono text-red-400">{anomMut.data.anomaly_count}</p></div>
                  <div><p className="text-slate-500 text-xs">Threshold (σ)</p>
                    <p className="font-mono text-amber-400">{anomMut.data.threshold}</p></div>
                  <div><p className="text-slate-500 text-xs">Mean</p>
                    <p className="font-mono text-slate-200">{anomMut.data.mean}</p></div>
                  <div><p className="text-slate-500 text-xs">Std Dev</p>
                    <p className="font-mono text-slate-200">{anomMut.data.std}</p></div>
                </div>
                <AnomalyChart result={anomMut.data} height={280} />
              </>
            ) : <EmptyState icon="🔍" message="Configure and run anomaly detection above" />}
          </Card>
        )}

        {/* ── Risk ──────────────────────────────────────────────────────────── */}
        {tab === "Risk" && (
          <Card>
            <SectionHeader title="Climate Risk Assessment" />
            {riskMut.data ? (
              <div className="space-y-4">
                <div className="flex items-center gap-4">
                  <div className="text-center">
                    <p className="text-5xl font-bold" style={{ color: riskMut.data.composite_risk > 0.6 ? "#ef4444" : riskMut.data.composite_risk > 0.3 ? "#f59e0b" : "#22c55e" }}>
                      {(riskMut.data.composite_risk * 100).toFixed(0)}%
                    </p>
                    <p className="text-xs text-slate-500 mt-1">Composite Risk</p>
                  </div>
                  <Badge variant={riskMut.data.risk_level === "HIGH" ? "danger" : riskMut.data.risk_level === "MEDIUM" ? "warning" : "success"}
                    className="text-base px-3 py-1">
                    {riskMut.data.risk_level} RISK
                  </Badge>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                  {[
                    ["🏜️ Drought",    riskMut.data.drought_risk],
                    ["🌊 Flood",       riskMut.data.flood_risk],
                    ["🔥 Heatwave",    riskMut.data.heatwave_risk],
                    ["🥶 Cold Wave",   riskMut.data.cold_wave_risk],
                  ].map(([label, val]) => (
                    <div key={label} className="card text-center">
                      <p className="text-xs text-slate-500">{label}</p>
                      <p className={`text-xl font-bold mt-1 ${RISK_COLOR(val)}`}>
                        {(val * 100).toFixed(1)}%
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            ) : <EmptyState icon="⚠️" message="Run risk assessment above" />}
          </Card>
        )}

        {/* ── Indicators ────────────────────────────────────────────────────── */}
        {tab === "Indicators" && (
          <Card>
            <SectionHeader title="Climate Indicators" subtitle="Annual climate summary for India 2025" />
            {loadInd ? <div className="flex justify-center py-8"><Spinner /></div>
              : indicators ? (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {Object.entries(indicators).map(([k, v]) => (
                    <div key={k} className="card">
                      <p className="text-xs text-slate-500 capitalize">
                        {k.replace(/_/g, " ")}
                      </p>
                      <p className="text-lg font-bold font-mono text-brand-400 mt-0.5">
                        {typeof v === "number" ? v.toLocaleString() : v}
                      </p>
                    </div>
                  ))}
                </div>
              ) : <EmptyState icon="📊" />}
          </Card>
        )}
      </div>
    </div>
  );
}
