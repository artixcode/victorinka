// src/pages/GameRoom.js
import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';

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

          switch(data.type) {
            case 'room_state':
              setRoomData(data.data);
              setPlayers(data.data.players || []);
              if (data.data.recent_messages) {
                setChatMessages(data.data.recent_messages);
              }
              break;

            case 'player_joined':
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
              break;

            case 'player_left':
              setPlayers(prev => prev.filter(p => p.user_id !== data.data.user_id));
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
              break;

            case 'question_revealed':
              setCurrentQuestion(data.data);
              setGameStatus('playing');
              setAnswered(false);
              setQuestionStartTime(Date.now());
              if (data.data.time_limit) {
                setTimer({
                  remaining: data.data.time_limit,
                  total: data.data.time_limit
                });
              }
              break;

            case 'timer_update':
              setTimer({
                remaining: data.remaining_seconds,
                total: data.total_seconds
              });
              break;

            case 'answer_submitted':
              break;

            case 'answer_checked':
              if (data.data.user_id === userId) {
                alert(data.data.is_correct ? '✅ Правильно!' : '❌ Неправильно');
              }
              break;

            case 'round_completed':
              setCurrentQuestion(null);
              setAnswered(false);
              setQuestionStartTime(null);
              break;

            case 'game_finished':
              setGameStatus('finished');
              alert('Игра завершена!');
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
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <Header />
        <main style={{ flex: 1, padding: '20px', textAlign: 'center' }}>
          <h2>Ошибка загрузки комнаты</h2>
          <p>Пожалуйста, вернитесь в список комнат и присоединитесь к игре.</p>
          <button
            onClick={() => navigate('/rooms')}
            style={{
              padding: '10px 20px',
              background: '#667eea',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer',
              marginTop: '20px'
            }}
          >
            Вернуться к комнатам
          </button>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    }}>
      <Header />
      <main style={{
        flex: 1,
        padding: '20px',
        maxWidth: '1400px',
        margin: '0 auto',
        width: '100%'
      }}>
        <div style={{
          background: 'white',
          borderRadius: '10px',
          padding: '20px',
          marginBottom: '20px',
          boxShadow: '0 10px 40px rgba(0,0,0,0.1)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h1 style={{ margin: '0 0 10px 0', color: '#333' }}>{roomName}</h1>
              <div style={{ display: 'flex', gap: '20px', color: '#666' }}>
                <div><strong>ID комнаты:</strong> {roomId}</div>
                <div><strong>Статус:</strong>
                  <span style={{
                    color: isConnected ? '#2e7d32' : '#c62828',
                    fontWeight: 'bold',
                    marginLeft: '10px'
                  }}>
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
              style={{
                padding: '10px 20px',
                background: '#6c757d',
                color: 'white',
                border: 'none',
                borderRadius: '5px',
                cursor: 'pointer'
              }}
            >
              Выйти
            </button>
          </div>

          <div style={{
            display: 'flex',
            gap: '10px',
            marginTop: '20px',
            padding: '15px',
            background: '#f8f9fa',
            borderRadius: '5px'
          }}>
            <button
              onClick={handleGetState}
              disabled={!isConnected}
              style={{
                padding: '8px 16px',
                background: isConnected ? '#2196f3' : '#b0bec5',
                color: 'white',
                border: 'none',
                borderRadius: '5px',
                cursor: isConnected ? 'pointer' : 'not-allowed'
              }}
            >
              Обновить состояние
            </button>

            {isHost && gameStatus === 'waiting' && (
              <button
                onClick={handleStartGame}
                disabled={!isConnected}
                style={{
                  padding: '8px 16px',
                  background: isConnected ? '#4caf50' : '#b0bec5',
                  color: 'white',
                  border: 'none',
                  borderRadius: '5px',
                  cursor: isConnected ? 'pointer' : 'not-allowed'
                }}
              >
                🎮 Начать игру
              </button>
            )}

            {isHost && (gameStatus === 'playing' || gameStatus === 'paused') && (
              <button
                onClick={handlePauseGame}
                disabled={!isConnected}
                style={{
                  padding: '8px 16px',
                  background: isConnected ? '#ff9800' : '#b0bec5',
                  color: 'white',
                  border: 'none',
                  borderRadius: '5px',
                  cursor: isConnected ? 'pointer' : 'not-allowed'
                }}
              >
                {gameStatus === 'playing' ? '⏸️ Пауза' : '▶️ Продолжить'}
              </button>
            )}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '20px' }}>
          <div style={{
            flex: 3,
            background: 'white',
            borderRadius: '10px',
            padding: '20px',
            boxShadow: '0 10px 40px rgba(0,0,0,0.1)'
          }}>
            {(gameStatus === 'playing' || gameStatus === 'paused') && (
              <div style={{
                background: gameStatus === 'paused' ?
                  'linear-gradient(135deg, #9e9e9e 0%, #616161 100%)' :
                  timer.remaining <= 10 ?
                  'linear-gradient(135deg, #f5576c 0%, #d32f2f 100%)' :
                  'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                borderRadius: '10px',
                padding: '20px',
                color: 'white',
                textAlign: 'center',
                marginBottom: '20px'
              }}>
                <div style={{ fontSize: '48px', fontWeight: 'bold', marginBottom: '10px' }}>
                  {gameStatus === 'paused' ? '⏸️' : '⏱️'} {timer.remaining} сек
                </div>
                <div style={{
                  background: 'rgba(255,255,255,0.3)',
                  height: '20px',
                  borderRadius: '10px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    height: '100%',
                    background: 'white',
                    width: `${(timer.remaining / timer.total) * 100}%`,
                    transition: 'width 1s linear'
                  }} />
                </div>
                <div style={{ marginTop: '10px', fontSize: '14px' }}>
                  {gameStatus === 'paused' ? 'Игра на паузе' : `Раунд ${currentQuestion?.round_number || 1}`}
                </div>
              </div>
            )}

            {currentQuestion ? (
              <div>
                <h2 style={{ color: '#333' }}>Вопрос #{currentQuestion.round_number}</h2>
                <p style={{
                  fontSize: '20px',
                  margin: '20px 0',
                  lineHeight: '1.5',
                  padding: '15px',
                  background: '#f8f9fa',
                  borderRadius: '8px'
                }}>
                  {currentQuestion.question_text}
                </p>

                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(2, 1fr)',
                  gap: '15px',
                  marginTop: '30px'
                }}>
                  {currentQuestion.options?.map((option, index) => (
                    <button
                      key={option.id}
                      onClick={() => handleSubmitAnswer(option.id)}
                      disabled={answered}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        padding: '15px',
                        border: `2px solid ${answered ? '#ddd' : '#667eea'}`,
                        borderRadius: '8px',
                        background: 'white',
                        cursor: answered ? 'not-allowed' : 'pointer',
                        textAlign: 'left',
                        transition: 'all 0.2s',
                        opacity: answered ? 0.7 : 1
                      }}
                      onMouseEnter={(e) => {
                        if (!answered) e.currentTarget.style.transform = 'translateY(-2px)';
                      }}
                      onMouseLeave={(e) => {
                        if (!answered) e.currentTarget.style.transform = 'translateY(0)';
                      }}
                    >
                      <div style={{
                        width: '30px',
                        height: '30px',
                        background: '#667eea',
                        color: 'white',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        marginRight: '15px',
                        fontWeight: 'bold',
                        flexShrink: 0
                      }}>
                        {String.fromCharCode(65 + index)}
                      </div>
                      <span style={{ flex: 1 }}>{option.text}</span>
                    </button>
                  ))}
                </div>

                {answered && (
                  <div style={{
                    marginTop: '20px',
                    padding: '15px',
                    background: '#e8f5e9',
                    borderRadius: '8px',
                    textAlign: 'center',
                    color: '#2e7d32',
                    fontWeight: 'bold'
                  }}>
                    ✅ Ответ отправлен!
                  </div>
                )}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '40px 20px' }}>
                <h2 style={{ color: '#666' }}>
                  {gameStatus === 'waiting' ? 'Ожидание начала игры...' :
                   gameStatus === 'finished' ? 'Игра завершена!' :
                   'Между раундами...'}
                </h2>
                {gameStatus === 'waiting' && isHost && (
                  <p>Нажмите "Начать игру", когда все участники готовы</p>
                )}
                {gameStatus === 'waiting' && !isHost && (
                  <p>Ведущий скоро начнет игру...</p>
                )}
              </div>
            )}
          </div>

          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div style={{
              background: 'white',
              borderRadius: '10px',
              padding: '20px',
              boxShadow: '0 10px 40px rgba(0,0,0,0.1)'
            }}>
              <h3 style={{ margin: '0 0 15px 0', color: '#333' }}>
                👥 Игроки ({players.length})
              </h3>
              <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                {players.map(player => (
                  <div
                    key={player.user_id}
                    style={{
                      padding: '10px',
                      marginBottom: '8px',
                      background: player.user_id === userId ? '#e3f2fd' : '#f8f9fa',
                      borderRadius: '8px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      borderLeft: `4px solid ${player.is_host ? '#ffd700' : '#4caf50'}`
                    }}
                  >
                    <span style={{ fontWeight: player.user_id === userId ? 'bold' : 'normal' }}>
                      {player.username}
                    </span>
                    <div style={{ display: 'flex', gap: '5px' }}>
                      {player.user_id === userId && (
                        <span style={{
                          background: '#4caf50',
                          color: 'white',
                          padding: '2px 8px',
                          borderRadius: '10px',
                          fontSize: '12px'
                        }}>
                          Вы
                        </span>
                      )}
                      {player.is_host && (
                        <span style={{
                          background: '#ffd700',
                          color: '#333',
                          padding: '2px 8px',
                          borderRadius: '10px',
                          fontSize: '12px'
                        }}>
                          👑 Хост
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div style={{
              background: 'white',
              borderRadius: '10px',
              padding: '20px',
              boxShadow: '0 10px 40px rgba(0,0,0,0.1)',
              display: 'flex',
              flexDirection: 'column',
              height: '400px'
            }}>
              <h3 style={{ margin: '0 0 15px 0', color: '#333' }}>💬 Чат</h3>

              <div style={{
                flex: 1,
                overflowY: 'auto',
                marginBottom: '15px',
                padding: '10px',
                background: '#f9f9f9',
                borderRadius: '5px'
              }}>
                {chatMessages.map((msg, index) => (
                  <div
                    key={index}
                    style={{
                      marginBottom: '10px',
                      padding: '8px',
                      background: msg.user_id === userId ? '#e8f5e9' : 'white',
                      borderRadius: '5px',
                      borderLeft: `3px solid ${msg.username === 'Система' ? '#9c27b0' : '#667eea'}`
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <strong style={{ color: msg.username === 'Система' ? '#9c27b0' : '#333' }}>
                        {msg.username}
                      </strong>
                      <small style={{ color: '#666' }}>
                        {msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString() : ''}
                      </small>
                    </div>
                    <div style={{ marginTop: '5px' }}>{msg.message}</div>
                  </div>
                ))}
              </div>

              <div style={{ display: 'flex' }}>
                <input
                  type="text"
                  placeholder="Введите сообщение..."
                  style={{
                    flex: 1,
                    padding: '10px',
                    border: '1px solid #ddd',
                    borderRadius: '5px 0 0 5px',
                    fontSize: '14px'
                  }}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && e.target.value.trim()) {
                      handleSendChatMessage(e.target.value.trim());
                      e.target.value = '';
                    }
                  }}
                />
                <button
                  onClick={() => {
                    const input = document.querySelector('input[type="text"]');
                    if (input.value.trim()) {
                      handleSendChatMessage(input.value.trim());
                      input.value = '';
                    }
                  }}
                  style={{
                    padding: '10px 20px',
                    background: '#667eea',
                    color: 'white',
                    border: 'none',
                    borderRadius: '0 5px 5px 0',
                    cursor: 'pointer'
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