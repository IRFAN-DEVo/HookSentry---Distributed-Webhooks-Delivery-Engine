import apiClient from './axios';

export const workspaceApi = {
  list: async () => {
    const { data } = await apiClient.get('/workspaces/');
    return data;
  },
  create: async (payload) => {
    const { data } = await apiClient.post('/workspaces/', payload);
    return data;
  },
  get: async (id) => {
    const { data } = await apiClient.get(`/workspaces/${id}/`);
    return data;
  },
  update: async (id, payload) => {
    const { data } = await apiClient.patch(`/workspaces/${id}/`, payload);
    return data;
  },
  delete: async (id) => {
    const { data } = await apiClient.delete(`/workspaces/${id}/`);
    return data;
  },
  // Members
  listMembers: async (workspaceId) => {
    const { data } = await apiClient.get(`/workspaces/${workspaceId}/members/`);
    return data;
  },
  addMember: async (workspaceId, payload) => {
    const { data } = await apiClient.post(`/workspaces/${workspaceId}/members/`, payload);
    return data;
  },
  updateMemberRole: async (workspaceId, memberId, role) => {
    const { data } = await apiClient.patch(`/workspaces/${workspaceId}/members/${memberId}/`, { role });
    return data;
  },
  removeMember: async (workspaceId, memberId) => {
    const { data } = await apiClient.delete(`/workspaces/${workspaceId}/members/${memberId}/`);
    return data;
  },
  // API Keys
  listApiKeys: async () => {
    const { data } = await apiClient.get('/api-keys/');
    return data;
  },
  createApiKey: async (payload) => {
    const { data } = await apiClient.post('/api-keys/', payload);
    return data;
  },
  deleteApiKey: async (id) => {
    const { data } = await apiClient.delete(`/api-keys/${id}/`);
    return data;
  },
  // Audit Logs
  listAuditLogs: async (params = {}) => {
    const { data } = await apiClient.get('/audit-logs/', { params });
    return data;
  },
};

