import React, {useState, useEffect} from 'react';
import {useParams, useNavigate, Link} from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import roomsAPI from '../services/roomsAPI';
import quizzesAPI from '../services/quizzesAPI';
import styles from '../styles/RoomDetail.module.css';

const RoomDetail = () => {
    const {id} = useParams();
    const navigate = useNavigate();
    const [room, setRoom] = useState(null);
    const [loading, setLoading] = useState(true);
    const [participants, setParticipants] = useState([]);
    const [isChangingStatus, setIsChangingStatus] = useState(false);
    const [isStartingGame, setIsStartingGame] = useState(false);
    const [showQuizModal, setShowQuizModal] = useState(false);
    const [activeTab, setActiveTab] = useState('my');
    const [myQuizzes, setMyQuizzes] = useState([]);
    const [publicQuizzes, setPublicQuizzes] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedQuizId, setSelectedQuizId] = useState('');
    const [loadingMyQuizzes, setLoadingMyQuizzes] = useState(false);
    const [loadingPublicQuizzes, setLoadingPublicQuizzes] = useState(false);
    const [error, setError] = useState(null);

    const loadRoom = async (showLoading = true) => {
        try {
            if (showLoading) setLoading(true);
            setError(null);
            const response = await roomsAPI.getRoom(id);
            setRoom(response.data);
            setParticipants(response.data.participants || []);

            if (response.data.status === 'in_progress' || response.data.current_session_id) {
                const sessionId = response.data.current_session_id || id;
                localStorage.setItem('gameRoomId', id);
                localStorage.setItem('gameRoomName', response.data.name || 'Комната');
                localStorage.setItem('gameSessionId', String(sessionId));
                navigate(`/game/${sessionId}`);
                return;
            }
        } catch (err) {
            setError(err.response?.data?.detail || err.message || 'Ошибка загрузки комнаты');
        } finally {
            if (showLoading) setLoading(false);
        }
    };

    useEffect(() => {
        loadRoom(true);
        const interval = setInterval(() => {
            loadRoom(false);
        }, 2000);

        return () => clearInterval(interval);
    }, [id]);

    const loadMyQuizzes = async () => {
        try {
            setLoadingMyQuizzes(true);
            const response = await quizzesAPI.getMyQuizzes();
            const quizzes = response.data.results || response.data || [];
            setMyQuizzes(Array.isArray(quizzes) ? quizzes : []);
        } catch (err) {
            console.error('Ошибка загрузки моих викторин:', err);
            setMyQuizzes([]);
        } finally {
            setLoadingMyQuizzes(false);
        }
    };

    const loadPublicQuizzes = async () => {
        try {
            setLoadingPublicQuizzes(true);
            const response = await quizzesAPI.getPublicQuizzes();
            const quizzes = response.data.results || response.data || [];
            setPublicQuizzes(Array.isArray(quizzes) ? quizzes : []);
        } catch (err) {
            console.error('Ошибка загрузки публичных викторин:', err);
            setPublicQuizzes([]);
        } finally {
            setLoadingPublicQuizzes(false);
        }
    };

    const handleStartGame = async () => {
        setShowQuizModal(true);
        if (activeTab === 'my') {
            await loadMyQuizzes();
        } else {
            await loadPublicQuizzes();
        }
    };

    const handleTabChange = (tab) => {
        setActiveTab(tab);
        setSearchQuery('');
        if (tab === 'my') {
            loadMyQuizzes();
        } else {
            loadPublicQuizzes();
        }
    };

    const confirmStartGame = async () => {
        if (!selectedQuizId) {
            alert('Выберите викторину');
            return;
        }

        if (!window.confirm('Начать викторину?')) return;

        try {
            setIsStartingGame(true);

            const response = await fetch(`/api/game/rooms/${id}/start/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify({
                    quiz_id: parseInt(selectedQuizId)
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || data.error || 'Ошибка запуска игры');
            }

            const sessionId = data.id || data.session_id;
            if (sessionId) {
                localStorage.setItem('gameRoomId', id);
                localStorage.setItem('gameRoomName', room?.name || 'Комната');
                localStorage.setItem('gameSessionId', sessionId);
                localStorage.setItem('selectedQuizId', selectedQuizId);
                navigate(`/game/${sessionId}`);
            } else {
                alert('Игра запущена, но ID сессии не получен');
                loadRoom();
            }

        } catch (err) {
            console.error('Ошибка запуска игры:', err);
            alert(err.message || 'Ошибка запуска игры');
        } finally {
            setIsStartingGame(false);
            setShowQuizModal(false);
        }
    };

    const handleJoinGame = () => {
        if (!room) return;

        localStorage.setItem('gameRoomId', id);
        localStorage.setItem('gameRoomName', room.name || 'Комната');

        const sessionId = localStorage.getItem('gameSessionId') || id;
        localStorage.setItem('gameSessionId', sessionId);

        navigate(`/game/${sessionId}`);
    };

    const getCurrentQuizzes = () => {
        const quizzes = activeTab === 'my' ? myQuizzes : publicQuizzes;
        if (!searchQuery.trim()) return quizzes;

        const query = searchQuery.toLowerCase();
        return quizzes.filter(quiz =>
            quiz.title?.toLowerCase().includes(query) ||
            quiz.description?.toLowerCase().includes(query) ||
            (quiz.topics && quiz.topics.some(topic =>
                topic.name?.toLowerCase().includes(query)
            ))
        );
    };

    const sortQuizzes = (quizzes) => {
        return [...quizzes].sort((a, b) => {
            if (a.question_count !== b.question_count) {
                return b.question_count - a.question_count;
            }
            return a.title?.localeCompare(b.title);
        });
    };

    const getQuizzesCount = () => {
        const quizzes = activeTab === 'my' ? myQuizzes : publicQuizzes;
        const filtered = getCurrentQuizzes();
        return {total: quizzes.length, filtered: filtered.length};
    };

    const handleChangeStatus = async (newStatus) => {
        if (!window.confirm('Изменить статус?')) return;

        try {
            setIsChangingStatus(true);
            const response = await roomsAPI.updateRoom(id, {status: newStatus});
            setRoom(response.data);
        } catch (err) {
            setError(err.response?.data?.detail || err.message || 'Ошибка изменения статуса');
        } finally {
            setIsChangingStatus(false);
        }
    };

    const handleDeleteRoom = async () => {
        if (!window.confirm('Удалить комнату?')) return;

        try {
            await roomsAPI.deleteRoom(id);
            navigate('/rooms');
        } catch (err) {
            setError(err.response?.data?.detail || err.message || 'Ошибка удаления комнаты');
        }
    };

    const handleLeaveRoom = async () => {
        if (!window.confirm('Выйти из комнаты?')) return;

        try {
            await roomsAPI.leaveRoom(id);
            navigate('/rooms');
        } catch (err) {
            setError(err.response?.data?.detail || err.message || 'Ошибка выхода из комнаты');
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

    if (loading) {
        return (
            <div className={styles.pageContainer}>
                <Header/>
                <main className={styles.main}>
                    <div className={styles.loading}>
                        <p>Загрузка...</p>
                    </div>
                </main>
                <Footer/>
            </div>
        );
    }

    if (!room) {
        return (
            <div className={styles.pageContainer}>
                <Header/>
                <main className={styles.main}>
                    <div className={styles.error}>
                        Комната не найдена
                        <Link to="/rooms" className={styles.errorLink}>Назад</Link>
                    </div>
                </main>
                <Footer/>
            </div>
        );
    }

    const userId = getUserId();
    const isHost = room.host_id === userId;
    const quizzesCount = getQuizzesCount();
    const currentQuizzes = sortQuizzes(getCurrentQuizzes());
    const hasActiveGame = room.status === 'in_progress';

    return (
        <div className={styles.pageContainer}>
            <Header/>
            <main className={styles.main}>
                <div className={styles.headerContainer}>
                    <div className={styles.titleWrapper}>
                        <h1 className={styles.roomTitle}>{room.name}</h1>
                        <span className={`${styles.statusBadge} ${getStatusClass(room.status)}`}>
                            {getStatusText(room.status)}
                        </span>
                        {isHost && <span className={styles.hostBadge}>Хост</span>}
                        {hasActiveGame && (
                            <span className={`${styles.statusBadge} ${styles.statusInProgress}`}>
                                🎮 Игра идет
                            </span>
                        )}
                    </div>
                    <Link to="/rooms" className={styles.backButton}>
                        ← Назад
                    </Link>
                </div>

                {error && (
                    <div className={styles.error}>
                        <p>{error}</p>
                        <button onClick={loadRoom} className={styles.retryButton}>
                            Обновить
                        </button>
                    </div>
                )}

                <div className={styles.roomCard}>
                    <div className={styles.roomInfo}>
                        <p><span className={styles.infoLabel}>Код:</span> <span
                            className={styles.inviteCode}>{room.invite_code}</span></p>
                        <p><span
                            className={styles.infoLabel}>Создана:</span> {new Date(room.created_at).toLocaleString('ru-RU')}
                        </p>
                        <p><span className={styles.infoLabel}>Игроков:</span> {participants.length}</p>
                        {hasActiveGame && (
                            <p>
                                <span className={styles.infoLabel}>Статус игры:</span>
                                <span style={{color: '#4caf50', fontWeight: 'bold', marginLeft: '5px'}}>
                                    Активна
                                </span>
                            </p>
                        )}
                    </div>

                    {hasActiveGame ? (
                        <div className={styles.manageSection}>
                            <h3>{isHost ? 'Вернуться в игру' : 'Присоединиться к игре'}</h3>
                            <div className={styles.controlButtons}>
                                <button
                                    className={`${styles.controlButton} ${styles.controlStart}`}
                                    onClick={handleJoinGame}
                                >
                                    🎮 {isHost ? 'Вернуться в игру' : 'Войти в игру'}
                                </button>
                            </div>
                            <p style={{marginTop: '10px', color: '#666', fontSize: '0.9rem'}}>
                                {isHost
                                    ? 'Вы уже начали игру. Нажмите, чтобы вернуться к игровому процессу.'
                                    : 'Ведущий начал игру. Нажмите, чтобы присоединиться.'
                                }
                            </p>
                        </div>
                    ) : isHost && (
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

                                <button
                                    className={`${styles.controlButton} ${styles.controlStart}`}
                                    onClick={handleStartGame}
                                    disabled={isStartingGame || isChangingStatus}
                                >
                                    {isStartingGame ? '...' : 'Начать викторину'}
                                </button>

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
                                    <div key={p.user_id} className={styles.participantItem}>
                                        <span>{p.username || p.nickname || `Пользователь #${p.user_id}`}</span>
                                        {isHost && p.user_id === userId &&
                                            <span className={styles.hostBadge}>Хост</span>}
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
            <Footer/>

            {showQuizModal && (
                <div className={styles.modalOverlay}>
                    <div className={styles.modal}>
                        <h2>Выберите викторину</h2>

                        <div className={styles.tabs}>
                            <button
                                className={`${styles.tabButton} ${activeTab === 'my' ? styles.activeTab : ''}`}
                                onClick={() => handleTabChange('my')}
                            >
                                Мои викторины
                            </button>
                            <button
                                className={`${styles.tabButton} ${activeTab === 'public' ? styles.activeTab : ''}`}
                                onClick={() => handleTabChange('public')}
                            >
                                Все викторины
                            </button>
                        </div>

                        <div className={styles.searchContainer}>
                            <input
                                type="text"
                                placeholder="Поиск по названию, описанию или темам..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className={styles.searchInput}
                            />
                        </div>

                        <div className={styles.stats}>
                            <span>Всего: {quizzesCount.total}</span>
                            <span>Найдено: {quizzesCount.filtered}</span>
                            {selectedQuizId && <span>✓ Выбрана 1 викторина</span>}
                        </div>

                        {activeTab === 'my' && loadingMyQuizzes ? (
                            <div className={styles.loadingQuizzes}>Загрузка моих викторин...</div>
                        ) : activeTab === 'public' && loadingPublicQuizzes ? (
                            <div className={styles.loadingQuizzes}>Загрузка викторин...</div>
                        ) : currentQuizzes.length === 0 ? (
                            <div className={styles.emptyQuizzes}>
                                {searchQuery ? 'Викторины не найдены' : 'Нет доступных викторин'}
                            </div>
                        ) : (
                            <div className={styles.quizList}>
                                {currentQuizzes.map(quiz => (
                                    <div
                                        key={quiz.id}
                                        className={`${styles.quizItem} ${selectedQuizId === quiz.id.toString() ? styles.quizItemSelected : ''}`}
                                        onClick={() => {
                                            setSelectedQuizId(quiz.id.toString());
                                        }}
                                    >
                                        <div className={styles.quizHeader}>
                                            <h4>{quiz.title}</h4>
                                            <span className={styles.quizStatus}>
                                                {quiz.status === 'published' ? '📢' : '📝'}
                                            </span>
                                        </div>

                                        <p className={styles.quizDescription}>
                                            {quiz.description || 'Описание отсутствует'}
                                        </p>

                                        <div className={styles.quizMeta}>
                                            <span className={styles.quizStat}>
                                                ❓ {quiz.question_count || 0} вопросов
                                            </span>
                                            <span className={styles.quizStat}>
                                                👁️ {quiz.views_count || 0}
                                            </span>
                                            {quiz.author_name && (
                                                <span className={styles.quizAuthor}>
                                                    👤 {quiz.author_name}
                                                </span>
                                            )}
                                        </div>

                                        {quiz.topics && quiz.topics.length > 0 && (
                                            <div className={styles.quizTopics}>
                                                {quiz.topics.slice(0, 3).map(topic => (
                                                    <span key={topic.id} className={styles.topic}>
                                                        {topic.name}
                                                    </span>
                                                ))}
                                                {quiz.topics.length > 3 && (
                                                    <span className={styles.topic}>+{quiz.topics.length - 3}</span>
                                                )}
                                            </div>
                                        )}

                                        {selectedQuizId === quiz.id.toString() && (
                                            <div className={styles.selectedBadge}>✓ Выбрано</div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}

                        <div className={styles.formButtons}>
                            <button
                                type="button"
                                className={styles.cancelButton}
                                onClick={() => setShowQuizModal(false)}
                                disabled={isStartingGame}
                            >
                                Отмена
                            </button>
                            <button
                                type="button"
                                className={styles.submitButton}
                                onClick={confirmStartGame}
                                disabled={isStartingGame || !selectedQuizId}
                            >
                                {isStartingGame ? '...' : 'Начать игру'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default RoomDetail;