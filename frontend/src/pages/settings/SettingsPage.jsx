import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { workspaceApi } from '../../api/workspace.api';
import { useWorkspaceStore } from '../../stores/workspace.store';
import Modal from '../../components/common/Modal';
import { TableSkeleton } from '../../components/common/LoadingSkeleton';
import {
  Building2,
  Users,
  Key,
  ShieldCheck,
  Plus,
  Trash2,
  Copy,
  Check,
  AlertTriangle,
  History,
} from 'lucide-react';

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const { activeWorkspace } = useWorkspaceStore();
  const [activeTab, setActiveTab] = useState('members'); // 'members' | 'apikeys' | 'audit'

  // Member Invite State
  const [inviteModalOpen, setInviteModalOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('MEMBER');
  const [inviteError, setInviteError] = useState('');

  // API Key State
  const [keyModalOpen, setKeyModalOpen] = useState(false);
  const [keyName, setKeyName] = useState('');
  const [newRawKey, setNewRawKey] = useState(null);
  const [copiedKey, setCopiedKey] = useState(false);

  // Queries
  const { data: members, isLoading: membersLoading } = useQuery({
    queryKey: ['workspace-members', activeWorkspace?.id],
    queryFn: () => workspaceApi.listMembers(activeWorkspace.id),
    enabled: !!activeWorkspace?.id,
  });

  const { data: apiKeysData, isLoading: keysLoading } = useQuery({
    queryKey: ['api-keys', activeWorkspace?.id],
    queryFn: () => workspaceApi.listApiKeys(),
    enabled: !!activeWorkspace?.id,
  });

  const { data: auditLogsData, isLoading: auditLoading } = useQuery({
    queryKey: ['audit-logs', activeWorkspace?.id],
    queryFn: () => workspaceApi.listAuditLogs(),
    enabled: !!activeWorkspace?.id,
  });

  // Mutations
  const addMemberMutation = useMutation({
    mutationFn: (payload) => workspaceApi.addMember(activeWorkspace.id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workspace-members', activeWorkspace.id] });
      setInviteModalOpen(false);
      setInviteEmail('');
      setInviteError('');
    },
    onError: (err) => {
      setInviteError(
        err.response?.data?.error?.details?.user_email?.[0] ||
        err.response?.data?.error?.message ||
        'Failed to invite member.'
      );
    },
  });

  const removeMemberMutation = useMutation({
    mutationFn: (memberId) => workspaceApi.removeMember(activeWorkspace.id, memberId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['workspace-members', activeWorkspace.id] }),
  });

  const createKeyMutation = useMutation({
    mutationFn: (payload) => workspaceApi.createApiKey(payload),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['api-keys', activeWorkspace.id] });
      setNewRawKey(data.raw_key);
    },
  });

  const deleteKeyMutation = useMutation({
    mutationFn: (id) => workspaceApi.deleteApiKey(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['api-keys', activeWorkspace.id] }),
  });

  const apiKeys = apiKeysData?.results || [];
  const auditLogs = auditLogsData?.results || [];

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Workspace Header Info */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
            <Building2 className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-extrabold text-white">{activeWorkspace?.name}</h1>
            <p className="text-xs font-mono text-slate-400">
              Workspace ID: {activeWorkspace?.id} • Role: {activeWorkspace?.role || 'OWNER'}
            </p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800 space-x-6 text-sm font-medium">
        <button
          onClick={() => setActiveTab('members')}
          className={`pb-3 border-b-2 flex items-center gap-2 font-mono text-xs transition-colors ${
            activeTab === 'members'
              ? 'border-indigo-500 text-indigo-400 font-semibold'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Users className="w-4 h-4" />
          <span>Members & Roles</span>
        </button>
        <button
          onClick={() => setActiveTab('apikeys')}
          className={`pb-3 border-b-2 flex items-center gap-2 font-mono text-xs transition-colors ${
            activeTab === 'apikeys'
              ? 'border-indigo-500 text-indigo-400 font-semibold'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Key className="w-4 h-4" />
          <span>API Keys (M2M)</span>
        </button>
        <button
          onClick={() => setActiveTab('audit')}
          className={`pb-3 border-b-2 flex items-center gap-2 font-mono text-xs transition-colors ${
            activeTab === 'audit'
              ? 'border-indigo-500 text-indigo-400 font-semibold'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <History className="w-4 h-4" />
          <span>Audit Log Trail</span>
        </button>
      </div>

      {/* Tab 1: Members */}
      {activeTab === 'members' && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-slate-200">Workspace Members</h2>
              <p className="text-xs text-slate-400">Users with access to this tenant workspace</p>
            </div>
            <button
              onClick={() => setInviteModalOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Invite Member</span>
            </button>
          </div>

          {membersLoading ? (
            <TableSkeleton rows={3} cols={4} />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[11px] bg-slate-950/40">
                    <th className="py-3 px-4">Member Email</th>
                    <th className="py-3 px-4">Full Name</th>
                    <th className="py-3 px-4">Role</th>
                    <th className="py-3 px-4">Joined At</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {members?.map((m) => (
                    <tr key={m.id} className="hover:bg-slate-850/50">
                      <td className="py-3.5 px-4 font-semibold text-slate-200">{m.user?.email}</td>
                      <td className="py-3.5 px-4 text-slate-300">{m.user?.full_name || '—'}</td>
                      <td className="py-3.5 px-4">
                        <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-indigo-400 font-bold text-[10px]">
                          {m.role}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-slate-400">
                        {new Date(m.joined_at).toLocaleDateString()}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        {m.role !== 'OWNER' && (
                          <button
                            onClick={() => removeMemberMutation.mutate(m.id)}
                            className="text-slate-400 hover:text-rose-400 p-1"
                            title="Remove Member"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: API Keys */}
      {activeTab === 'apikeys' && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-slate-200">Machine-to-Machine API Keys</h2>
              <p className="text-xs text-slate-400">Authenticate upstream event ingestion without user logins</p>
            </div>
            <button
              onClick={() => setKeyModalOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Generate New API Key</span>
            </button>
          </div>

          {keysLoading ? (
            <TableSkeleton rows={2} cols={4} />
          ) : apiKeys.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[11px] bg-slate-950/40">
                    <th className="py-3 px-4">Key Name</th>
                    <th className="py-3 px-4">Key Prefix</th>
                    <th className="py-3 px-4">Created At</th>
                    <th className="py-3 px-4">Last Used</th>
                    <th className="py-3 px-4 text-right">Revoke</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {apiKeys.map((k) => (
                    <tr key={k.id} className="hover:bg-slate-850/50">
                      <td className="py-3.5 px-4 font-semibold text-slate-200">{k.name}</td>
                      <td className="py-3.5 px-4 text-indigo-400 font-bold">{k.prefix}••••••••</td>
                      <td className="py-3.5 px-4 text-slate-400">{new Date(k.created_at).toLocaleDateString()}</td>
                      <td className="py-3.5 px-4 text-slate-400">{k.last_used_at ? new Date(k.last_used_at).toLocaleDateString() : 'Never'}</td>
                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={() => {
                            if (window.confirm(`Revoke API key "${k.name}"?`)) {
                              deleteKeyMutation.mutate(k.id);
                            }
                          }}
                          className="text-slate-400 hover:text-rose-400 p-1"
                          title="Revoke Key"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-8 text-center text-xs text-slate-400 font-mono">
              No API keys generated yet. Click &ldquo;Generate New API Key&rdquo; above.
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Audit Logs */}
      {activeTab === 'audit' && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
          <div className="p-4 border-b border-slate-800">
            <h2 className="text-sm font-semibold text-slate-200">Security & Operational Audit Log</h2>
            <p className="text-xs text-slate-400">Immutable audit record of all tenant activities</p>
          </div>

          {auditLoading ? (
            <TableSkeleton rows={5} cols={4} />
          ) : auditLogs.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[11px] bg-slate-950/40">
                    <th className="py-3 px-4">Timestamp</th>
                    <th className="py-3 px-4">Action</th>
                    <th className="py-3 px-4">Actor</th>
                    <th className="py-3 px-4">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {auditLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-850/50">
                      <td className="py-3.5 px-4 text-slate-400">{new Date(log.created_at).toLocaleString()}</td>
                      <td className="py-3.5 px-4">
                        <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-indigo-300 font-bold text-[10px]">
                          {log.action}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-slate-200">{log.actor?.email || 'System'}</td>
                      <td className="py-3.5 px-4 text-slate-400 truncate max-w-xs">
                        {JSON.stringify(log.details)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-8 text-center text-xs text-slate-400 font-mono">
              No audit records logged yet.
            </div>
          )}
        </div>
      )}

      {/* Invite Member Modal */}
      <Modal isOpen={inviteModalOpen} onClose={() => setInviteModalOpen(false)} title="Invite Member to Workspace">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            addMemberMutation.mutate({ user_email: inviteEmail, role: inviteRole });
          }}
          className="space-y-4"
        >
          {inviteError && (
            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs">
              {inviteError}
            </div>
          )}
          <div>
            <label className="text-xs font-mono font-semibold text-slate-300 block mb-1">User Email Address</label>
            <input
              type="email"
              required
              placeholder="user@company.com"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-lg bg-slate-950 border border-slate-800 focus:border-indigo-500 text-slate-200 text-sm outline-none"
            />
          </div>
          <div>
            <label className="text-xs font-mono font-semibold text-slate-300 block mb-1">Role</label>
            <select
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-lg bg-slate-950 border border-slate-800 focus:border-indigo-500 text-slate-200 text-sm font-mono outline-none"
            >
              <option value="MEMBER">Member (View & Ingest)</option>
              <option value="ADMIN">Admin (Manage Endpoints & Settings)</option>
              <option value="OWNER">Owner (Full Permissions)</option>
            </select>
          </div>
          <div className="pt-3 border-t border-slate-800 flex justify-end gap-2.5">
            <button
              type="button"
              onClick={() => setInviteModalOpen(false)}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={addMemberMutation.isPending}
              className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold disabled:opacity-50"
            >
              {addMemberMutation.isPending ? 'Inviting...' : 'Add Member'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Create API Key Modal */}
      <Modal
        isOpen={keyModalOpen}
        onClose={() => {
          setKeyModalOpen(false);
          setNewRawKey(null);
          setKeyName('');
        }}
        title={newRawKey ? 'API Key Generated' : 'Generate Machine-to-Machine API Key'}
      >
        {newRawKey ? (
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex gap-3">
              <AlertTriangle className="w-5 h-5 shrink-0 text-amber-400 mt-0.5" />
              <div>
                <p className="font-semibold mb-1">Copy this API key now</p>
                <p>Only the SHA-256 hash is saved. You will not be able to see this key again.</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <div className="flex-1 p-3 rounded-lg bg-slate-950 border border-slate-800 font-mono text-xs text-emerald-400 truncate select-all">
                {newRawKey}
              </div>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(newRawKey);
                  setCopiedKey(true);
                  setTimeout(() => setCopiedKey(false), 2000);
                }}
                className="flex items-center gap-1.5 px-3 py-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium"
              >
                {copiedKey ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                {copiedKey ? 'Copied' : 'Copy'}
              </button>
            </div>

            <div className="pt-3 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => {
                  setKeyModalOpen(false);
                  setNewRawKey(null);
                  setKeyName('');
                }}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold"
              >
                Done
              </button>
            </div>
          </div>
        ) : (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              createKeyMutation.mutate({ name: keyName });
            }}
            className="space-y-4"
          >
            <div>
              <label className="text-xs font-mono font-semibold text-slate-300 block mb-1">Key Name / Description</label>
              <input
                type="text"
                required
                placeholder="e.g. Ingest Service Node 1"
                value={keyName}
                onChange={(e) => setKeyName(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-lg bg-slate-950 border border-slate-800 focus:border-indigo-500 text-slate-200 text-sm outline-none"
              />
            </div>
            <div className="pt-3 border-t border-slate-800 flex justify-end gap-2.5">
              <button
                type="button"
                onClick={() => setKeyModalOpen(false)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={createKeyMutation.isPending}
                className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold disabled:opacity-50"
              >
                {createKeyMutation.isPending ? 'Generating...' : 'Generate Key'}
              </button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
}

