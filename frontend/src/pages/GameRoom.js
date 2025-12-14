// src/pages/GameRoom.js
import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import styles from '../styles/GameRoom.module.css';

const GameRoom = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();

  const [roomId, setRoomId] = useState('');
  const [roomName, setRoomName] = useState('');
  const [userId, setUserId] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const [players, setPlayers] = useState([]);
  const [chatMessages, setChatMessages] = useState([]);
  const [roomData, setRoomData] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [timer, setTimer] = useState({ remaining: 0, total: 30 });
  const [gameStatus, setGameStatus] = useState('waiting');
  const [answered, setAnswered] = useState(false);
  const [questionStartTime, setQuestionStartTime] = useState(null);

  const socketRef = useRef(null);

  useEffect(() => {
    const storedRoomId = localStorage.getItem('gameRoomId');
    const storedRoomName = localStorage.getItem('gameRoomName');
    const storedSessionId = localStorage.getItem('gameSessionId');

    try {
      const userStr = localStorage.getItem('user');
      if (userStr) {
        const user = JSON.parse(userStr);
        setUserId(user.id || 0);
      }
    } catch (error) {
      console.error('Ошибка получения user:', error);
    }

    if (!storedRoomId) {
      navigate('/rooms');
      return;
    }

    setRoomId(storedRoomId);
    setRoomName(storedRoomName || `Комната ${storedRoomId}`);
  }, [navigate]);

  useEffect(() => {
    if (!roomId) return;

    const token = localStorage.getItem('access_token');
    if (!token) {
      alert('Требуется авторизация');
      navigate('/login');
      return;
    }

    const wsUrl = `ws://localhost/ws/room/${roomId}/?token=${token}`;

    try {
      const socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        setIsConnected(true);
        setChatMessages(prev => [...prev, {
          username: 'Система',
          message: 'Подключение к игре установлено',
          timestamp: new Date().toISOString()
        }]);
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('WebSocket received:', data.type, data);

          switch(data.type) {
            case 'room_state':
              setRoomData(data.data);
              setPlayers(data.data.players || []);
              if (data.data.recent_messages) {
                setChatMessages(data.data.recent_messages);
              }
              if (data.data.game_session) {
                const session = data.data.game_session;
                if (session.status === 'playing') {
                  setGameStatus('playing');
                  if (data.data.current_question) {
                    setCurrentQuestion(data.data.current_question);
                    setTimer({
                      remaining: data.data.current_question.time_limit || 30,
                      total: data.data.current_question.time_limit || 30
                    });
                  }
                } else if (session.status === 'waiting') {
                  setGameStatus('waiting');
                } else if (session.status === 'finished') {
                  setGameStatus('finished');
                }
              }
              break;

            case 'player_joined':
              console.log('Player joined event:', data.data);
              setPlayers(prev => {
                const exists = prev.some(p => p.user_id === data.data.user_id);
                if (!exists) {
                  return [...prev, {
                    user_id: data.data.user_id,
                    username: data.data.username,
                    is_host: data.data.is_host
                  }];
                }
                return prev;
              });

              setChatMessages(prev => [...prev, {
                username: 'Система',
                message: `${data.data.username} присоединился к комнате`,
                timestamp: new Date().toISOString()
              }]);
              break;

            case 'player_left':
              setPlayers(prev => prev.filter(p => p.user_id !== data.data.user_id));
              setChatMessages(prev => [...prev, {
                username: 'Система',
                message: `${data.data.username} покинул комнату`,
                timestamp: new Date().toISOString()
              }]);
              break;

            case 'chat_message':
              setChatMessages(prev => [...prev, {
                user_id: data.data.user_id,
                username: data.data.username,
                message: data.data.message,
                timestamp: data.data.timestamp || new Date().toISOString()
              }]);
              break;

            case 'game_started':
              setGameStatus('playing');
              const gameData = data.data || data;
              setChatMessages(prev => [...prev, {
                username: 'Система',
                message: `🎮 Игра началась! Викторина: ${gameData.quiz_title || 'Неизвестно'}`,
                timestamp: new Date().toISOString()
              }]);
              break;

            case 'question_revealed':
              const questionData = data.data || data;
              setCurrentQuestion({
                round_number: questionData.round_number,
                question_id: questionData.question_id,
                question_text: questionData.question_text,
                options: questionData.options,
                time_limit: questionData.time_limit || 30,
                points: questionData.points,
                difficulty: questionData.difficulty
              });
              setGameStatus('playing');
              setAnswered(false);
              setQuestionStartTime(Date.now());
              const timeLimit = questionData.time_limit || 30;
              setTimer({
                remaining: timeLimit,
                total: timeLimit
              });
              break;

            case 'timer_update':
              setTimer({
                remaining: data.remaining_seconds,
                total: data.total_seconds
              });
              break;

            case 'new_question':
              setCurrentQuestion({
                round_number: data.round_number,
                question_id: data.question_id,
                question_text: data.question_text,
                options: data.options,
                total_questions: data.total_questions,
                time_limit: data.timer_duration || 30
              });
              setGameStatus('playing');
              setAnswered(false);
              setQuestionStartTime(Date.now());
              setTimer({
                remaining: data.timer_duration || 30,
                total: data.timer_duration || 30
              });
              break;

            case 'round_ended':
              setChatMessages(prev => [...prev, {
                username: 'Система',
                message: data.message || 'Время вышло!',
                timestamp: new Date().toISOString()
              }]);
              break;

            case 'answer_submitted':
              break;

            case 'answer_checked':
              const answerData = data.data || data;
              if (answerData.user_id === userId) {
                const resultMsg = answerData.is_correct
                  ? `✅ Правильно! +${answerData.points_earned || 0} очков`
                  : '❌ Неправильно';
                setChatMessages(prev => [...prev, {
                  username: 'Система',
                  message: resultMsg,
                  timestamp: new Date().toISOString()
                }]);
              }
              break;

            case 'round_completed':
              setCurrentQuestion(null);
              setAnswered(false);
              setQuestionStartTime(null);
              const roundData = data.data || data;
              setChatMessages(prev => [...prev, {
                username: 'Система',
                message: `Раунд ${roundData.round_number || ''} завершен! Следующий вопрос...`,
                timestamp: new Date().toISOString()
              }]);
              break;

            case 'game_finished':
              setGameStatus('finished');
              setCurrentQuestion(null);
              setTimer({ remaining: 0, total: 30 });
              setChatMessages(prev => [...prev, {
                username: 'Система',
                message: data.message || '🏆 Игра завершена! Спасибо за участие!',
                timestamp: new Date().toISOString()
              }]);

              setTimeout(() => {
                alert('Игра завершена! Посмотрите результаты в лидерборде.');
              }, 500);
              break;

            case 'game_paused':
              setGameStatus('paused');
              break;

            case 'game_resumed':
              setGameStatus('playing');
              break;

            case 'error':
              alert(`Ошибка: ${data.message}`);
              break;
          }

        } catch (error) {
          console.error('Ошибка парсинга сообщения:', error);
        }
      };

      socket.onerror = (error) => {
        console.error('Ошибка WebSocket:', error);
        setChatMessages(prev => [...prev, {
          username: 'Система',
          message: 'Ошибка соединения',
          timestamp: new Date().toISOString()
        }]);
      };

      socket.onclose = (event) => {
        setIsConnected(false);
        setChatMessages(prev => [...prev, {
          username: 'Система',
          message: 'Соединение разорвано',
          timestamp: new Date().toISOString()
        }]);
      };

      socketRef.current = socket;

    } catch (error) {
      console.error('Ошибка создания WebSocket:', error);
    }

    return () => {
      if (socketRef.current?.readyState === WebSocket.OPEN) {
        socketRef.current.close();
      }
    };
  }, [roomId, navigate, userId]);

  const sendWebSocketMessage = (type, data = {}) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type, ...data }));
      return true;
    } else {
      console.error('WebSocket не подключен');
      return false;
    }
  };

  const handleSubmitAnswer = async (answerOptionId) => {
    if (!currentQuestion || answered || !questionStartTime) return;

    try {
      setAnswered(true);
      const timeTaken = (Date.now() - questionStartTime) / 1000;

      const success = sendWebSocketMessage('submit_answer', {
        answer_option_id: answerOptionId,
        time_taken: timeTaken
      });

      if (!success) {
        alert('Не удалось отправить ответ. Проверьте соединение.');
        setAnswered(false);
      }

    } catch (error) {
      console.error('Ошибка отправки ответа:', error);
      setAnswered(false);
    }
  };

  const handleSendChatMessage = (message) => {
    if (!message.trim()) return;
    sendWebSocketMessage('chat_message', { message });
  };

  const handleGetState = () => {
    sendWebSocketMessage('get_state');
  };

  const handleStartGame = () => {
    const selectedQuizId = localStorage.getItem('selectedQuizId');
    if (!selectedQuizId) {
      alert('Сначала выберите викторину в настройках комнаты');
      return;
    }

    if (confirm('Начать игру?')) {
      sendWebSocketMessage('start_game');
    }
  };

  const handlePauseGame = () => {
    sendWebSocketMessage(gameStatus === 'playing' ? 'pause_game' : 'resume_game');
  };

  const isHost = roomData?.host_id === userId;

  if (!roomId) {
    return (
      <div className={styles.pageContainer}>
        <Header />
        <main className={styles.main}>
          <div className={styles.errorContainer}>
            <h2>Ошибка загрузки комнаты</h2>
            <p>Пожалуйста, вернитесь в список комнат и присоединитесь к игре.</p>
            <button
              onClick={() => navigate('/rooms')}
              className={styles.returnButton}
            >
              Вернуться к комнатам
            </button>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className={styles.pageContainer}>
      <Header />
      <main className={styles.main}>
        <div className={styles.roomHeader}>
          <div className={styles.headerContent}>
            <h1>{roomName}</h1>
            <div className={styles.roomInfo}>
              <div><strong>ID комнаты:</strong> {roomId}</div>
              <div><strong>Статус:</strong>
                <span className={isConnected ? styles.statusConnected : styles.statusDisconnected}>
                  {isConnected ? '✅ ПОДКЛЮЧЕНО' : '❌ ОТКЛЮЧЕНО'}
                </span>
              </div>
              <div><strong>Вы:</strong> {isHost ? '👑 Хост' : 'Игрок'}</div>
            </div>
          </div>

          <button
            onClick={() => {
              localStorage.removeItem('gameRoomId');
              localStorage.removeItem('gameRoomName');
              localStorage.removeItem('gameSessionId');
              localStorage.removeItem('selectedQuizId');
              navigate('/rooms');
            }}
            className={styles.exitButton}
          >
            Выйти
          </button>
        </div>

        <div className={styles.controlsPanel}>
          <button
            onClick={handleGetState}
            disabled={!isConnected}
            className={`${styles.controlButton} ${!isConnected ? styles.disabled : ''}`}
          >
            Обновить состояние
          </button>

          {isHost && gameStatus === 'waiting' && (
            <button
              onClick={handleStartGame}
              disabled={!isConnected}
              className={`${styles.controlButton} ${styles.startButton} ${!isConnected ? styles.disabled : ''}`}
            >
              🎮 Начать игру
            </button>
          )}

          {isHost && (gameStatus === 'playing' || gameStatus === 'paused') && (
            <button
              onClick={handlePauseGame}
              disabled={!isConnected}
              className={`${styles.controlButton} ${styles.pauseButton} ${!isConnected ? styles.disabled : ''}`}
            >
              {gameStatus === 'playing' ? '⏸️ Пауза' : '▶️ Продолжить'}
            </button>
          )}
        </div>

        <div className={styles.gameContent}>
          <div className={styles.gameArea}>
            {(gameStatus === 'playing' || gameStatus === 'paused') && (
              <div className={`${styles.timer} ${gameStatus === 'paused' ? styles.timerPaused : timer.remaining <= 10 ? styles.timerCritical : styles.timerNormal}`}>
                <div className={styles.timerValue}>
                  {gameStatus === 'paused' ? '⏸️' : '⏱️'} {timer.remaining} сек
                </div>
                <div className={styles.timerBar}>
                  <div
                    className={styles.timerProgress}
                    style={{ width: `${(timer.remaining / timer.total) * 100}%` }}
                  />
                </div>
                <div className={styles.timerLabel}>
                  {gameStatus === 'paused' ? 'Игра на паузе' : `Раунд ${currentQuestion?.round_number || 1}`}
                </div>
              </div>
            )}

            {currentQuestion ? (
              <div className={styles.questionSection}>
                <h2>Вопрос #{currentQuestion.round_number}</h2>
                <div className={styles.questionText}>
                  {currentQuestion.question_text}
                </div>

                <div className={styles.optionsGrid}>
                  {currentQuestion.options?.map((option, index) => (
                    <button
                      key={option.id}
                      onClick={() => handleSubmitAnswer(option.id)}
                      disabled={answered}
                      className={styles.optionButton}
                    >
                      <div className={styles.optionIndex}>
                        {String.fromCharCode(65 + index)}
                      </div>
                      <div className={styles.optionText}>{option.text}</div>
                    </button>
                  ))}
                </div>

                {answered && (
                  <div className={styles.answerSubmitted}>
                    ✅ Ответ отправлен!
                  </div>
                )}
              </div>
            ) : (
              <div className={styles.waitingSection}>
                <h2>
                  {gameStatus === 'waiting' ? 'Ожидание начала игры...' :
                   gameStatus === 'finished' ? '🏆 Игра завершена!' :
                   'Между раундами...'}
                </h2>
                {gameStatus === 'waiting' && isHost && (
                  <p>Нажмите "Начать игру", когда все участники готовы</p>
                )}
                {gameStatus === 'waiting' && !isHost && (
                  <p>Ведущий скоро начнет игру...</p>
                )}
                {gameStatus === 'finished' && (
                  <div className={styles.finishedActions}>
                    <p>
                      Спасибо за участие! Посмотрите результаты в лидерборде.
                    </p>
                    <div className={styles.actionButtons}>
                      <button
                        onClick={() => navigate(`/room/${roomId}`)}
                        className={styles.actionButton}
                      >
                        🚪 Вернуться к комнате
                      </button>
                      <button
                        onClick={() => navigate('/leaderboard')}
                        className={styles.actionButton}
                      >
                        🏆 Лидерборд
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className={styles.sidebar}>
            <div className={styles.playersPanel}>
              <h3>👥 Игроки ({players.length})</h3>
              <div className={styles.playersList}>
                {players.map(player => (
                  <div
                    key={player.user_id}
                    className={`${styles.playerItem} ${player.user_id === userId ? styles.currentPlayer : ''}`}
                  >
                    <span>{player.username}</span>
                    <div className={styles.playerTags}>
                      {player.user_id === userId && (
                        <span className={styles.youTag}>Вы</span>
                      )}
                      {player.is_host && (
                        <span className={styles.hostTag}>👑 Хост</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className={styles.chatPanel}>
              <h3>💬 Чат</h3>
              <div className={styles.chatMessages}>
                {chatMessages.map((msg, index) => (
                  <div
                    key={index}
                    className={`${styles.chatMessage} ${msg.user_id === userId ? styles.ownMessage : ''}`}
                  >
                    <div className={styles.chatHeader}>
                      <strong>{msg.username}</strong>
                      <small>
                        {msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString() : ''}
                      </small>
                    </div>
                    <div>{msg.message}</div>
                  </div>
                ))}
              </div>
              <div className={styles.chatInput}>
                <input
                  type="text"
                  placeholder="Введите сообщение..."
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && e.target.value.trim()) {
                      handleSendChatMessage(e.target.value.trim());
                      e.target.value = '';
                    }
                  }}
                />
                <button
                  onClick={() => {
                    const input = document.querySelector(`.${styles.chatInput} input`);
                    if (input.value.trim()) {
                      handleSendChatMessage(input.value.trim());
                      input.value = '';
                    }
                  }}
                >
                  Отправить
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default GameRoom;