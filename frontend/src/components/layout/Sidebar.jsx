import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Radio,
  Send,
  Layers,
  AlertOctagon,
  BarChart3,
  Settings,
  ShieldCheck,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { useUIStore } from '../../stores/ui.store';

const NAV_ITEMS = [
  { to: '/', label: 'Overview', icon: LayoutDashboard },
  { to: '/endpoints', label: 'Endpoints', icon: Radio },
  { to: '/events', label: 'Event Explorer', icon: Send },
  { to: '/deliveries', label: 'Delivery Logs', icon: Layers },
  { to: '/dead-letters', label: 'Dead-Letter Queue', icon: AlertOctagon },
  { to: '/analytics', label: 'Analytics', icon: BarChart3 },
  { to: '/settings', label: 'Settings', icon: Settings },
];

export default function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useUIStore();

  return (
    <aside
      className={`h-screen sticky top-0 bg-slate-900/80 backdrop-blur-md border-r border-slate-800 transition-all duration-300 flex flex-col justify-between z-30 ${
        sidebarCollapsed ? 'w-20' : 'w-64'
      }`}
    >
      <div>
        {/* Brand Logo */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-slate-800">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/20 shrink-0">
              <ShieldCheck className="w-5 h-5 text-white" />
            </div>
            {!sidebarCollapsed && (
              <div>
                <span className="font-extrabold text-base tracking-tight text-white block">
                  HookSentry
                </span>
                <span className="text-[10px] uppercase font-mono font-semibold tracking-wider text-indigo-400 block -mt-1">
                  Delivery Engine
                </span>
              </div>
            )}
          </div>
          <button
            onClick={toggleSidebar}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            {sidebarCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="p-3 space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                  } ${sidebarCollapsed ? 'justify-center' : ''}`
                }
                title={sidebarCollapsed ? item.label : undefined}
              >
                <Icon className="w-5 h-5 shrink-0" />
                {!sidebarCollapsed && <span>{item.label}</span>}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Footer Info */}
      {!sidebarCollapsed && (
        <div className="p-4 border-t border-slate-800 text-xs text-slate-400 font-mono">
          <div className="flex items-center justify-between">
            <span>At-Least-Once</span>
            <span className="px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px]">
              Active
            </span>
          </div>
          <div className="text-[10px] text-slate-400 mt-1">v1.0.0 • HMAC-SHA256</div>
        </div>
      )}
    </aside>
  );
}
