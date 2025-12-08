import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Quizzes from './pages/Quizzes';
import Leaderboard from './pages/Leaderboard';
import Rooms from './pages/Rooms';
import RoomDetail from './pages/RoomDetail';
import Profile from './pages/Profile';
import CreateQuiz from './pages/CreateQuiz';
import MyQuizzes from './pages/MyQuizzes';
import QuizView from './pages/QuizView';
import EditQuiz from './pages/EditQuiz';

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
          <Route path="/rooms" element={<Rooms />} />
          <Route path="/room/:id" element={<RoomDetail />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/create-quiz" element={<CreateQuiz />} />
          <Route path="/my-quizzes" element={<MyQuizzes />} />
          <Route path="/quiz/:id" element={<QuizView />} />
          <Route path="/edit-quiz/:id" element={<EditQuiz />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;