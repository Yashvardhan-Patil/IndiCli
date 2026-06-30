import { useEffect, Suspense, lazy } from "react";
import { useQuery } from "@tanstack/react-query";
import { climateApi } from "@/api/client";
import useStore from "@/store/useStore";
import Topbar from "@/components/ui/Topbar";
import { Card, StatCard, Spinner, Select } from "@/components/ui";
import { TimeseriesChart } from "@/components/charts/ClimateCharts";

const CesiumGlobe = lazy(() => import("@/components/map/CesiumGlobe"));

export default function ClimateTwin() {
  const {
    selectedDate, selectedVariable,
    selectedLat, selectedLon, setSelectedLocation,
  } = useStore();

  const { data: gridData, isLoading } = useQuery({
    queryKey: ["climate-state", selectedDate, selectedVariable],
    queryFn: () =>
      climateApi.getCurrent(selectedDate, selectedVariable)
        .then((r) => r.data?.grid_points || []),
    staleTime: 5 * 60 * 1000,
  });

  const { data: timeseries } = useQuery({
    queryKey: ["timeseries", selectedLat, selectedLon],
    queryFn: () =>
      climateApi.getTimeseries(selectedLat, selectedLon, "2025-01-01", "2025-12-31")
        .then((r) => r.data),
    enabled: !!selectedLat,
  });

  const { data: summary } = useQuery({
    queryKey: ["climate-stats", selectedDate, selectedVariable],
    queryFn: () =>
      climateApi.getCurrent(selectedDate, selectedVariable)
        .then((r) => r.data?.stats || {}),
  });

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <Topbar title="Climate Digital Twin — India 3D Globe" />
      <div className="flex flex-1 overflow-hidden gap-4 p-4">

        {/* Globe */}
        <div className="flex-1 relative rounded-xl overflow-hidden border border-surface-border">
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-surface/70 z-10">
              <Spinner size="lg" />
            </div>
          )}
          <Suspense fallback={
            <div className="w-full h-full flex items-center justify-center">
              <Spinner size="lg" />
            </div>
          }>
            <CesiumGlobe gridData={gridData} />
          </Suspense>
        </div>

        {/* Right panel */}
        <div className="w-72 flex flex-col gap-4 overflow-y-auto">
          {/* Stats */}
          <Card>
            <p className="text-xs text-slate-500 font-medium uppercase mb-3">
              {selectedVariable} — {selectedDate}
            </p>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <p className="text-xs text-slate-500">Mean</p>
                <p className="text-lg font-bold text-brand-400">
                  {summary?.mean?.toFixed(2) ?? "—"}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Max</p>
                <p className="text-lg font-bold text-climate-heat">
                  {summary?.max?.toFixed(2) ?? "—"}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Min</p>
                <p className="text-lg font-bold text-climate-cold">
                  {summary?.min?.toFixed(2) ?? "—"}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500">P90</p>
                <p className="text-lg font-bold text-amber-400">
                  {summary?.p90?.toFixed(2) ?? "—"}
                </p>
              </div>
            </div>
          </Card>

          {/* Selected location */}
          <Card>
            <p className="text-xs text-slate-500 font-medium uppercase mb-2">
              Selected Location
            </p>
            <p className="text-sm text-slate-300 font-mono">
              {selectedLat?.toFixed(3)}°N, {selectedLon?.toFixed(3)}°E
            </p>
            <p className="text-xs text-slate-500 mt-1">
              Click globe to select location
            </p>
          </Card>

          {/* Timeseries for selected location */}
          <Card className="flex-1">
            <p className="text-xs text-slate-500 font-medium uppercase mb-2">
              Location Timeseries
            </p>
            {timeseries ? (
              <TimeseriesChart
                data={timeseries}
                variables={["rainfall", "max_temp", "min_temp"]}
                height={300}
              />
            ) : (
              <div className="flex justify-center py-8"><Spinner /></div>
            )}
          </Card>

          {/* Color legend */}
          <Card>
            <p className="text-xs text-slate-500 font-medium uppercase mb-2">
              Color Scale
            </p>
            {selectedVariable === "rainfall" && (
              <div className="space-y-1 text-xs">
                {[
                  ["No rain", "#f0f0f0"], ["0–5 mm", "#add8e6"],
                  ["5–20 mm", "#6495ed"], ["20–50 mm", "#0000ff"],
                  ["50–100 mm", "#0000b4"], [">100 mm", "#4b0082"],
                ].map(([label, color]) => (
                  <div key={label} className="flex items-center gap-2">
                    <div className="w-4 h-3 rounded" style={{ background: color }} />
                    <span className="text-slate-400">{label}</span>
                  </div>
                ))}
              </div>
            )}
            {selectedVariable === "max_temp" && (
              <div className="space-y-1 text-xs">
                {[
                  ["< 20°C", "#87cefa"], ["20–30°C", "#90ee90"],
                  ["30–35°C", "#ffff00"], ["35–40°C", "#ffa500"], ["> 40°C", "#dc1414"],
                ].map(([label, color]) => (
                  <div key={label} className="flex items-center gap-2">
                    <div className="w-4 h-3 rounded" style={{ background: color }} />
                    <span className="text-slate-400">{label}</span>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
