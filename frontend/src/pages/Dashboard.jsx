import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { climateApi, datasetsApi, analyticsApi } from "@/api/client";
import useStore from "@/store/useStore";
import Topbar from "@/components/ui/Topbar";
import { Card, StatCard, Badge, Spinner, SectionHeader } from "@/components/ui";
import { MonthlyBarChart, TimeseriesChart } from "@/components/charts/ClimateCharts";

export default function Dashboard() {
  const { selectedDate } = useStore();

  const { data: summary, isLoading: loadingSum } = useQuery({
    queryKey: ["national-summary", selectedDate],
    queryFn: () => climateApi.getNationalSummary(selectedDate).then((r) => r.data),
  });

  const { data: meta } = useQuery({
    queryKey: ["dataset-meta"],
    queryFn: () => datasetsApi.getMeta().then((r) => r.data),
    staleTime: Infinity,
  });

  const { data: quality } = useQuery({
    queryKey: ["dataset-quality"],
    queryFn: () => datasetsApi.getQuality().then((r) => r.data),
    staleTime: Infinity,
  });

  const { data: indicators } = useQuery({
    queryKey: ["indicators"],
    queryFn: () => analyticsApi.indicators("2025-01-01", "2025-12-31").then((r) => r.data?.result),
    staleTime: 10 * 60 * 1000,
  });

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <Topbar title="Dashboard — IndiCli" />
      <div className="flex-1 overflow-y-auto p-6 space-y-6">

        {/* Hero stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard
            label="Avg Rainfall"
            value={summary?.rainfall?.mean?.toFixed(1) ?? "\u2014"}
            unit="mm/day" icon={"\u{1F327}"} color="rain"
          />
          <StatCard
            label="Avg Max Temp"
            value={summary?.max_temp?.mean?.toFixed(1) ?? "\u2014"}
            unit="°C" icon={"\u{1F321}"} color="heat"
          />
          <StatCard
            label="Avg Min Temp"
            value={summary?.min_temp?.mean?.toFixed(1) ?? "\u2014"}
            unit="°C" icon={"\u{2744}"} color="cold"
          />
          <StatCard
            label="Peak Rainfall"
            value={summary?.rainfall?.max?.toFixed(1) ?? "\u2014"}
            unit="mm" icon={"\u{26C8}"} color="rain"
          />
        </div>

        {/* Climate Indicators */}
        {indicators && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Annual Rainfall"   value={indicators.annual_rainfall_mm}    unit="mm"  icon={"\u{1F308}"} />
            <StatCard label="Monsoon Rainfall"  value={indicators.monsoon_rainfall_mm}   unit="mm"  icon={"\u{2614}"} color="rain" />
            <StatCard label="Days Above 40°C"   value={indicators.days_above_40c}        unit="days" icon={"\u{1F525}"} color="heat" />
            <StatCard label="Max Dry Streak"    value={indicators.consecutive_dry_days}  unit="days" icon={"\u{1F3DC}"} color="drought" />
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Monthly climate chart */}
          <Card>
            <SectionHeader title="Monthly Climate Averages" subtitle="Rainfall and temperature by month" />
            {summary?.monthly_avg
              ? <MonthlyBarChart data={summary.monthly_avg} height={220} />
              : <div className="flex justify-center py-8"><Spinner /></div>
            }
          </Card>

          {/* Dataset quality */}
          <Card>
            <SectionHeader title="Dataset Health" subtitle="IMD India 2025 data quality" />
            {quality ? (
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Total Records</span>
                  <span className="font-mono text-slate-200">
                    {quality.total_rows?.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Completeness</span>
                  <span className="font-mono text-green-400">
                    {quality.completeness_pct}%
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Missing Rainfall</span>
                  <span className="font-mono text-amber-400">
                    {quality.missing_rainfall?.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Missing MaxTemp</span>
                  <span className="font-mono text-amber-400">
                    {quality.missing_max_temp?.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Outliers Detected</span>
                  <span className="font-mono text-red-400">
                    {quality.outlier_count?.toLocaleString()}
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-2">
                  <Badge variant={quality.completeness_pct > 85 ? "success" : "warning"}>
                    {quality.completeness_pct > 85 ? "Good Quality" : "Check Missing Data"}
                  </Badge>
                </div>
              </div>
            ) : <Spinner />}
          </Card>
        </div>

        {/* Dataset meta */}
        {meta && (
          <Card>
            <SectionHeader title="Active Dataset" />
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
              {[
                ["Name", meta.name],
                ["Date Range", `${meta.date_start} → ${meta.date_end}`],
                ["Lat Range", `${meta.lat_min}° — ${meta.lat_max}°N`],
                ["Lon Range", `${meta.lon_min}° — ${meta.lon_max}°E`],
                ["Grid Points / Day", `${(meta.unique_lats * meta.unique_lons)?.toLocaleString()}`],
              ].map(([k, v]) => (
                <div key={k}>
                  <p className="text-slate-500 text-xs">{k}</p>
                  <p className="text-slate-200 font-medium truncate">{v}</p>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}

