import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { scenarioApi } from "@/api/client";
import Topbar from "@/components/ui/Topbar";
import { Card, StatCard, Spinner, Badge, SectionHeader, EmptyState } from "@/components/ui";
import toast from "react-hot-toast";

const SCENARIO_ICONS = {
  temp_plus_1c:    { icon: "🌡️", color: "text-orange-400",  label: "+1°C Temperature"     },
  temp_plus_2c:    { icon: "🔥", color: "text-red-400",     label: "+2°C Temperature"     },
  rain_plus_20pct: { icon: "🌧️", color: "text-blue-400",   label: "+20% Rainfall"        },
  rain_minus_20pct:{ icon: "🏜️", color: "text-amber-400",  label: "-20% Rainfall"        },
  drought:         { icon: "💀", color: "text-red-500",     label: "Severe Drought"       },
  heatwave:        { icon: "☀️", color: "text-orange-500",  label: "Heatwave Event"       },
  extreme_rainfall:{ icon: "⛈️", color: "text-indigo-400", label: "Extreme Rainfall"     },
};

export default function Simulation() {
  const [selected, setSelected]   = useState("temp_plus_1c");
  const [baseDate, setBaseDate]   = useState("2025-06-01");
  const [duration, setDuration]   = useState(30);

  const { data: scenarioTypes } = useQuery({
    queryKey: ["scenario-types"],
    queryFn: () => scenarioApi.getTypes().then((r) => r.data?.scenarios || []),
    staleTime: Infinity,
  });

  const { mutate, data: result, isPending, reset } = useMutation({
    mutationFn: () =>
      scenarioApi.runScenario({
        scenario_type: selected,
        base_date:     baseDate,
        duration_days: duration,
      }).then((r) => r.data),
    onError: (e) => toast.error(e.message),
  });

  const summary = result?.summary_stats;

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <Topbar title="What-If Simulation Engine" />
      <div className="flex-1 overflow-y-auto p-6 space-y-6">

        {/* Scenario selector */}
        <Card>
          <SectionHeader title="Select Scenario"
            subtitle="Apply physical perturbations to the baseline climate state" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            {Object.entries(SCENARIO_ICONS).map(([id, { icon, color, label }]) => (
              <button
                key={id}
                onClick={() => { setSelected(id); reset(); }}
                className={`p-3 rounded-xl border text-left transition-all ${
                  selected === id
                    ? "border-brand-500 bg-brand-900/30"
                    : "border-surface-border bg-surface hover:border-surface-muted"
                }`}
              >
                <span className="text-2xl">{icon}</span>
                <p className={`text-xs font-medium mt-1 ${color}`}>{label}</p>
              </button>
            ))}
          </div>

          <div className="flex flex-wrap gap-4 items-end">
            <div>
              <label className="text-xs text-slate-400">Base Date</label>
              <input type="date" value={baseDate}
                min="2025-01-01" max="2025-12-31"
                onChange={(e) => setBaseDate(e.target.value)}
                className="input text-sm w-40" />
            </div>
            <div>
              <label className="text-xs text-slate-400">Duration (days)</label>
              <input type="number" value={duration} min={1} max={365}
                onChange={(e) => setDuration(parseInt(e.target.value))}
                className="input text-sm w-32" />
            </div>
            <button onClick={() => mutate()} disabled={isPending}
              className="btn-primary flex items-center gap-2">
              {isPending ? <><Spinner size="sm" /> Running Simulation...</> : "⚡ Run Simulation"}
            </button>
          </div>

          {selected && (
            <p className="text-xs text-slate-500 mt-3 italic">
              {scenarioTypes?.find((s) => s.id === selected)?.description}
            </p>
          )}
        </Card>

        {result && (
          <>
            {/* Scenario summary */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {["rainfall", "max_temp", "min_temp"].map((v) => {
                const s = summary?.[v];
                if (!s) return null;
                return (
                  <Card key={v}>
                    <p className="text-xs text-slate-500 uppercase font-medium mb-2">
                      {v === "rainfall" ? "🌧️ Rainfall" : v === "max_temp" ? "🌡️ Max Temp" : "❄️ Min Temp"}
                    </p>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <p className="text-xs text-slate-500">Baseline Mean</p>
                        <p className="font-mono text-slate-200">{s.baseline_mean}</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-500">Scenario Mean</p>
                        <p className="font-mono text-slate-200">{s.scenario_mean}</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-500">Absolute Change</p>
                        <p className={`font-mono font-bold ${s.absolute_change > 0 ? "text-red-400" : "text-green-400"}`}>
                          {s.absolute_change > 0 ? "+" : ""}{s.absolute_change}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-500">% Change</p>
                        <p className={`font-mono font-bold ${s.pct_change > 0 ? "text-red-400" : "text-green-400"}`}>
                          {s.pct_change > 0 ? "+" : ""}{s.pct_change}%
                        </p>
                      </div>
                    </div>
                  </Card>
                );
              })}
            </div>

            {/* Scenario info */}
            <Card>
              <div className="flex items-center gap-3 mb-4">
                <span className="text-3xl">{SCENARIO_ICONS[result.scenario_type]?.icon}</span>
                <div>
                  <p className="font-semibold text-slate-100">{result.description}</p>
                  <p className="text-xs text-slate-500">
                    ID: <span className="font-mono">{result.scenario_id}</span> •
                    Base: {result.base_date} •
                    Duration: {result.duration_days} days •
                    Grid points: {result.grid_points?.length?.toLocaleString()}
                  </p>
                </div>
              </div>

              {/* Grid sample table */}
              <SectionHeader title="Sample Grid Points" subtitle="First 20 perturbed grid points" />
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-slate-300">
                  <thead>
                    <tr className="border-b border-surface-border">
                      {["Lat","Lon","Rainfall","Max Temp","Min Temp","Δ Rain","Δ Tmax","Δ Tmin"].map((h) => (
                        <th key={h} className="text-right py-1.5 text-slate-500 first:text-left">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {result.grid_points?.slice(0, 20).map((pt, i) => (
                      <tr key={i} className="border-b border-surface-border/40">
                        <td className="py-1 font-mono text-left">{pt.latitude?.toFixed(2)}</td>
                        <td className="py-1 font-mono text-right">{pt.longitude?.toFixed(2)}</td>
                        <td className="py-1 font-mono text-right">{pt.rainfall?.toFixed(2)}</td>
                        <td className="py-1 font-mono text-right">{pt.max_temp?.toFixed(2)}</td>
                        <td className="py-1 font-mono text-right">{pt.min_temp?.toFixed(2)}</td>
                        <td className={`py-1 font-mono text-right ${(pt.delta_rainfall||0) > 0 ? "text-blue-400" : "text-amber-400"}`}>
                          {pt.delta_rainfall?.toFixed(2)}
                        </td>
                        <td className={`py-1 font-mono text-right ${(pt.delta_max_temp||0) > 0 ? "text-red-400" : "text-cyan-400"}`}>
                          {pt.delta_max_temp?.toFixed(2)}
                        </td>
                        <td className={`py-1 font-mono text-right ${(pt.delta_min_temp||0) > 0 ? "text-red-400" : "text-cyan-400"}`}>
                          {pt.delta_min_temp?.toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </>
        )}

        {!result && !isPending && (
          <EmptyState icon="🔬" message="Select a scenario and click Run Simulation" />
        )}
      </div>
    </div>
  );
}
