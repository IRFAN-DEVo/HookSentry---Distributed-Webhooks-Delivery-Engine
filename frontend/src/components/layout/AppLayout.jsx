import React, { useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopNavbar from './TopNavbar';
import DeliveryInspectorDrawer from '../inspector/DeliveryInspectorDrawer';
import { useQuery } from '@tanstack/react-query';
import { authApi } from '../../api/auth.api';
import { useWorkspaceStore } from '../../stores/workspace.store';

export default function AppLayout() {
  const { setWorkspaces } = useWorkspaceStore();

  // Sync workspace memberships on mount
  const { data: meData } = useQuery({
    queryKey: ['me'],
    queryFn: authApi.getMe,
    staleTime: 60000,
  });

  useEffect(() => {
    if (meData?.workspaces) {
      setWorkspaces(meData.workspaces);
    }
  }, [meData, setWorkspaces]);

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <TopNavbar />
        <main className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>

      {/* Slide-over Delivery Inspector Drawer */}
      <DeliveryInspectorDrawer />
    </div>
  );
}

