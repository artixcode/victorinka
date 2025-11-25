import api from './api';

export const quizzesAPI = {
  getPublicQuizzes: () => api.get('/quizzes/'),

  getMyQuizzes: () => api.get('/quizzes/mine/'),
  createQuiz: (data) => api.post('/quizzes/mine/', data),
  getMyQuiz: (id) => api.get(`/quizzes/mine/${id}/`),
  updateMyQuiz: (id, data) => api.put(`/quizzes/mine/${id}/`, data),
  patchMyQuiz: (id, data) => api.patch(`/quizzes/mine/${id}/`, data),
  deleteMyQuiz: (id) => api.delete(`/quizzes/mine/${id}/`),

  getQuiz: (id) => api.get(`/quizzes/${id}/`),
};

export default quizzesAPI;