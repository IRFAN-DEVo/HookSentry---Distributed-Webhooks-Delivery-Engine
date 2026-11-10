import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { deliveryApi } from '../../api/delivery.api';
import { useUIStore } from '../../stores/ui.store';
import StatusBadge from '../../components/common/StatusBadge';
import { TableSkeleton } from '../../components/common/LoadingSkeleton';
import EmptyState from '../../components/common/EmptyState';
import { Layers, Filter, Search, ArrowUpRight } from 'lucide-react';

const STATUS_FILTERS = [
  'ALL',
  'SUCCESS',
  'PENDING',
  'PROCESSING',
  'RETRY_SCHEDULED',
  'FAILED',
  'DEAD_LETTERED',
];

export default function DeliveriesPage() {
  const [selectedStatus, setSelectedStatus] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const { openInspector } = useUIStore();

  const { data: deliveriesData, isLoading } = useQuery({
    queryKey: ['deliveries', selectedStatus],
    queryFn: () =>
      deliveryApi.list(selectedStatus !== 'ALL' ? { status: selectedStatus } : {}),
    refetchInterval: 5000,
  });

  const rawDeliveries = deliveriesData?.results || [];
  const deliveries = rawDeliveries.filter((d) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      d.id.toLowerCase().includes(term) ||
      d.endpoint?.name?.toLowerCase().includes(term) ||
      d.event?.event_type?.toLowerCase().includes(term)
    );
  });

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">Delivery Logs</h1>
          <p className="text-xs font-mono text-slate-400 mt-1">
            Complete audit trail of asynchronous webhook dispatches, response telemetry, and retry states
          </p>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search by ID, endpoint, topic..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9 pr-3.5 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs font-mono text-slate-200 focus:border-indigo-500 outline-none w-64"
          />
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 border-b border-slate-800">
        {STATUS_FILTERS.map((st) => (
          <button
            key={st}
            onClick={() => setSelectedStatus(st)}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-colors shrink-0 ${
              selectedStatus === st
                ? 'bg-indigo-600 text-white'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            {st}
          </button>
        ))}
      </div>

      {/* Deliveries Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        {isLoading ? (
          <TableSkeleton rows={6} cols={6} />
        ) : deliveries.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[11px] bg-slate-950/40">
                  <th className="py-3.5 px-4">Delivery ID</th>
                  <th className="py-3.5 px-4">Topic / Event</th>
                  <th className="py-3.5 px-4">Destination Endpoint</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4">Attempts</th>
                  <th className="py-3.5 px-4">HTTP Status</th>
                  <th className="py-3.5 px-4">Created At</th>
                  <th className="py-3.5 px-4 text-right">Inspect</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {deliveries.map((del) => (
                  <tr
                    key={del.id}
                    onClick={() => openInspector(del.id)}
                    className="hover:bg-slate-850/60 cursor-pointer transition-colors group"
                  >
                    <td className="py-4 px-4 font-bold text-indigo-400 truncate max-w-[120px]">
                      {del.id.slice(0, 8)}...
                    </td>
                    <td className="py-4 px-4 font-semibold text-slate-200">
                      {del.event?.event_type || 'custom.event'}
                    </td>
                    <td className="py-4 px-4 text-slate-300 max-w-[180px] truncate">
                      {del.endpoint?.name}
                    </td>
                    <td className="py-4 px-4">
                      <StatusBadge status={del.status} size="xs" />
                    </td>
                    <td className="py-4 px-4 text-slate-400">
                      {del.attempt_count} / {del.max_attempts}
                    </td>
                    <td className="py-4 px-4">
                      <span
                        className={`font-bold ${
                          del.last_response_status >= 200 && del.last_response_status < 300
                            ? 'text-emerald-400'
                            : del.last_response_status
                            ? 'text-rose-400'
                            : 'text-slate-400'
                        }`}
                      >
                        {del.last_response_status || '—'}
                      </span>
                    </td>
                    <td className="py-4 px-4 text-slate-400">
                      {new Date(del.created_at).toLocaleTimeString()}
                    </td>
                    <td className="py-4 px-4 text-right">
                      <button className="text-slate-400 group-hover:text-indigo-400 transition-colors p-1">
                        <ArrowUpRight className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            icon={Layers}
            title="No deliveries match your criteria"
            description="Deliveries will be logged as soon as events are ingested and matched with endpoints."
          />
        )}
      </div>
    </div>
  );
}
