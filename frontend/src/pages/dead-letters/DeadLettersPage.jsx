import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { deliveryApi } from '../../api/delivery.api';
import { useUIStore } from '../../stores/ui.store';
import Modal from '../../components/common/Modal';
import { TableSkeleton } from '../../components/common/LoadingSkeleton';
import EmptyState from '../../components/common/EmptyState';
import { AlertOctagon, Play, Skull, CheckCircle2, ArrowUpRight } from 'lucide-react';

export default function DeadLettersPage() {
  const queryClient = useQueryClient();
  const { openInspector } = useUIStore();
  const [replayTarget, setReplayTarget] = useState(null);

  const { data: dlqData, isLoading } = useQuery({
    queryKey: ['dead-letters'],
    queryFn: () => deliveryApi.listDeadLetters(),
    refetchInterval: 5000,
  });

  const replayMutation = useMutation({
    mutationFn: (deliveryId) => deliveryApi.replay(deliveryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dead-letters'] });
      queryClient.invalidateQueries({ queryKey: ['deliveries'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-overview'] });
      setReplayTarget(null);
    },
  });

  const deadLetters = dlqData?.results || [];

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">Dead-Letter Queue (DLQ)</h1>
          <p className="text-xs font-mono text-slate-400 mt-1">
            Deliveries that exhausted all retry attempts or encountered unrecoverable non-retryable errors
          </p>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        {isLoading ? (
          <TableSkeleton rows={4} cols={5} />
        ) : deadLetters.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[11px] bg-slate-950/40">
                  <th className="py-3.5 px-4">Delivery ID</th>
                  <th className="py-3.5 px-4">Failure Reason</th>
                  <th className="py-3.5 px-4">Endpoint</th>
                  <th className="py-3.5 px-4">Attempts</th>
                  <th className="py-3.5 px-4">Resolution Status</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {deadLetters.map((dlq) => (
                  <tr key={dlq.id} className="hover:bg-slate-850/50 transition-colors">
                    <td
                      onClick={() => openInspector(dlq.delivery?.id)}
                      className="py-4 px-4 font-bold text-indigo-400 cursor-pointer hover:underline"
                    >
                      {dlq.delivery?.id?.slice(0, 8)}...
                    </td>
                    <td className="py-4 px-4 font-medium text-rose-400 max-w-sm truncate">
                      {dlq.failure_reason}
                    </td>
                    <td className="py-4 px-4 text-slate-300">
                      {dlq.delivery?.endpoint?.name}
                    </td>
                    <td className="py-4 px-4 text-slate-400">
                      {dlq.total_attempts} attempts
                    </td>
                    <td className="py-4 px-4">
                      {dlq.resolution_status === 'REPLAYED' ? (
                        <span className="inline-flex items-center gap-1 text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full text-[10px] font-bold">
                          <CheckCircle2 className="w-3 h-3" /> REPLAYED
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded-full text-[10px] font-bold">
                          <Skull className="w-3 h-3" /> UNRESOLVED
                        </span>
                      )}
                    </td>
                    <td className="py-4 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => openInspector(dlq.delivery?.id)}
                          className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition-colors"
                        >
                          Inspect
                        </button>
                        <button
                          onClick={() => setReplayTarget(dlq)}
                          className="flex items-center gap-1 px-2.5 py-1 rounded bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-colors"
                        >
                          <Play className="w-3 h-3" />
                          <span>Replay</span>
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
            icon={AlertOctagon}
            title="Dead-Letter Queue is empty"
            description="All webhook deliveries have succeeded or are safely recovering through automated retry schedules."
          />
        )}
      </div>

      {/* Replay Confirmation Modal */}
      {replayTarget && (
        <Modal
          isOpen={!!replayTarget}
          onClose={() => setReplayTarget(null)}
          title="Confirm Delivery Replay"
        >
          <div className="space-y-4">
            <p className="text-xs text-slate-300">
              Are you sure you want to manually replay delivery{' '}
              <strong className="text-indigo-400 font-mono">
                {replayTarget.delivery?.id?.slice(0, 8)}...
              </strong>
              ?
            </p>
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-slate-300 space-y-1">
              <div>
                <span className="text-slate-400">Endpoint:</span>{' '}
                {replayTarget.delivery?.endpoint?.name}
              </div>
              <div>
                <span className="text-slate-400">Original Event:</span>{' '}
                {replayTarget.delivery?.event?.event_type}
              </div>
              <div>
                <span className="text-slate-400">Prior Attempts:</span>{' '}
                {replayTarget.total_attempts}
              </div>
            </div>
            <p className="text-xs text-slate-400">
              The original event ID and payload will be preserved. A new delivery attempt will be
              executed asynchronously by a Celery worker.
            </p>

            <div className="pt-3 border-t border-slate-800 flex justify-end gap-2.5">
              <button
                onClick={() => setReplayTarget(null)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
              >
                Cancel
              </button>
              <button
                onClick={() => replayMutation.mutate(replayTarget.delivery?.id)}
                disabled={replayMutation.isPending}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md transition-colors disabled:opacity-50"
              >
                <Play className="w-3.5 h-3.5" />
                {replayMutation.isPending ? 'Queuing Replay...' : 'Confirm Replay'}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
