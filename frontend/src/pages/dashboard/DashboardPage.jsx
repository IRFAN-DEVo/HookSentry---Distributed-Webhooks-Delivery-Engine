import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '../../api/dashboard.api';
import { useUIStore } from '../../stores/ui.store';
import StatusBadge from '../../components/common/StatusBadge';
import { TableSkeleton } from '../../components/common/LoadingSkeleton';
import IngestEventModal from '../../components/forms/IngestEventModal';
import CreateEndpointModal from '../../components/endpoints/CreateEndpointModal';
import {
  Send,
  Layers,
  CheckCircle2,
  AlertTriangle,
  Skull,
  Clock,
  Radio,
  Plus,
  Play,
  ArrowUpRight,
  TrendingUp,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';

export default function DashboardPage() {
  const [ingestModalOpen, setIngestModalOpen] = useState(false);
  const [endpointModalOpen, setEndpointModalOpen] = useState(false);
  const { openInspector } = useUIStore();

  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ['dashboard-overview'],
    queryFn: dashboardApi.getOverview,
    refetchInterval: 5000,
  });

  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: dashboardApi.getDeliveryStats,
    refetchInterval: 10000,
  });

  const { data: recentDeliveries, isLoading: recentLoading } = useQuery({
    queryKey: ['dashboard-recent'],
    queryFn: dashboardApi.getRecentDeliveries,
    refetchInterval: 4000,
  });

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Top Banner & Quick Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">Delivery Engine Overview</h1>
          <p className="text-xs font-mono text-slate-400 mt-1">
            Real-time telemetry • At-least-once delivery semantics • HMAC cryptographic verification
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => setEndpointModalOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700/60 transition-colors"
          >
            <Radio className="w-4 h-4 text-indigo-400" />
            <span>New Endpoint</span>
          </button>
          <button
            onClick={() => setIngestModalOpen(true)}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/30 transition-colors"
          >
            <Send className="w-3.5 h-3.5" />
            <span>Dispatch Test Webhook</span>
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3.5">
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-mono uppercase">Total Events</span>
            <Send className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white">
            {overviewLoading ? '...' : overview?.total_events ?? 0}
          </div>
          <span className="text-[10px] text-slate-400">Ingested via REST</span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-mono uppercase">Deliveries</span>
            <Layers className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white">
            {overviewLoading ? '...' : overview?.total_deliveries ?? 0}
          </div>
          <span className="text-[10px] text-slate-400">Endpoint dispatches</span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-mono uppercase">Success Rate</span>
            <TrendingUp className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-emerald-400">
            {overviewLoading ? '...' : `${overview?.success_rate ?? 100}%`}
          </div>
          <span className="text-[10px] text-slate-400">
            {overview?.successful_deliveries ?? 0} delivered
          </span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-mono uppercase">Pending/Retry</span>
            <Clock className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-amber-400">
            {overviewLoading ? '...' : overview?.pending_deliveries ?? 0}
          </div>
          <span className="text-[10px] text-slate-400">In Celery / Outbox</span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-mono uppercase">Dead-Lettered</span>
            <Skull className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-rose-400">
            {overviewLoading ? '...' : overview?.dead_lettered_deliveries ?? 0}
          </div>
          <span className="text-[10px] text-slate-400">Retries exhausted</span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-mono uppercase">Avg Latency</span>
            <Clock className="w-4 h-4 text-violet-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-violet-400">
            {overviewLoading ? '...' : `${overview?.average_duration_ms ?? 0}ms`}
          </div>
          <span className="text-[10px] text-slate-400">Across workers</span>
        </div>
      </div>

      {/* Analytics Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Time-Series Area Chart (2 Cols) */}
        <div className="lg:col-span-2 p-5 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold text-slate-100">Delivery Volume & Reliability</h2>
              <p className="text-xs text-slate-400">Successful vs failed dispatches over the past 24 hours</p>
            </div>
          </div>

          <div className="h-64 w-full">
            {statsLoading ? (
              <div className="h-full flex items-center justify-center text-slate-400 text-xs">Loading chart...</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={statsData?.time_series || []}>
                  <defs>
                    <linearGradient id="colorSuccess" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10B981" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#10B981" stopOpacity={0.0} />
                    </linearGradient>
                    <linearGradient id="colorFailure" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#EF4444" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#EF4444" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="timestamp" stroke="#64748B" fontSize={11} tickLine={false} />
                  <YAxis stroke="#64748B" fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0F172A',
                      borderColor: '#1E293B',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="success"
                    name="Successful"
                    stroke="#10B981"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorSuccess)"
                  />
                  <Area
                    type="monotone"
                    dataKey="failure"
                    name="Failed / Retried"
                    stroke="#EF4444"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorFailure)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* HTTP Status Breakdown Donut Chart (1 Col) */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col justify-between">
          <div>
            <h2 className="text-sm font-semibold text-slate-100">HTTP Status Distribution</h2>
            <p className="text-xs text-slate-400">Response classification across destinations</p>
          </div>

          <div className="h-64 w-full flex items-center justify-center">
            {statsLoading ? (
              <div className="text-slate-400 text-xs">Loading status breakdown...</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={statsData?.status_breakdown || []}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="count"
                  >
                    {(statsData?.status_breakdown || []).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0F172A',
                      borderColor: '#1E293B',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                  />
                  <Legend
                    verticalAlign="bottom"
                    iconSize={8}
                    formatter={(val) => <span className="text-xs text-slate-400">{val}</span>}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      {/* Recent Deliveries Table */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-slate-100">Live Delivery Activity</h2>
            <p className="text-xs text-slate-400">Most recent asynchronous webhook dispatches</p>
          </div>
          <span className="flex items-center gap-1.5 text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Live Polling
          </span>
        </div>

        {recentLoading ? (
          <TableSkeleton rows={5} cols={5} />
        ) : recentDeliveries && recentDeliveries.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                  <th className="py-3 px-3">Delivery ID</th>
                  <th className="py-3 px-3">Event Type</th>
                  <th className="py-3 px-3">Endpoint</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-3">Attempts</th>
                  <th className="py-3 px-3">HTTP Code</th>
                  <th className="py-3 px-3 text-right">Inspect</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {recentDeliveries.map((del) => (
                  <tr
                    key={del.id}
                    onClick={() => openInspector(del.id)}
                    className="hover:bg-slate-800/50 cursor-pointer transition-colors group"
                  >
                    <td className="py-3.5 px-3 font-semibold text-indigo-400 truncate max-w-[120px]">
                      {del.id.slice(0, 8)}...
                    </td>
                    <td className="py-3.5 px-3 text-slate-200">
                      {del.event?.event_type || 'custom.event'}
                    </td>
                    <td className="py-3.5 px-3 text-slate-300 truncate max-w-[180px]">
                      {del.endpoint?.name}
                    </td>
                    <td className="py-3.5 px-3">
                      <StatusBadge status={del.status} size="xs" />
                    </td>
                    <td className="py-3.5 px-3 text-slate-400">
                      {del.attempt_count} / {del.max_attempts}
                    </td>
                    <td className="py-3.5 px-3">
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
                    <td className="py-3.5 px-3 text-right">
                      <button className="text-slate-400 group-hover:text-indigo-400 transition-colors p-1 rounded">
                        <ArrowUpRight className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-12 text-center text-slate-400 text-xs">
            No deliveries registered yet. Click &ldquo;Dispatch Test Webhook&rdquo; above to ingest an event.
          </div>
        )}
      </div>

      {/* Modals */}
      <IngestEventModal isOpen={ingestModalOpen} onClose={() => setIngestModalOpen(false)} />
      <CreateEndpointModal isOpen={endpointModalOpen} onClose={() => setEndpointModalOpen(false)} />
    </div>
  );
}

