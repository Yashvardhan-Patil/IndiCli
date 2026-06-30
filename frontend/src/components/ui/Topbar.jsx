import useStore from "@/store/useStore";
import { Select } from "@/components/ui";

const VARIABLES = [
  { value: "rainfall", label: "🌧️ Rainfall" },
  { value: "max_temp", label: "🌡️ Max Temp" },
  { value: "min_temp", label: "❄️ Min Temp" },
];

const LAYERS = [
  { value: "current",  label: "Current" },
  { value: "forecast", label: "Forecast" },
  { value: "scenario", label: "Scenario" },
];

export default function Topbar({ title }) {
  const {
    selectedDate, setSelectedDate,
    selectedVariable, setSelectedVariable,
    selectedLayer, setSelectedLayer,
  } = useStore();

  return (
    <header className="flex items-center justify-between px-6 py-3 border-b border-surface-border bg-surface-card shrink-0">
      <h1 className="text-base font-semibold text-slate-100">{title}</h1>

      <div className="flex items-center gap-3">
        <div className="flex flex-col gap-0.5">
          <label className="text-xs text-slate-500">Date</label>
          <input
            type="date"
            value={selectedDate}
            min="2025-01-01"
            max="2025-12-31"
            onChange={(e) => setSelectedDate(e.target.value)}
            className="input text-xs py-1 px-2 w-36"
          />
        </div>

        <Select
          label="Variable"
          value={selectedVariable}
          onChange={setSelectedVariable}
          options={VARIABLES}
          className="w-36"
        />

        <Select
          label="Layer"
          value={selectedLayer}
          onChange={setSelectedLayer}
          options={LAYERS}
          className="w-32"
        />
      </div>
    </header>
  );
}
