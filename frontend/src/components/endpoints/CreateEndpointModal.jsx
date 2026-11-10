import React, { useState } from 'react';
import Modal from '../common/Modal';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { endpointApi } from '../../api/endpoint.api';
import { ShieldAlert, Copy, Check, Key } from 'lucide-react';

export default function CreateEndpointModal({ isOpen, onClose }) {
  const queryClient = useQueryClient();
  const [name, setName] = useState('');
  const [destinationUrl, setDestinationUrl] = useState('');
  const [eventTypesStr, setEventTypesStr] = useState('order.*, payment.*');
  const [isActive, setIsActive] = useState(true);
  const [createdSecret, setCreatedSecret] = useState(null);
  const [copied, setCopied] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const createMutation = useMutation({
    mutationFn: (payload) => endpointApi.create(payload),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['endpoints'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-overview'] });
      setCreatedSecret(data.raw_signing_secret);
    },
    onError: (err) => {
      const details = err.response?.data?.error?.details;
      if (details?.destination_url) {
        setErrorMsg(details.destination_url.join(' '));
      } else {
        setErrorMsg(err.response?.data?.error?.message || 'Failed to create endpoint.');
      }
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    setErrorMsg('');
    const eventTypes = eventTypesStr
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);

    createMutation.mutate({
      name,
      destination_url: destinationUrl,
      event_types: eventTypes.length > 0 ? eventTypes : ['*'],
      is_active: isActive,
    });
  };

  const handleClose = () => {
    setName('');
    setDestinationUrl('');
    setEventTypesStr('order.*, payment.*');
    setCreatedSecret(null);
    setErrorMsg('');
    setCopied(false);
    onClose();
  };

  const handleCopy = () => {
    if (createdSecret) {
      navigator.clipboard.writeText(createdSecret);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={createdSecret ? 'Endpoint Secret Generated' : 'Create Webhook Destination Endpoint'}
    >
      {createdSecret ? (
        <div className="space-y-5">
          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex gap-3">
            <ShieldAlert className="w-5 h-5 shrink-0 text-amber-400 mt-0.5" />
            <div>
              <p className="font-semibold mb-1">Save your signing secret now</p>
              <p>
                This secret is encrypted at rest using Fernet and will{' '}
                <strong>never be displayed in full again</strong>. Your receiver must use this key to
                verify HMAC-SHA256 signatures.
              </p>
            </div>
          </div>

          <div>
            <label className="text-xs font-mono font-semibold uppercase text-slate-400 block mb-1.5">
              Raw HMAC-SHA256 Signing Secret
            </label>
            <div className="flex items-center gap-2">
              <div className="flex-1 p-3 rounded-lg bg-slate-950 border border-slate-800 font-mono text-xs text-emerald-400 truncate select-all">
                {createdSecret}
              </div>
              <button
                onClick={handleCopy}
                className="flex items-center gap-1.5 px-3 py-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition-colors"
              >
                {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                {copied ? 'Copied' : 'Copy'}
              </button>
            </div>
          </div>

          <div className="pt-3 border-t border-slate-800 flex justify-end">
            <button
              onClick={handleClose}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold transition-colors"
            >
              Done & Return to Endpoints
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
              Endpoint Name
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Production Billing Webhook"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-lg bg-slate-950 border border-slate-800 focus:border-indigo-500 text-slate-200 text-sm outline-none transition-colors"
            />
          </div>

          <div>
            <label className="text-xs font-mono font-semibold text-slate-300 block mb-1">
              Destination URL (HTTPS required in prod)
            </label>
            <input
              type="url"
              required
              placeholder="https://api.yourdomain.com/webhooks"
              value={destinationUrl}
              onChange={(e) => setDestinationUrl(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-lg bg-slate-950 border border-slate-800 focus:border-indigo-500 text-slate-200 text-sm outline-none font-mono transition-colors"
            />
            <span className="text-[11px] text-slate-400 mt-1 block">
              Protected by SSRF guard (blocks loopback, cloud metadata, link-local addresses).
            </span>
          </div>

          <div>
            <label className="text-xs font-mono font-semibold text-slate-300 block mb-1">
              Subscribed Event Types (comma-separated, * for all)
            </label>
            <input
              type="text"
              value={eventTypesStr}
              onChange={(e) => setEventTypesStr(e.target.value)}
              placeholder="order.*, payment.succeeded, *"
              className="w-full px-3.5 py-2.5 rounded-lg bg-slate-950 border border-slate-800 focus:border-indigo-500 text-slate-200 text-sm outline-none font-mono transition-colors"
            />
          </div>

          <div className="flex items-center gap-2 pt-1">
            <input
              type="checkbox"
              id="isActiveCheck"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              className="rounded bg-slate-950 border-slate-800 text-indigo-600 focus:ring-indigo-500 w-4 h-4"
            />
            <label htmlFor="isActiveCheck" className="text-xs text-slate-300 font-medium">
              Enable endpoint immediately upon creation
            </label>
          </div>

          <div className="pt-3 border-t border-slate-800 flex justify-end gap-2.5">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/30 transition-colors disabled:opacity-50"
            >
              {createMutation.isPending ? 'Generating Endpoint...' : 'Create Endpoint'}
            </button>
          </div>
        </form>
      )}
    </Modal>
  );
}
