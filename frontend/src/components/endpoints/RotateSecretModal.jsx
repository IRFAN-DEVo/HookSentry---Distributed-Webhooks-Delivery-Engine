import React, { useState } from 'react';
import Modal from '../common/Modal';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { endpointApi } from '../../api/endpoint.api';
import { AlertTriangle, Copy, Check } from 'lucide-react';

export default function RotateSecretModal({ isOpen, onClose, endpoint }) {
  const queryClient = useQueryClient();
  const [newSecret, setNewSecret] = useState(null);
  const [copied, setCopied] = useState(false);

  const rotateMutation = useMutation({
    mutationFn: () => endpointApi.rotateSecret(endpoint.id),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['endpoints'] });
      queryClient.invalidateQueries({ queryKey: ['delivery'] });
      setNewSecret(data.raw_signing_secret);
    },
  });

  const handleClose = () => {
    setNewSecret(null);
    setCopied(false);
    onClose();
  };

  const handleCopy = () => {
    if (newSecret) {
      navigator.clipboard.writeText(newSecret);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={newSecret ? 'New Signing Secret' : 'Rotate Endpoint Signing Secret'}
    >
      {newSecret ? (
        <div className="space-y-4">
          <p className="text-xs text-slate-300">
            The previous signing secret was revoked. Update your webhook receiver server to verify
            signatures using this new key:
          </p>

          <div className="flex items-center gap-2">
            <div className="flex-1 p-3 rounded-lg bg-slate-950 border border-slate-800 font-mono text-xs text-emerald-400 truncate select-all">
              {newSecret}
            </div>
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 px-3 py-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition-colors"
            >
              {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
              {copied ? 'Copied' : 'Copy'}
            </button>
          </div>

          <div className="pt-3 border-t border-slate-800 flex justify-end">
            <button
              onClick={handleClose}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold"
            >
              Close
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex gap-3">
            <AlertTriangle className="w-5 h-5 shrink-0 text-amber-400 mt-0.5" />
            <div>
              <p className="font-semibold mb-1">Warning: Secret Invalidation</p>
              <p>
                Rotating this secret will immediately invalidate the current signing key for{' '}
                <strong>{endpoint?.name}</strong>. Webhook deliveries signed with the old secret will
                fail signature validation until your server is updated.
              </p>
            </div>
          </div>

          <div className="pt-3 border-t border-slate-800 flex justify-end gap-2.5">
            <button
              onClick={handleClose}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
            >
              Cancel
            </button>
            <button
              onClick={() => rotateMutation.mutate()}
              disabled={rotateMutation.isPending}
              className="px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold shadow-md transition-colors disabled:opacity-50"
            >
              {rotateMutation.isPending ? 'Rotating Secret...' : 'Rotate Secret Now'}
            </button>
          </div>
        </div>
      )}
    </Modal>
  );
}
