import apiClient from './axios';

export const authApi = {
  login: async (credentials) => {
    const { data } = await apiClient.post('/auth/login/', credentials);
    return data;
  },
  register: async (payload) => {
    const { data } = await apiClient.post('/auth/register/', payload);
    return data;
  },
  getMe: async () => {
    const { data } = await apiClient.get('/auth/me/');
    return data;
  },
  logout: async () => {
    try {
      await apiClient.post('/auth/logout/');
    } catch {
      // Ignore network errors on logout
    }
  },
};
