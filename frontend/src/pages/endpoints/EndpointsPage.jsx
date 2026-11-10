import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { endpointApi } from '../../api/endpoint.api';
import CreateEndpointModal from '../../components/endpoints/CreateEndpointModal';
import RotateSecretModal from '../../components/endpoints/RotateSecretModal';
import { TableSkeleton } from '../../components/common/LoadingSkeleton';
import EmptyState from '../../components/common/EmptyState';
import { Radio, Plus, Key, Trash2, Power, CheckCircle, XCircle } from 'lucide-react';

export default function EndpointsPage() {
  const queryClient = useQueryClient();
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [rotateTarget, setRotateTarget] = useState(null);

  const { data: endpointsData, isLoading } = useQuery({
    queryKey: ['endpoints'],
    queryFn: () => endpointApi.list(),
  });

  const toggleActiveMutation = useMutation({
    mutationFn: ({ id, is_active }) => endpointApi.update(id, { is_active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['endpoints'] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => endpointApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['endpoints'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-overview'] });
    },
  });

  const endpoints = endpointsData?.results || [];

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">Webhook Endpoints</h1>
          <p className="text-xs font-mono text-slate-400 mt-1">
            Registered HTTP receivers, cryptographic keys, and subscription rules
          </p>
        </div>

        <button
          onClick={() => setCreateModalOpen(true)}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/30 transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Add Destination Endpoint</span>
        </button>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        {isLoading ? (
          <TableSkeleton rows={4} cols={5} />
        ) : endpoints.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[11px] bg-slate-950/40">
                  <th className="py-3.5 px-4">Endpoint Name</th>
                  <th className="py-3.5 px-4">Destination URL</th>
                  <th className="py-3.5 px-4">Subscriptions</th>
                  <th className="py-3.5 px-4">Success Rate</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {endpoints.map((ep) => (
                  <tr key={ep.id} className="hover:bg-slate-850/50 transition-colors">
                    <td className="py-4 px-4 font-semibold text-slate-100">
                      <div className="flex items-center gap-2">
                        <Radio className="w-4 h-4 text-indigo-400 shrink-0" />
                        <span>{ep.name}</span>
                      </div>
                    </td>
                    <td className="py-4 px-4 font-mono text-slate-300 max-w-xs truncate">
                      {ep.destination_url}
                    </td>
                    <td className="py-4 px-4">
                      <div className="flex flex-wrap gap-1">
                        {ep.event_types?.map((t) => (
                          <span
                            key={t}
                            className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-[10px] text-indigo-300"
                          >
                            {t}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="py-4 px-4">
                      <span className="font-bold text-emerald-400">{ep.success_rate}%</span>
                      <span className="text-slate-400 text-[10px] ml-1">
                        ({ep.delivery_count} total)
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      {ep.is_active ? (
                        <span className="inline-flex items-center gap-1 text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full text-[10px] font-bold">
                          <CheckCircle className="w-3 h-3" /> ACTIVE
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-slate-400 bg-slate-500/10 px-2 py-0.5 rounded-full text-[10px] font-bold">
                          <XCircle className="w-3 h-3" /> DISABLED
                        </span>
                      )}
                    </td>
                    <td className="py-4 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => setRotateTarget(ep)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-amber-400 hover:bg-slate-800 transition-colors"
                          title="Rotate Signing Secret"
                        >
                          <Key className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() =>
                            toggleActiveMutation.mutate({
                              id: ep.id,
                              is_active: !ep.is_active,
                            })
                          }
                          className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-400 hover:bg-slate-800 transition-colors"
                          title={ep.is_active ? 'Disable Endpoint' : 'Enable Endpoint'}
                        >
                          <Power className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => {
                            if (window.confirm(`Delete endpoint "${ep.name}"?`)) {
                              deleteMutation.mutate(ep.id);
                            }
                          }}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors"
                          title="Delete Endpoint"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            icon={Radio}
            title="No webhook endpoints configured"
            description="Create your first destination endpoint to begin distributing subscribed events."
            action={
              <button
                onClick={() => setCreateModalOpen(true)}
                className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold"
              >
                Create Endpoint
              </button>
            }
          />
        )}
      </div>

      <CreateEndpointModal isOpen={createModalOpen} onClose={() => setCreateModalOpen(false)} />
      {rotateTarget && (
        <RotateSecretModal
          isOpen={!!rotateTarget}
          onClose={() => setRotateTarget(null)}
          endpoint={rotateTarget}
        />
      )}
    </div>
  );
}

