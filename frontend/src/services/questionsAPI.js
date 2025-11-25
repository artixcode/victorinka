import api from './api';

export const questionsAPI = {
    getQuestions: () => api.get('/questions/'),
    createQuestion: (data) => api.post('/questions/', data),
    getQuestion: (id) => api.get(`/questions/${id}/`),
    updateQuestion: (id, data) => api.put(`/questions/${id}/`, data),
    patchQuestion: (id, data) => api.patch(`/questions/${id}/`, data),
    deleteQuestion: (id) => api.delete(`/questions/${id}/`),
};

export default questionsAPI;