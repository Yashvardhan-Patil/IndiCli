import clsx from "clsx";

// ── Card ──────────────────────────────────────────────────────────────────────
export function Card({ children, className, ...props }) {
  return (
    <div className={clsx("card", className)} {...props}>
      {children}
    </div>
  );
}

// ── StatCard ──────────────────────────────────────────────────────────────────
export function StatCard({ label, value, unit, trend, icon, color = "brand" }) {
  const colorMap = {
    brand:   "text-brand-400",
    rain:    "text-climate-rain",
    heat:    "text-climate-heat",
    cold:    "text-climate-cold",
    drought: "text-climate-drought",
    safe:    "text-climate-safe",
  };
  return (
    <div className="stat-card">
      <div className="flex items-center justify-between">
        <span className="text-slate-400 text-xs font-medium uppercase tracking-wide">
          {label}
        </span>
        {icon && <span className={clsx("text-lg", colorMap[color])}>{icon}</span>}
      </div>
      <div className="flex items-end gap-1 mt-1">
        <span className={clsx("text-2xl font-bold", colorMap[color])}>
          {value ?? "—"}
        </span>
        {unit && <span className="text-slate-400 text-sm mb-0.5">{unit}</span>}
      </div>
      {trend !== undefined && (
        <span className={clsx("text-xs", trend >= 0 ? "text-red-400" : "text-green-400")}>
          {trend >= 0 ? "▲" : "▼"} {Math.abs(trend).toFixed(2)}
        </span>
      )}
    </div>
  );
}

// ── Badge ─────────────────────────────────────────────────────────────────────
const badgeVariants = {
  default: "bg-slate-700 text-slate-200",
  success: "bg-green-900 text-green-300",
  warning: "bg-amber-900 text-amber-300",
  danger:  "bg-red-900 text-red-300",
  info:    "bg-blue-900 text-blue-300",
};

export function Badge({ children, variant = "default", className }) {
  return (
    <span className={clsx("badge", badgeVariants[variant], className)}>
      {children}
    </span>
  );
}

// ── Spinner ───────────────────────────────────────────────────────────────────
export function Spinner({ size = "md" }) {
  const s = { sm: "h-4 w-4", md: "h-6 w-6", lg: "h-10 w-10" }[size];
  return (
    <div className={clsx("animate-spin rounded-full border-2 border-surface-border border-t-brand-400", s)} />
  );
}

// ── Select ────────────────────────────────────────────────────────────────────
export function Select({ label, value, onChange, options, className }) {
  return (
    <div className={clsx("flex flex-col gap-1", className)}>
      {label && <label className="text-xs text-slate-400 font-medium">{label}</label>}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="input text-sm"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </div>
  );
}

// ── SectionHeader ─────────────────────────────────────────────────────────────
export function SectionHeader({ title, subtitle, action }) {
  return (
    <div className="flex items-start justify-between mb-4">
      <div>
        <h2 className="text-lg font-semibold text-slate-100">{title}</h2>
        {subtitle && <p className="text-sm text-slate-400 mt-0.5">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}

// ── EmptyState ────────────────────────────────────────────────────────────────
export function EmptyState({ icon = "📭", message = "No data available" }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-slate-500">
      <span className="text-4xl mb-3">{icon}</span>
      <p className="text-sm">{message}</p>
    </div>
  );
}
