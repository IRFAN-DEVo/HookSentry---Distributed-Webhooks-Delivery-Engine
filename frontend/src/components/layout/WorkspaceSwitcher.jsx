import React, { useState } from 'react';
import { useWorkspaceStore } from '../../stores/workspace.store';
import { Building2, ChevronDown, Check, Plus } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function WorkspaceSwitcher() {
  const { activeWorkspace, workspaces, setActiveWorkspace } = useWorkspaceStore();
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-sm font-medium text-slate-200 transition-all hover:bg-slate-850"
      >
        <Building2 className="w-4 h-4 text-indigo-400" />
        <span className="max-w-[140px] truncate">{activeWorkspace?.name || 'Select Workspace'}</span>
        <ChevronDown className="w-3.5 h-3.5 text-slate-400 ml-1" />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute left-0 mt-1.5 w-60 rounded-xl bg-slate-900 border border-slate-800 shadow-2xl py-1.5 z-50 animate-fadeIn">
            <div className="px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-slate-400">
              Workspaces
            </div>
            <div className="max-h-56 overflow-y-auto py-1">
              {workspaces.map((ws) => (
                <button
                  key={ws.id}
                  onClick={() => {
                    setActiveWorkspace(ws);
                    setOpen(false);
                  }}
                  className={`w-full flex items-center justify-between px-3 py-2 text-sm text-left transition-colors ${
                    activeWorkspace?.id === ws.id
                      ? 'bg-indigo-600/10 text-indigo-400 font-medium'
                      : 'text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  <span className="truncate">{ws.name}</span>
                  {activeWorkspace?.id === ws.id && <Check className="w-4 h-4 text-indigo-400" />}
                </button>
              ))}
            </div>
            <div className="border-t border-slate-800 mt-1 pt-1">
              <button
                onClick={() => {
                  setOpen(false);
                  navigate('/settings');
                }}
                className="w-full flex items-center gap-2 px-3 py-2 text-xs font-medium text-indigo-400 hover:bg-slate-800 transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                Manage Workspaces
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

