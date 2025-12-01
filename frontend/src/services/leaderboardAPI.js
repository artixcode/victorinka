import api from './api';

const leaderboardAPI = {
  getGlobal: (params = {}) => {
    return api.get('/leaderboard/global/', { params });
  },

  getQuiz: (quizId, params = {}) => {
    return api.get(`/leaderboard/quiz/${quizId}/`, { params });
  },

  getRoom: (roomId, params = {}) => {
    return api.get(`/leaderboard/room/${roomId}/`, { params });
  },

  getUserStats: (userId, params = {}) => {
    return api.get(`/leaderboard/user/${userId}/`, { params });
  },

  fetchGlobalLeaderboard: async (ordering = '-total_points', limit = 100) => {
    try {
      const response = await api.get('/leaderboard/global/', {
        params: { ordering, limit }
      });

      let data = response.data;

      if (data && typeof data === 'object' && !Array.isArray(data)) {
        if (data.results && Array.isArray(data.results)) {
          data = data.results;
        } else if (data.leaderboard && Array.isArray(data.leaderboard)) {
          data = data.leaderboard;
        } else if (Array.isArray(data)) {
          return data;
        } else {
          data = Object.values(data);
        }
      }

      return Array.isArray(data) ? data : [];
    } catch (error) {
      console.error('Error fetching global leaderboard:', error);
      throw error;
    }
  },

  fetchQuizLeaderboard: async (quizId, limit = 50) => {
    try {
      const response = await api.get(`/leaderboard/quiz/${quizId}/`, {
        params: { limit }
      });

      let data = response.data;

      if (data && typeof data === 'object') {
        if (data.leaderboard && Array.isArray(data.leaderboard)) {
          data = data.leaderboard;
        } else if (data.results && Array.isArray(data.results)) {
          data = data.results;
        } else if (Array.isArray(data)) {
          return data;
        } else {
          data = Object.values(data);
        }
      }

      return Array.isArray(data) ? data : [];
    } catch (error) {
      console.error('Error fetching quiz leaderboard:', error);
      throw error;
    }
  },

  fetchRoomLeaderboard: async (roomId) => {
    try {
      const response = await api.get(`/leaderboard/room/${roomId}/`);

      let data = response.data;

      if (data && typeof data === 'object') {
        if (data.leaderboard && Array.isArray(data.leaderboard)) {
          data = data.leaderboard;
        } else if (data.results && Array.isArray(data.results)) {
          data = data.results;
        } else if (Array.isArray(data)) {
          return data;
        } else {
          data = Object.values(data);
        }
      }

      return Array.isArray(data) ? data : [];
    } catch (error) {
      console.error('Error fetching room leaderboard:', error);
      throw error;
    }
  },

  fetchUserStats: async (userId) => {
    try {
      const response = await api.get(`/leaderboard/user/${userId}/`);
      return response.data;
    } catch (error) {
      console.error('Error fetching user stats:', error);
      throw error;
    }
  },

  fetchMyStats: async () => {
    try {
      const response = await api.get('/leaderboard/user/me/');
      return response.data;
    } catch (error) {
      console.error('Error fetching my stats:', error);
      throw error;
    }
  },

  fetchTopPlayers: async (period = 'week', limit = 10) => {
    try {
      const response = await api.get('/leaderboard/top/', {
        params: { period, limit }
      });

      let data = response.data;

      if (data && typeof data === 'object' && !Array.isArray(data)) {
        if (data.results && Array.isArray(data.results)) {
          data = data.results;
        } else if (data.leaderboard && Array.isArray(data.leaderboard)) {
          data = data.leaderboard;
        } else if (Array.isArray(data)) {
          return data;
        } else {
          data = Object.values(data);
        }
      }

      return Array.isArray(data) ? data : [];
    } catch (error) {
      console.error('Error fetching top players:', error);
      throw error;
    }
  },

  getRankColor: (rank) => {
    if (rank === 1) return '#FFD700';
    if (rank === 2) return '#C0C0C0';
    if (rank === 3) return '#CD7F32';
    if (rank <= 10) return '#8A2BE2';
    if (rank <= 50) return '#9370DB';
    return '#BA55D3';
  },

  getPlayerLevel: (points) => {
    if (points >= 10000) return { level: 'Легенда', color: '#FF4500' };
    if (points >= 5000) return { level: 'Мастер', color: '#9370DB' };
    if (points >= 2000) return { level: 'Эксперт', color: '#32CD32' };
    if (points >= 1000) return { level: 'Продвинутый', color: '#1E90FF' };
    if (points >= 500) return { level: 'Средний', color: '#FFD700' };
    if (points >= 100) return { level: 'Начинающий', color: '#87CEEB' };
    return { level: 'Новичок', color: '#98FB98' };
  },

  calculateAccuracy: (correctAnswers, totalQuestions) => {
    if (!totalQuestions || totalQuestions === 0) return 0;
    return Math.round((correctAnswers / totalQuestions) * 100);
  }
};

export default leaderboardAPI;