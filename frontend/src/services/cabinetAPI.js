import api from './api';

export const cabinetAPI = {
  getStats: () => {
    return api.get('/cabinet/stats/');
  },

  getHistory: (params = {}) => {
    return api.get('/cabinet/history/', { params });
  },

  getBookmarks: () => {
    return api.get('/cabinet/bookmarks/');
  },

  addBookmark: (bookmarkData) => {
    return api.post('/cabinet/bookmarks/add/', bookmarkData);
  },

  getBookmark: (id) => {
    return api.get(`/cabinet/bookmarks/${id}/`);
  },

  updateBookmark: (id, bookmarkData) => {
    return api.patch(`/cabinet/bookmarks/${id}/`, bookmarkData);
  },

  deleteBookmark: (id) => {
    return api.delete(`/cabinet/bookmarks/${id}/`);
  },

  // Активные комнаты
  getActiveRooms: () => {
    return api.get('/cabinet/active-room/');
  }
};