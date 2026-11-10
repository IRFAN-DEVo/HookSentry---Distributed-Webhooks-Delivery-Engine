import React from 'react';
import WorkspaceSwitcher from './WorkspaceSwitcher';
import { useAuthStore } from '../../stores/auth.store';
import { LogOut, BookOpen, ExternalLink, User } from 'lucide-react';

export default function TopNavbar() {
  const { user, logout } = useAuthStore();

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/40 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-20">
      <div className="flex items-center gap-4">
        <WorkspaceSwitcher />
      </div>

      <div className="flex items-center gap-4">
        {/* API Docs Link */}
        <a
          href="http://localhost:8000/api/docs/"
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-medium text-slate-300 hover:text-white bg-slate-800/80 hover:bg-slate-800 border border-slate-700/60 transition-colors"
        >
          <BookOpen className="w-3.5 h-3.5 text-indigo-400" />
          <span>API Docs (Swagger)</span>
          <ExternalLink className="w-3 h-3 text-slate-400" />
        </a>

        {/* User Info & Logout */}
        <div className="flex items-center gap-3 pl-3 border-l border-slate-800">
          <div className="flex items-center gap-2 text-sm text-slate-300">
            <div className="w-7 h-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-indigo-400">
              <User className="w-4 h-4" />
            </div>
            <span className="font-medium text-xs max-w-[120px] truncate">
              {user?.email || 'Developer'}
            </span>
          </div>

          <button
            onClick={logout}
            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
            title="Log out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}

