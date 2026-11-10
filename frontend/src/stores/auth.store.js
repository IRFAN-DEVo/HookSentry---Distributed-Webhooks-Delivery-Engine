import { create } from 'zustand';

const ACCESS_TOKEN_KEY = 'hooksentry_access_token';
const REFRESH_TOKEN_KEY = 'hooksentry_refresh_token';
const USER_KEY = 'hooksentry_user';

export const useAuthStore = create((set) => ({
  user: (() => {
    try {
      const saved = localStorage.getItem(USER_KEY);
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  })(),
  accessToken: localStorage.getItem(ACCESS_TOKEN_KEY) || null,
  refreshToken: localStorage.getItem(REFRESH_TOKEN_KEY) || null,
  isAuthenticated: !!localStorage.getItem(ACCESS_TOKEN_KEY),

  setAuth: (user, accessToken, refreshToken) => {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    if (refreshToken) {
      localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    }
    set({
      user,
      accessToken,
      refreshToken: refreshToken || null,
      isAuthenticated: true,
    });
  },

  setTokens: (accessToken, refreshToken) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    if (refreshToken) {
      localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    }
    set((state) => ({
      accessToken,
      refreshToken: refreshToken || state.refreshToken,
      isAuthenticated: true,
    }));
  },

  logout: () => {
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    set({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
    });
  },
}));

