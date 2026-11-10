import apiClient from './axios';

export const endpointApi = {
  list: async (params = {}) => {
    const { data } = await apiClient.get('/endpoints/', { params });
    return data;
  },
  create: async (payload) => {
    const { data } = await apiClient.post('/endpoints/', payload);
    return data;
  },
  get: async (id) => {
    const { data } = await apiClient.get(`/endpoints/${id}/`);
    return data;
  },
  update: async (id, payload) => {
    const { data } = await apiClient.patch(`/endpoints/${id}/`, payload);
    return data;
  },
  delete: async (id) => {
    const { data } = await apiClient.delete(`/endpoints/${id}/`);
    return data;
  },
  rotateSecret: async (id) => {
    const { data } = await apiClient.post(`/endpoints/${id}/rotate-secret/`);
    return data;
  },
  getStats: async (id) => {
    const { data } = await apiClient.get(`/endpoints/${id}/stats/`);
    return data;
  },
};
