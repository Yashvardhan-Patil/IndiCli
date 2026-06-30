import { NavLink } from "react-router-dom";
import clsx from "clsx";
import useStore from "@/store/useStore";

const NAV = [
  { to: "/",            icon: "🏠", label: "Dashboard"     },
  { to: "/twin",        icon: "🌏", label: "Climate Twin"  },
  { to: "/forecasting", icon: "📈", label: "Forecasting"   },
  { to: "/simulation",  icon: "🔬", label: "Simulation"    },
  { to: "/analytics",   icon: "📊", label: "Analytics"     },
  { to: "/settings",    icon: "⚙️", label: "Settings"      },
];

export default function Sidebar() {
  const { sidebarOpen, toggleSidebar } = useStore();

  return (
    <aside
      className={clsx(
        "flex flex-col bg-surface-card border-r border-surface-border transition-all duration-200 shrink-0",
        sidebarOpen ? "w-56" : "w-16"
      )}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-surface-border">
        <span className="text-2xl shrink-0">🌦️</span>
        {sidebarOpen && (
          <div className="min-w-0">
            <p className="font-bold text-brand-400 text-sm leading-tight truncate">
              IndiCli
            </p>
            <p className="text-xs text-slate-500 truncate">Climate Intelligence</p>
          </div>
        )}
      </div>

      {/* Nav links */}
      <nav className="flex-1 py-4 flex flex-col gap-1 px-2">
        {NAV.map(({ to, icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-brand-700 text-white"
                  : "text-slate-400 hover:bg-surface-border hover:text-slate-200"
              )
            }
          >
            <span className="text-base shrink-0">{icon}</span>
            {sidebarOpen && <span className="truncate">{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Toggle button */}
      <button
        onClick={toggleSidebar}
        className="mx-2 mb-4 p-2 rounded-lg text-slate-500 hover:text-slate-200
                   hover:bg-surface-border transition-colors text-xs"
      >
        {sidebarOpen ? "◀ Collapse" : "▶"}
      </button>
    </aside>
  );
}
