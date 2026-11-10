import apiClient from './axios';

export const deliveryApi = {
  list: async (params = {}) => {
    const { data } = await apiClient.get('/deliveries/', { params });
    return data;
  },
  get: async (id) => {
    const { data } = await apiClient.get(`/deliveries/${id}/`);
    return data;
  },
  replay: async (id) => {
    const { data } = await apiClient.post(`/deliveries/${id}/replay/`);
    return data;
  },
  getAttempts: async (id) => {
    const { data } = await apiClient.get(`/deliveries/${id}/attempts/`);
    return data;
  },
  // Dead Letter Queue
  listDeadLetters: async (params = {}) => {
    const { data } = await apiClient.get('/dead-letters/', { params });
    return data;
  },
  getDeadLetter: async (id) => {
    const { data } = await apiClient.get(`/dead-letters/${id}/`);
    return data;
  },
};

