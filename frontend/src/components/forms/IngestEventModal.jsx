import React, { useState } from 'react';
import Modal from '../common/Modal';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { eventApi } from '../../api/event.api';
import { Send, CheckCircle2 } from 'lucide-react';

const DEFAULT_PAYLOAD = JSON.stringify(
  {
    order_id: 2048,
    amount: 7500,
    currency: 'USD',
    customer: {
      name: 'Sarah Connor',
      email: 'sarah@example.com',
    },
    items: [
      { id: 'item_1', name: 'CyberShield Pro', qty: 1, price: 7500 },
    ],
  },
  null,
  2
);

export default function IngestEventModal({ isOpen, onClose }) {
  const queryClient = useQueryClient();
  const [eventType, setEventType] = useState('order.created');
  const [idempotencyKey, setIdempotencyKey] = useState('');
  const [payloadStr, setPayloadStr] = useState(DEFAULT_PAYLOAD);
  const [errorMsg, setErrorMsg] = useState('');
  const [resultData, setResultData] = useState(null);

  const ingestMutation = useMutation({
    mutationFn: ({ event_type, payload, idempotency_key }) =>
      eventApi.ingest({ event_type, payload }, idempotency_key || null),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['events'] });
      queryClient.invalidateQueries({ queryKey: ['deliveries'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-overview'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-recent'] });
      setResultData(data);
    },
    onError: (err) => {
      setErrorMsg(
        err.response?.data?.error?.message ||
        err.response?.data?.detail ||
        'Failed to ingest event.'
      );
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    setErrorMsg('');
    try {
      const parsed = JSON.parse(payloadStr);
      ingestMutation.mutate({
        event_type: eventType,
        payload: parsed,
        idempotency_key: idempotencyKey,
      });
    } catch {
      setErrorMsg('Invalid JSON format in webhook payload.');
    }
  };

  const handleClose = () => {
    setResultData(null);
    setErrorMsg('');
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={resultData ? 'Event Successfully Ingested' : 'Ingest New Webhook Event'}
      maxWidth="max-w-xl"
    >
      {resultData ? (
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex gap-3">
            <CheckCircle2 className="w-5 h-5 shrink-0 text-emerald-400 mt-0.5" />
            <div>
              <p className="font-semibold mb-1">Event Persisted & Deliveries Dispatched</p>
              <p>
                The event has been durably recorded in PostgreSQL and{' '}
                <strong>{resultData.deliveries_created} delivery task(s)</strong> were queued
                through the Transactional Outbox for asynchronous Celery worker processing.
              </p>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 font-mono text-xs text-slate-300 space-y-1">
            <div>
              <span className="text-slate-400">Event ID:</span> {resultData.event_id}
            </div>
            <div>
              <span className="text-slate-400">Event Type:</span> {resultData.event_type}
            </div>
            <div>
              <span className="text-slate-400">Matching Endpoints:</span>{' '}
              {resultData.matching_endpoints}
            </div>
            <div>
              <span className="text-slate-400">Deliveries Created:</span>{' '}
              {resultData.deliveries_created}
            </div>
          </div>

          <div className="pt-3 border-t border-slate-800 flex justify-end">
            <button
              onClick={handleClose}
              className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold"
            >
              Done & View Deliveries
            </button>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          {errorMsg && (
            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs">
              {errorMsg}
            </div>
          )}

          <div>
            <label className="text-xs font-mono font-semibold text-slate-300 block mb-1">
              Event Type (Topic)
            </label>
            <input
              type="text"
              required
              placeholder="e.g. order.created, invoice.paid"
              value={eventType}
              onChange={(e) => setEventType(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-lg bg-slate-950 border border-slate-800 focus:border-indigo-500 text-slate-200 text-sm font-mono outline-none"
            />
          </div>

          <div>
            <label className="text-xs font-mono font-semibold text-slate-300 block mb-1">
              Idempotency Key (Optional)
            </label>
            <input
              type="text"
              placeholder="e.g. idem_req_998877"
              value={idempotencyKey}
              onChange={(e) => setIdempotencyKey(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-lg bg-slate-950 border border-slate-800 focus:border-indigo-500 text-slate-200 text-sm font-mono outline-none"
            />
          </div>

          <div>
            <label className="text-xs font-mono font-semibold text-slate-300 block mb-1">
              JSON Event Payload
            </label>
            <textarea
              rows={8}
              required
              value={payloadStr}
              onChange={(e) => setPayloadStr(e.target.value)}
              className="w-full p-3.5 rounded-lg bg-slate-950 border border-slate-800 focus:border-indigo-500 text-slate-200 text-xs font-mono outline-none resize-y"
            />
          </div>

          <div className="pt-3 border-t border-slate-800 flex justify-end gap-2.5">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={ingestMutation.isPending}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/30 transition-colors disabled:opacity-50"
            >
              <Send className="w-3.5 h-3.5" />
              {ingestMutation.isPending ? 'Ingesting Event...' : 'Dispatch Event'}
            </button>
          </div>
        </form>
      )}
    </Modal>
  );
}
