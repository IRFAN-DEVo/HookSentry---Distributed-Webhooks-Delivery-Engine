import apiClient from './axios';

export const eventApi = {
  list: async (params = {}) => {
    const { data } = await apiClient.get('/events/', { params });
    return data;
  },
  ingest: async (payload, idempotencyKey = null) => {
    const headers = {};
    if (idempotencyKey) {
      headers['Idempotency-Key'] = idempotencyKey;
    }
    const { data } = await apiClient.post('/events/', payload, { headers });
    return data;
  },
  get: async (id) => {
    const { data } = await apiClient.get(`/events/${id}/`);
    return data;
  },
};

