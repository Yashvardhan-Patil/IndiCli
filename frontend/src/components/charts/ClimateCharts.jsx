import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine,
} from "recharts";

const COLORS = {
  rainfall: "#3b82f6",
  max_temp: "#ef4444",
  min_temp: "#06b6d4",
  forecast: "#a78bfa",
  anomaly:  "#f59e0b",
  trend:    "#22c55e",
};

const tooltipStyle = {
  contentStyle: { background: "#1e293b", border: "1px solid #334155",
                  borderRadius: "8px", color: "#f1f5f9" },
  itemStyle:    { color: "#cbd5e1" },
};

// ── TimeseriesChart ────────────────────────────────────────────────────────────
export function TimeseriesChart({ data, variables = ["rainfall"], height = 240 }) {
  if (!data?.length) return <p className="text-slate-500 text-sm text-center py-8">No data</p>;

  const chartData = data.dates?.map((d, i) => {
    const row = { date: d.slice(5) };
    variables.forEach((v) => { row[v] = data[v]?.[i] ?? null; });
    return row;
  }) ?? data;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={chartData} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
        <defs>
          {variables.map((v) => (
            <linearGradient key={v} id={`grad_${v}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor={COLORS[v] || "#6366f1"} stopOpacity={0.3} />
              <stop offset="95%" stopColor={COLORS[v] || "#6366f1"} stopOpacity={0}   />
            </linearGradient>
          ))}
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#94a3b8" }} interval="preserveStartEnd" />
        <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} />
        <Tooltip {...tooltipStyle} />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        {variables.map((v) => (
          <Area key={v} type="monotone" dataKey={v} dot={false}
            stroke={COLORS[v] || "#6366f1"} fill={`url(#grad_${v})`}
            strokeWidth={1.5} connectNulls />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  );
}

// ── ForecastChart ──────────────────────────────────────────────────────────────
export function ForecastChart({ data, variable = "rainfall", height = 240 }) {
  if (!data?.length) return <p className="text-slate-500 text-sm text-center py-8">No forecast data</p>;

  const predKey = `${variable}_pred`;
  const chartData = data.map((r) => ({
    date:       String(r.target_date).slice(5),
    value:      r[predKey],
    confidence: r.confidence ? Math.round(r.confidence * 100) : null,
  }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={chartData} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#94a3b8" }} interval={4} />
        <YAxis yAxisId="left"  tick={{ fontSize: 10, fill: "#94a3b8" }} />
        <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 10, fill: "#94a3b8" }}
               domain={[0, 100]} />
        <Tooltip {...tooltipStyle} />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        <Line yAxisId="left" type="monotone" dataKey="value" name={variable}
          stroke={COLORS[variable] || "#6366f1"} dot={false} strokeWidth={2} />
        <Line yAxisId="right" type="monotone" dataKey="confidence" name="Confidence (%)"
          stroke="#22c55e" dot={false} strokeWidth={1} strokeDasharray="4 2" />
      </LineChart>
    </ResponsiveContainer>
  );
}

// ── AnomalyChart ───────────────────────────────────────────────────────────────
export function AnomalyChart({ result, height = 240 }) {
  if (!result?.dates?.length) return null;
  const chartData = result.dates.map((d, i) => ({
    date:    d.slice(5),
    value:   result.values?.[i],
    z_score: result.anomaly_scores?.[i],
    anomaly: result.anomaly_flags?.[i],
  }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={chartData} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#94a3b8" }} interval="preserveStartEnd" />
        <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} />
        <Tooltip {...tooltipStyle} />
        <ReferenceLine y={result.threshold}  stroke="#f59e0b" strokeDasharray="4 2" label={{ value: "+σ", fill: "#f59e0b", fontSize: 10 }} />
        <ReferenceLine y={-result.threshold} stroke="#f59e0b" strokeDasharray="4 2" label={{ value: "-σ", fill: "#f59e0b", fontSize: 10 }} />
        <Line type="monotone" dataKey="z_score" name="Z-score" stroke="#f59e0b"
          dot={false} strokeWidth={1.5} />
      </LineChart>
    </ResponsiveContainer>
  );
}

// ── MonthlyBarChart ────────────────────────────────────────────────────────────
export function MonthlyBarChart({ data, height = 200 }) {
  if (!data) return null;
  const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  const chartData = Object.entries(data).map(([m, v]) => ({
    month: MONTHS[parseInt(m) - 1],
    rainfall: v?.rainfall ? parseFloat(v.rainfall.toFixed(1)) : 0,
    max_temp: v?.max_temp  ? parseFloat(v.max_temp.toFixed(1))  : 0,
  }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={chartData} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="month" tick={{ fontSize: 10, fill: "#94a3b8" }} />
        <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} />
        <Tooltip {...tooltipStyle} />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        <Bar dataKey="rainfall" name="Rainfall (mm)" fill="#3b82f6" radius={[3,3,0,0]} />
        <Bar dataKey="max_temp" name="Max Temp (°C)"  fill="#ef4444" radius={[3,3,0,0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
