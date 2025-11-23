// App.js
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Quizzes from './pages/Quizzes';
import Leaderboard from './pages/Leaderboard';
import CreateRoom from './pages/CreateRoom';
import Profile from './pages/Profile'; // Добавляем импорт

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/quizzes" element={<Quizzes />} />
          <Route path="/leaderboard" element={<Leaderboard />} />
          <Route path="/create-room" element={<CreateRoom />} />
          <Route path="/profile" element={<Profile />} /> {/* Добавляем маршрут */}
        </Routes>
      </div>
    </Router>
  );
}

export default App;