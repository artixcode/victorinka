import api from './api';

export const authAPI = {
    register: (userData) => api.post('/auth/register/', userData),
    login: (email, password) => api.post('/auth/login/', {email, password}),
    getProfile: () => api.get('/auth/me/'),
    logout: (refreshToken) => api.post('/auth/logout/', {refresh: refreshToken}),
    logoutAll: () => api.post('/auth/logout_all/'),
    updateProfile: (userData) => {
        return api.put('/api/user/profile/', userData);
    },
};
