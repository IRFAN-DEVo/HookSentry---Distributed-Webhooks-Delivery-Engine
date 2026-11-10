import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '../../api/dashboard.api';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
  LineChart,
  Line,
} from 'recharts';
import { BarChart3, TrendingUp, Clock, Radio, ShieldCheck } from 'lucide-react';

export default function AnalyticsPage() {
  const { data: statsData, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: dashboardApi.getDeliveryStats,
    refetchInterval: 10000,
  });

  const { data: overview } = useQuery({
    queryKey: ['dashboard-overview'],
    queryFn: dashboardApi.getOverview,
  });

  return (
    <div className="space-y-8 animate-fadeIn">
      <div>
        <h1 className="text-2xl font-extrabold text-white tracking-tight">System Analytics & Latency</h1>
        <p className="text-xs font-mono text-slate-400 mt-1">
          Endpoint latency profiles, error distributions, and historical reliability metrics
        </p>
      </div>

      {/* Latency over time line chart */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
        <div>
          <h2 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <Clock className="w-4 h-4 text-indigo-400" />
            <span>Average Dispatch Latency (ms)</span>
          </h2>
          <p className="text-xs text-slate-400">Time taken for third-party endpoints to respond to webhooks</p>
        </div>

        <div className="h-64 w-full">
          {isLoading ? (
            <div className="h-full flex items-center justify-center text-slate-400 text-xs">Loading latency...</div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={statsData?.time_series || []}>
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
                <Line
                  type="monotone"
                  dataKey="avg_duration_ms"
                  name="Latency (ms)"
                  stroke="#8B5CF6"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: '#8B5CF6' }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Grid: Endpoint Performance & Failure Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Endpoint Performance Table */}
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <div>
            <h2 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <Radio className="w-4 h-4 text-indigo-400" />
              <span>Endpoint Reliability Rankings</span>
            </h2>
            <p className="text-xs text-slate-400">Success rate per registered destination</p>
          </div>

          {statsData?.endpoint_performance && statsData.endpoint_performance.length > 0 ? (
            <div className="space-y-3 font-mono text-xs">
              {statsData.endpoint_performance.map((ep) => (
                <div
                  key={ep.id}
                  className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between"
                >
                  <div className="truncate max-w-[200px]">
                    <span className="font-semibold text-slate-200 block truncate">{ep.name}</span>
                    <span className="text-[10px] text-slate-400">
                      {ep.success} / {ep.total} delivered
                    </span>
                  </div>
                  <div className="text-right">
                    <span
                      className={`text-sm font-bold ${
                        ep.rate >= 95 ? 'text-emerald-400' : ep.rate >= 75 ? 'text-amber-400' : 'text-rose-400'
                      }`}
                    >
                      {ep.rate}%
                    </span>
                    <span className="text-[10px] text-slate-400 block">success</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-12 text-center text-slate-400 text-xs">No endpoint data available yet.</div>
          )}
        </div>

        {/* HTTP Status Breakdown Chart */}
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col justify-between">
          <div>
            <h2 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-indigo-400" />
              <span>Failure Distribution & HTTP Codes</span>
            </h2>
            <p className="text-xs text-slate-400">Classification of receiving server responses</p>
          </div>

          <div className="h-64 w-full flex items-center justify-center">
            {isLoading ? (
              <div className="text-slate-400 text-xs">Loading chart...</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={statsData?.status_breakdown || []} layout="vertical">
                  <XAxis type="number" stroke="#64748B" fontSize={11} />
                  <YAxis type="category" dataKey="name" stroke="#64748B" fontSize={11} width={110} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0F172A',
                      borderColor: '#1E293B',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                  />
                  <Bar dataKey="count" name="Count" fill="#6366F1" radius={[0, 4, 4, 0]}>
                    {(statsData?.status_breakdown || []).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

