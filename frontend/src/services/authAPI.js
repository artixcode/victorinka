import api from './api';

export const authAPI = {
  register: (userData) =>
    api.post('/api/auth/register/', userData),

  login: (email, password) =>
    api.post('/api/auth/login/', { email, password }),

  getProfile: () =>
    api.get('/api/auth/me/'),

  logout: (refreshToken) =>
    api.post('/api/auth/logout/', { refresh: refreshToken }),

  logoutAll: () =>
    api.post('/api/auth/logout_all/'),
};