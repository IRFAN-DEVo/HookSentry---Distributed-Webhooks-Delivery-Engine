import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { eventApi } from '../../api/event.api';
import IngestEventModal from '../../components/forms/IngestEventModal';
import { TableSkeleton } from '../../components/common/LoadingSkeleton';
import EmptyState from '../../components/common/EmptyState';
import { Send, Plus, ChevronDown, ChevronRight, CheckCircle2, Clock, XCircle } from 'lucide-react';

export default function EventsPage() {
  const [ingestModalOpen, setIngestModalOpen] = useState(false);
  const [expandedEventId, setExpandedEventId] = useState(null);

  const { data: eventsData, isLoading } = useQuery({
    queryKey: ['events'],
    queryFn: () => eventApi.list(),
    refetchInterval: 5000,
  });

  const events = eventsData?.results || [];

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">Event Explorer</h1>
          <p className="text-xs font-mono text-slate-400 mt-1">
            Immutable log of ingested webhook events, payloads, and fan-out targets
          </p>
        </div>

        <button
          onClick={() => setIngestModalOpen(true)}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/30 transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Ingest New Event</span>
        </button>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        {isLoading ? (
          <TableSkeleton rows={4} cols={5} />
        ) : events.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[11px] bg-slate-950/40">
                  <th className="py-3.5 px-4 w-10"></th>
                  <th className="py-3.5 px-4">Event ID</th>
                  <th className="py-3.5 px-4">Topic / Event Type</th>
                  <th className="py-3.5 px-4">Idempotency Key</th>
                  <th className="py-3.5 px-4">Deliveries</th>
                  <th className="py-3.5 px-4 text-right">Created At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {events.map((ev) => (
                  <React.Fragment key={ev.id}>
                    <tr
                      onClick={() =>
                        setExpandedEventId(expandedEventId === ev.id ? null : ev.id)
                      }
                      className="hover:bg-slate-850/50 cursor-pointer transition-colors"
                    >
                      <td className="py-4 px-4 text-slate-400">
                        {expandedEventId === ev.id ? (
                          <ChevronDown className="w-4 h-4" />
                        ) : (
                          <ChevronRight className="w-4 h-4" />
                        )}
                      </td>
                      <td className="py-4 px-4 font-bold text-indigo-400">
                        {ev.id.slice(0, 8)}...
                      </td>
                      <td className="py-4 px-4 font-semibold text-slate-100">
                        <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-indigo-300">
                          {ev.event_type}
                        </span>
                      </td>
                      <td className="py-4 px-4 text-slate-400">
                        {ev.idempotency_key || '—'}
                      </td>
                      <td className="py-4 px-4">
                        <div className="flex items-center gap-2">
                          <span className="text-slate-200 font-bold">{ev.delivery_count} target(s)</span>
                          {ev.success_count > 0 && (
                            <span className="inline-flex items-center gap-0.5 text-emerald-400 text-[10px]">
                              <CheckCircle2 className="w-3 h-3" /> {ev.success_count}
                            </span>
                          )}
                          {ev.failed_count > 0 && (
                            <span className="inline-flex items-center gap-0.5 text-rose-400 text-[10px]">
                              <XCircle className="w-3 h-3" /> {ev.failed_count}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-4 px-4 text-right text-slate-400">
                        {new Date(ev.created_at).toLocaleString()}
                      </td>
                    </tr>

                    {/* Collapsible raw JSON payload view */}
                    {expandedEventId === ev.id && (
                      <tr className="bg-slate-950/80 border-b border-slate-800">
                        <td colSpan={6} className="p-4 pl-12">
                          <div className="text-[11px] font-mono text-slate-400 mb-1">
                            Immutable Raw Event Payload:
                          </div>
                          <pre className="p-3.5 rounded-lg bg-slate-900 border border-slate-800 text-emerald-400 font-mono text-xs overflow-x-auto max-h-56">
                            {JSON.stringify(ev.payload, null, 2)}
                          </pre>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            icon={Send}
            title="No events ingested"
            description="Submit events through the Ingest API or use the manual dispatcher."
            action={
              <button
                onClick={() => setIngestModalOpen(true)}
                className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold"
              >
                Ingest Event
              </button>
            }
          />
        )}
      </div>

      <IngestEventModal isOpen={ingestModalOpen} onClose={() => setIngestModalOpen(false)} />
    </div>
  );
}

