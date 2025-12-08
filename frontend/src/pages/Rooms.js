import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import roomsAPI from '../services/roomsAPI';
import styles from '../styles/Rooms.module.css';

const Rooms = () => {
  const [rooms, setRooms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newRoomName, setNewRoomName] = useState('');
  const [inviteCode, setInviteCode] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [isJoining, setIsJoining] = useState(false);
  const [error, setError] = useState(null);
  const [joinError, setJoinError] = useState(null);

  useEffect(() => {
    loadRooms();
  }, []);

  const loadRooms = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await roomsAPI.getMyRooms();
      let roomsData = [];

      if (Array.isArray(response.data)) {
        roomsData = response.data;
      } else if (response.data && Array.isArray(response.data.results)) {
        roomsData = response.data.results;
      } else if (response.data && Array.isArray(response.data.rooms)) {
        roomsData = response.data.rooms;
      } else if (response.data && typeof response.data === 'object') {
        if (response.data.id) {
          roomsData = [response.data];
        } else {
          roomsData = [];
        }
      } else if (response.data === null || response.data === undefined) {
        roomsData = [];
      } else {
        roomsData = [];
      }

      setRooms(roomsData);

    } catch (err) {
      setError(err.message || 'Не удалось загрузить комнаты');
      setRooms([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRoom = async (e) => {
    e.preventDefault();
    if (!newRoomName.trim()) {
      setError('Введите название комнаты');
      return;
    }

    try {
      setIsCreating(true);
      setError(null);
      const response = await roomsAPI.createRoom(newRoomName.trim());
      setRooms(prevRooms => [response.data, ...prevRooms]);
      setNewRoomName('');
      setShowCreateModal(false);

    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Не удалось создать комнату');
    } finally {
      setIsCreating(false);
    }
  };

  const handleJoinRoom = async (e) => {
    e.preventDefault();
    if (!inviteCode.trim()) {
      setJoinError('Введите инвайт-код');
      return;
    }

    try {
      setIsJoining(true);
      setJoinError(null);
      const response = await roomsAPI.findRoomByCode(inviteCode.trim());

      if (response.data && response.data.id) {
        await roomsAPI.joinRoom(response.data.id, inviteCode.trim());
        setRooms(prevRooms => [response.data, ...prevRooms]);
        setInviteCode('');
      } else {
        setJoinError('Комната не найдена');
      }

    } catch (err) {
      setJoinError(err.response?.data?.detail || err.message || 'Не удалось присоединиться');
    } finally {
      setIsJoining(false);
    }
  };

  const handleLeaveRoom = async (roomId, roomName) => {
    if (!window.confirm(`Выйти из комнаты "${roomName}"?`)) return;

    try {
      setError(null);
      await roomsAPI.leaveRoom(roomId);
      setRooms(rooms.filter(room => room.id !== roomId));
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Не удалось выйти из комнаты');
    }
  };

  const handleDeleteRoom = async (roomId, roomName) => {
    if (!window.confirm(`Удалить комнату "${roomName}"?`)) return;

    try {
      setError(null);
      await roomsAPI.deleteRoom(roomId);
      setRooms(rooms.filter(room => room.id !== roomId));
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Не удалось удалить комнату');
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
  
  const getUserId = () => {
    try {
      const userStr = localStorage.getItem('user');
      if (!userStr) return 0;
      const user = JSON.parse(userStr);
      return user.id || 0;
    } catch {
      return 0;
    }
  };

  const userId = getUserId();

  const renderRooms = () => {
    if (!Array.isArray(rooms)) {
      return (
        <div className={styles.error}>
          <p>Ошибка: данные комнат в неверном формате</p>
          <button onClick={loadRooms} className={styles.retryButton}>
            Попробовать снова
          </button>
        </div>
      );
    }

    if (rooms.length === 0) {
      return (
        <div className={styles.emptyState}>
          <h3>Нет комнат</h3>
          <p>Создайте комнату или присоединитесь по коду</p>
          <button
            className={`${styles.createButton} ${styles.emptyCreateButton}`}
            onClick={() => setShowCreateModal(true)}
          >
            Создать комнату
          </button>
        </div>
      );
    }

    return (
      <div className={styles.roomsGrid}>
        {rooms.map(room => (
          <div key={room.id} className={styles.roomCard}>
            <div className={styles.roomHeader}>
              <h3 className={styles.roomName}>{room.name}</h3>
              <span className={`${styles.statusBadge} ${getStatusClass(room.status)}`}>
                {getStatusText(room.status)}
              </span>
            </div>

            <div className={styles.roomInfo}>
              <p>
                <span className={styles.infoLabel}>Код:</span>
                <span className={styles.inviteCode}>{room.invite_code}</span>
              </p>
              <p>
                <span className={styles.infoLabel}>Создана:</span>
                {room.created_at ? new Date(room.created_at).toLocaleDateString('ru-RU') : 'Н/Д'}
              </p>
              <p>
                <span className={styles.infoLabel}>Игроков:</span>
                {room.players_count || 0}
              </p>
              {room.host_id === userId && (
                <p>
                  <span className={styles.hostBadge}>Вы - хост</span>
                </p>
              )}
            </div>

            <div className={styles.roomActions}>
              <Link
                to={`/room/${room.id}`}
                className={`${styles.actionButton} ${styles.viewButton}`}
              >
                Открыть
              </Link>

              {room.host_id !== userId ? (
                <button
                  className={`${styles.actionButton} ${styles.leaveButton}`}
                  onClick={() => handleLeaveRoom(room.id, room.name)}
                >
                  Выйти
                </button>
              ) : (
                <button
                  className={`${styles.actionButton} ${styles.deleteButton}`}
                  onClick={() => handleDeleteRoom(room.id, room.name)}
                >
                  Удалить
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className={styles.pageContainer}>
      <Header />
      <main className={styles.main}>
        <div className={styles.headerContainer}>
          <h1>Мои комнаты</h1>
          <button
            className={styles.createButton}
            onClick={() => setShowCreateModal(true)}
          >
            + Создать комнату
          </button>
        </div>

        <section className={styles.joinSection}>
          <h2>Присоединиться к комнате</h2>
          <p>Введите инвайт-код для присоединения</p>
          {joinError && <div className={styles.error}>{joinError}</div>}
          <form className={styles.joinForm} onSubmit={handleJoinRoom}>
            <input
              type="text"
              placeholder="Инвайт-код"
              value={inviteCode}
              onChange={(e) => setInviteCode(e.target.value.toUpperCase())}
              maxLength="12"
              required
            />
            <button type="submit" disabled={isJoining}>
              {isJoining ? '...' : 'Присоединиться'}
            </button>
          </form>
        </section>

        {error && (
          <div className={styles.error}>
            <p>{error}</p>
            <button onClick={loadRooms} className={styles.retryButton}>
              Обновить
            </button>
          </div>
        )}

        {loading ? (
          <div className={styles.loading}>
            <p>Загрузка...</p>
          </div>
        ) : (
          renderRooms()
        )}
      </main>
      <Footer />

      {showCreateModal && (
        <div className={styles.modalOverlay}>
          <div className={styles.modal}>
            <h2>Создать комнату</h2>
            <form onSubmit={handleCreateRoom}>
              <div className={styles.formGroup}>
                <label htmlFor="roomName">Название</label>
                <input
                  id="roomName"
                  type="text"
                  value={newRoomName}
                  onChange={(e) => setNewRoomName(e.target.value)}
                  placeholder="Название комнаты"
                  required
                  autoFocus
                />
              </div>
              <div className={styles.formButtons}>
                <button
                  type="button"
                  className={styles.cancelButton}
                  onClick={() => setShowCreateModal(false)}
                  disabled={isCreating}
                >
                  Отмена
                </button>
                <button
                  type="submit"
                  className={styles.submitButton}
                  disabled={isCreating}
                >
                  {isCreating ? '...' : 'Создать'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Rooms;