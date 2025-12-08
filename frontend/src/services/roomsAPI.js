import api from './api';

const roomsAPI = {
  getMyRooms: () => api.get('/rooms/mine/'),

  createRoom: (name) => api.post('/rooms/', { name }),

  getRoom: (roomId) => api.get(`/rooms/${roomId}/`),

  updateRoom: (roomId, data) => api.patch(`/rooms/${roomId}/`, data),

  deleteRoom: (roomId) => api.delete(`/rooms/${roomId}/`),

  joinRoom: (roomId, inviteCode) => api.post(`/rooms/${roomId}/join/`, { invite_code: inviteCode }),

  leaveRoom: (roomId) => api.post(`/rooms/${roomId}/leave/`),

  startGame: (roomId) => api.post(`/game/rooms/${roomId}/start/`),

  findRoomByCode: (inviteCode) => api.get(`/rooms/find/?invite_code=${inviteCode}`),

};

export default roomsAPI;