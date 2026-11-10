import React, { useState } from 'react';
import { useUIStore } from '../../stores/ui.store';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { deliveryApi } from '../../api/delivery.api';
import StatusBadge from '../common/StatusBadge';
import { X, Play, Clock, ArrowRight, ShieldCheck, Copy, Check, Terminal, ExternalLink } from 'lucide-react';

export default function DeliveryInspectorDrawer() {
  const { inspectorOpen, selectedDeliveryId, closeInspector } = useUIStore();
  const [activeTab, setActiveTab] = useState('request'); // 'request' | 'response' | 'attempts'
  const [copied, setCopied] = useState(false);
  const queryClient = useQueryClient();

  const { data: delivery, isLoading } = useQuery({
    queryKey: ['delivery', selectedDeliveryId],
    queryFn: () => deliveryApi.get(selectedDeliveryId),
    enabled: !!selectedDeliveryId && inspectorOpen,
    refetchInterval: 3000,
  });

  const { data: attempts } = useQuery({
    queryKey: ['delivery-attempts', selectedDeliveryId],
    queryFn: () => deliveryApi.getAttempts(selectedDeliveryId),
    enabled: !!selectedDeliveryId && inspectorOpen,
  });

  const replayMutation = useMutation({
    mutationFn: (id) => deliveryApi.replay(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['delivery', selectedDeliveryId] });
      queryClient.invalidateQueries({ queryKey: ['delivery-attempts', selectedDeliveryId] });
      queryClient.invalidateQueries({ queryKey: ['deliveries'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-overview'] });
    },
  });

  if (!inspectorOpen) return null;

  const latestAttempt = attempts && attempts.length > 0 ? attempts[attempts.length - 1] : null;

  const handleCopyPayload = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden flex justify-end">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-950/70 backdrop-blur-xs transition-opacity"
        onClick={closeInspector}
      />

      {/* Slide-over panel */}
      <div className="relative w-full max-w-2xl bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col h-full z-10 animate-slideLeft">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/90">
          <div>
            <div className="flex items-center gap-2.5 mb-1">
              <span className="font-mono text-xs font-semibold text-indigo-400">
                DELIVERY INSPECTOR
              </span>
              {delivery && <StatusBadge status={delivery.status} />}
            </div>
            <div className="font-mono text-sm text-slate-200 truncate max-w-md">
              {delivery ? delivery.endpoint?.name : 'Loading delivery...'}
            </div>
          </div>

          <div className="flex items-center gap-2">
            {delivery?.is_replayable && (
              <button
                onClick={() => replayMutation.mutate(delivery.id)}
                disabled={replayMutation.isPending}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 hover:bg-indigo-500 text-white transition-colors disabled:opacity-50"
              >
                <Play className="w-3.5 h-3.5" />
                {replayMutation.isPending ? 'Queuing Replay...' : 'Replay Delivery'}
              </button>
            )}
            <button
              onClick={closeInspector}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-800 bg-slate-900/50 px-5 text-sm font-medium">
          <button
            onClick={() => setActiveTab('request')}
            className={`py-3 px-4 border-b-2 font-mono text-xs transition-colors ${
              activeTab === 'request'
                ? 'border-indigo-500 text-indigo-400 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            REQUEST
          </button>
          <button
            onClick={() => setActiveTab('response')}
            className={`py-3 px-4 border-b-2 font-mono text-xs transition-colors ${
              activeTab === 'response'
                ? 'border-indigo-500 text-indigo-400 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            RESPONSE
          </button>
          <button
            onClick={() => setActiveTab('attempts')}
            className={`py-3 px-4 border-b-2 font-mono text-xs transition-colors ${
              activeTab === 'attempts'
                ? 'border-indigo-500 text-indigo-400 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            ATTEMPTS ({attempts?.length || delivery?.attempt_count || 0})
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {isLoading ? (
            <div className="space-y-4">
              <div className="h-6 bg-slate-800 rounded animate-pulse w-3/4" />
              <div className="h-32 bg-slate-800 rounded animate-pulse" />
              <div className="h-48 bg-slate-800 rounded animate-pulse" />
            </div>
          ) : delivery ? (
            <>
              {/* Tab 1: REQUEST */}
              {activeTab === 'request' && (
                <div className="space-y-5">
                  {/* Target URL */}
                  <div>
                    <label className="text-xs font-mono font-semibold uppercase text-slate-400 block mb-1.5">
                      Destination URL
                    </label>
                    <div className="flex items-center gap-2 p-2.5 rounded-lg bg-slate-950 border border-slate-800 font-mono text-xs text-slate-200 break-all">
                      <span className="px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-[10px] font-bold">
                        POST
                      </span>
                      <span>{delivery.endpoint?.destination_url}</span>
                    </div>
                  </div>

                  {/* Request Headers */}
                  <div>
                    <label className="text-xs font-mono font-semibold uppercase text-slate-400 block mb-1.5">
                      Dispatched Request Headers
                    </label>
                    <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 font-mono text-xs text-slate-300 space-y-1.5">
                      {latestAttempt?.request_headers ? (
                        Object.entries(latestAttempt.request_headers).map(([k, v]) => (
                          <div key={k} className="flex gap-2">
                            <span className="text-indigo-400">{k}:</span>
                            <span className="text-slate-300 break-all">{v}</span>
                          </div>
                        ))
                      ) : (
                        <div className="text-slate-400">Headers prepared on next worker claim.</div>
                      )}
                    </div>
                  </div>

                  {/* JSON Payload */}
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <label className="text-xs font-mono font-semibold uppercase text-slate-400">
                        Webhook Payload
                      </label>
                      <button
                        onClick={() =>
                          handleCopyPayload(JSON.stringify(delivery.event?.payload, null, 2))
                        }
                        className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-indigo-400 transition-colors"
                      >
                        {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                        {copied ? 'Copied' : 'Copy JSON'}
                      </button>
                    </div>
                    <pre className="p-4 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-emerald-400 overflow-x-auto">
                      {JSON.stringify(delivery.event?.payload, null, 2)}
                    </pre>
                  </div>
                </div>
              )}

              {/* Tab 2: RESPONSE */}
              {activeTab === 'response' && (
                <div className="space-y-5">
                  {latestAttempt ? (
                    <>
                      {/* Status & Latency */}
                      <div className="grid grid-cols-2 gap-3">
                        <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                          <span className="text-[10px] font-mono uppercase text-slate-400 block mb-1">
                            HTTP Status
                          </span>
                          <span
                            className={`font-mono text-base font-bold ${
                              latestAttempt.response_status >= 200 &&
                              latestAttempt.response_status < 300
                                ? 'text-emerald-400'
                                : 'text-rose-400'
                            }`}
                          >
                            {latestAttempt.response_status || 'Connection Error'}
                          </span>
                        </div>
                        <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                          <span className="text-[10px] font-mono uppercase text-slate-400 block mb-1">
                            Duration
                          </span>
                          <span className="font-mono text-base font-bold text-slate-200">
                            {latestAttempt.duration_ms} ms
                          </span>
                        </div>
                      </div>

                      {/* Error Message if failed */}
                      {latestAttempt.error_message && (
                        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs font-mono">
                          <div className="font-semibold mb-1">Error Information:</div>
                          {latestAttempt.error_message}
                        </div>
                      )}

                      {/* Response Body */}
                      <div>
                        <label className="text-xs font-mono font-semibold uppercase text-slate-400 block mb-1.5">
                          Response Body
                        </label>
                        <pre className="p-4 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-slate-200 overflow-x-auto max-h-64 whitespace-pre-wrap">
                          {latestAttempt.response_body || '<Empty response body>'}
                        </pre>
                      </div>

                      {/* Response Headers */}
                      <div>
                        <label className="text-xs font-mono font-semibold uppercase text-slate-400 block mb-1.5">
                          Response Headers
                        </label>
                        <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 font-mono text-xs text-slate-300 space-y-1">
                          {Object.keys(latestAttempt.response_headers || {}).length > 0 ? (
                            Object.entries(latestAttempt.response_headers).map(([k, v]) => (
                              <div key={k} className="flex gap-2">
                                <span className="text-slate-400">{k}:</span>
                                <span className="text-slate-200 break-all">{v}</span>
                              </div>
                            ))
                          ) : (
                            <div className="text-slate-400">No response headers captured.</div>
                          )}
                        </div>
                      </div>
                    </>
                  ) : (
                    <div className="p-12 text-center text-slate-400 text-sm">
                      No response attempts recorded yet. The delivery is pending worker dispatch.
                    </div>
                  )}
                </div>
              )}

              {/* Tab 3: ATTEMPTS HISTORY */}
              {activeTab === 'attempts' && (
                <div className="space-y-4">
                  {attempts && attempts.length > 0 ? (
                    attempts.map((att) => (
                      <div
                        key={att.id}
                        className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs font-bold text-indigo-400">
                              Attempt #{att.attempt_number}
                            </span>
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                                att.result === 'SUCCESS'
                                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                  : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                              }`}
                            >
                              {att.result}
                            </span>
                          </div>
                          <span className="text-xs font-mono text-slate-400">
                            {att.duration_ms} ms
                          </span>
                        </div>

                        {att.error_message && (
                          <div className="text-xs text-rose-400 font-mono bg-rose-500/5 p-2 rounded border border-rose-500/10">
                            {att.error_message}
                          </div>
                        )}

                        <div className="text-[11px] font-mono text-slate-400 flex items-center justify-between pt-1 border-t border-slate-900">
                          <span>Started: {new Date(att.started_at).toLocaleTimeString()}</span>
                          <span>HTTP {att.response_status || 'N/A'}</span>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center text-slate-400 py-12 text-sm">
                      No execution attempts recorded.
                    </div>
                  )}
                </div>
              )}
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}

