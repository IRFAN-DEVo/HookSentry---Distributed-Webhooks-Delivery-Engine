import { create } from 'zustand';

const WORKSPACE_KEY = 'hooksentry_active_workspace';

export const useWorkspaceStore = create((set) => ({
  activeWorkspace: (() => {
    try {
      const saved = localStorage.getItem(WORKSPACE_KEY);
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  })(),
  workspaces: [],

  setActiveWorkspace: (workspace) => {
    if (workspace) {
      localStorage.setItem(WORKSPACE_KEY, JSON.stringify(workspace));
    } else {
      localStorage.removeItem(WORKSPACE_KEY);
    }
    set({ activeWorkspace: workspace });
  },

  setWorkspaces: (workspaces) => {
    set((state) => {
      let active = state.activeWorkspace;
      // If no active workspace or active workspace is not in the list, default to first
      if (!active || !workspaces.some((w) => w.id === active.id)) {
        active = workspaces.length > 0 ? workspaces[0] : null;
        if (active) {
          localStorage.setItem(WORKSPACE_KEY, JSON.stringify(active));
        } else {
          localStorage.removeItem(WORKSPACE_KEY);
        }
      }
      return { workspaces, activeWorkspace: active };
    });
  },
}));

