import apiClient from './axios';

export const dashboardApi = {
  getOverview: async () => {
    const { data } = await apiClient.get('/dashboard/overview/');
    return data;
  },
  getDeliveryStats: async () => {
    const { data } = await apiClient.get('/dashboard/delivery-stats/');
    return data;
  },
  getRecentDeliveries: async () => {
    const { data } = await apiClient.get('/dashboard/recent-deliveries/');
    return data;
  },
};
