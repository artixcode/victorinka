import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import roomsAPI from '../services/roomsAPI';
import styles from '../styles/RoomDetail.module.css';

const RoomDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [room, setRoom] = useState(null);
  const [loading, setLoading] = useState(true);
  const [participants, setParticipants] = useState([]);
  const [isChangingStatus, setIsChangingStatus] = useState(false);
  const [isStartingGame, setIsStartingGame] = useState(false);

  useEffect(() => {
    loadRoom();
  }, [id]);

  const loadRoom = async () => {
    try {
      setLoading(true);
      const response = await roomsAPI.getRoom(id);
      setRoom(response.data);
      loadParticipants();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadParticipants = async () => {
    try {
      const response = await roomsAPI.getRoom(id);
      setParticipants(response.data.participants || []);
    } catch (err) {
      console.error(err);
    }
  };

  const handleChangeStatus = async (newStatus) => {
    if (!window.confirm('Изменить статус?')) return;

    try {
      setIsChangingStatus(true);
      const response = await roomsAPI.updateRoom(id, { status: newStatus });
      setRoom(response.data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsChangingStatus(false);
    }
  };

  const handleStartGame = async () => {
    if (!window.confirm('Начать викторину?')) return;

    try {
      setIsStartingGame(true);
      const response = await roomsAPI.startGame(id);
      if (response.data.game_session_id) {
        navigate(`/game/${response.data.game_session_id}`);
      }
    } catch (err) {
      console.error(err);
      alert(err.response?.data?.detail || 'Ошибка запуска игры');
    } finally {
      setIsStartingGame(false);
    }
  };

  const handleDeleteRoom = async () => {
    if (!window.confirm('Удалить комнату?')) return;

    try {
      await roomsAPI.deleteRoom(id);
      navigate('/rooms');
    } catch (err) {
      console.error(err);
    }
  };

  const handleLeaveRoom = async () => {
    if (!window.confirm('Выйти из комнаты?')) return;

    try {
      await roomsAPI.leaveRoom(id);
      navigate('/rooms');
    } catch (err) {
      console.error(err);
    }
  };

  const getStatusText = (status) => {
    const statusMap = {
      'draft': 'Черновик',
      'open': 'Открыта',
      'in_progress': 'Идёт',
      'finished': 'Завершена'
    };
    return statusMap[status] || status;
  };

  const getStatusClass = (status) => {
    const classMap = {
      'draft': styles.statusDraft,
      'open': styles.statusOpen,
      'in_progress': styles.statusInProgress,
      'finished': styles.statusFinished
    };
    return classMap[status] || styles.statusDraft;
  };

  if (loading) {
    return (
      <div className={styles.pageContainer}>
        <Header />
        <main className={styles.main}>
          <div className={styles.loading}>
            <p>Загрузка...</p>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  if (!room) {
    return (
      <div className={styles.pageContainer}>
        <Header />
        <main className={styles.main}>
          <div className={styles.error}>
            Комната не найдена
            <Link to="/rooms" className={styles.errorLink}>Назад</Link>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  const userId = parseInt(localStorage.getItem('userId') || '0');
  const isHost = room.host_id === userId;

  return (
    <div className={styles.pageContainer}>
      <Header />
      <main className={styles.main}>
        <div className={styles.headerContainer}>
          <div className={styles.titleWrapper}>
            <h1 className={styles.roomTitle}>{room.name}</h1>
            <span className={`${styles.statusBadge} ${getStatusClass(room.status)}`}>
              {getStatusText(room.status)}
            </span>
            {isHost && <span className={styles.hostBadge}>Хост</span>}
          </div>
          <Link to="/rooms" className={styles.backButton}>
            ← Назад
          </Link>
        </div>

        <div className={styles.roomCard}>
          <div className={styles.roomInfo}>
            <p><span className={styles.infoLabel}>Код:</span> <span className={styles.inviteCode}>{room.invite_code}</span></p>
            <p><span className={styles.infoLabel}>Создана:</span> {new Date(room.created_at).toLocaleString('ru-RU')}</p>
            <p><span className={styles.infoLabel}>Игроков:</span> {participants.length}</p>
          </div>

          {isHost && (
            <div className={styles.manageSection}>
              <h3>Управление</h3>
              <div className={styles.controlButtons}>
                {room.status === 'draft' && (
                  <button
                    className={`${styles.controlButton} ${styles.controlOpen}`}
                    onClick={() => handleChangeStatus('open')}
                    disabled={isChangingStatus}
                  >
                    Открыть
                  </button>
                )}
                {(room.status === 'open' || participants.length >= 1) && (
                  <button
                    className={`${styles.controlButton} ${styles.controlStart}`}
                    onClick={handleStartGame}
                    disabled={isStartingGame || isChangingStatus}
                  >
                    {isStartingGame ? '...' : 'Начать викторину'}
                  </button>
                )}
                {(room.status === 'in_progress' || room.status === 'open') && (
                  <button
                    className={`${styles.controlButton} ${styles.controlFinish}`}
                    onClick={() => handleChangeStatus('finished')}
                    disabled={isChangingStatus}
                  >
                    Завершить
                  </button>
                )}
                {room.status === 'finished' && (
                  <button
                    className={`${styles.controlButton} ${styles.controlReopen}`}
                    onClick={() => handleChangeStatus('open')}
                    disabled={isChangingStatus}
                  >
                    Открыть
                  </button>
                )}
              </div>
            </div>
          )}

          <div className={styles.participantsSection}>
            <h3>Участники ({participants.length})</h3>
            {participants.length > 0 ? (
              <div className={styles.participantsList}>
                {participants.map(p => (
                  <div key={p.id} className={styles.participantItem}>
                    <span>{p.username || `Пользователь #${p.user_id}`}</span>
                    {p.is_host && <span className={styles.hostBadge}>Хост</span>}
                  </div>
                ))}
              </div>
            ) : (
              <p>Нет участников</p>
            )}
          </div>

          <div className={styles.actionsSection}>
            <h3>Действия</h3>
            <div className={styles.roomActions}>
              {!isHost ? (
                <button
                  className={`${styles.actionButton} ${styles.leaveButton}`}
                  onClick={handleLeaveRoom}
                >
                  Выйти
                </button>
              ) : (
                <button
                  className={`${styles.actionButton} ${styles.deleteButton}`}
                  onClick={handleDeleteRoom}
                >
                  Удалить
                </button>
              )}

              <button
                className={`${styles.actionButton} ${styles.copyButton}`}
                onClick={() => {
                  navigator.clipboard.writeText(room.invite_code);
                  alert('Код скопирован');
                }}
              >
                Скопировать код
              </button>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default RoomDetail;