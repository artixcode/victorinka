import React, {useState, useEffect} from 'react';
import styles from '../styles/CreateQuiz.module.css';

const QuestionForm = ({onSave, onCancel, initialData}) => {
    const [question, setQuestion] = useState({
        text: '',
        explanation: '',
        difficulty: 'medium',
        points: 1,
        options: [
            {text: '', is_correct: false, order: 1},
            {text: '', is_correct: false, order: 2},
            {text: '', is_correct: false, order: 3},
            {text: '', is_correct: false, order: 4}
        ]
    });

    useEffect(() => {
        if (initialData) {
            const restoredOptions = initialData.options && Array.isArray(initialData.options)
                ? initialData.options.map((opt, index) => ({
                    text: opt.text || '',
                    is_correct: Boolean(opt.is_correct),
                    order: index + 1
                }))
                : [
                    {text: '', is_correct: false, order: 1},
                    {text: '', is_correct: false, order: 2},
                    {text: '', is_correct: false, order: 3},
                    {text: '', is_correct: false, order: 4}
                ];

            while (restoredOptions.length < 4) {
                restoredOptions.push({
                    text: '',
                    is_correct: false,
                    order: restoredOptions.length + 1
                });
            }

            setQuestion({
                text: initialData.text || '',
                explanation: initialData.explanation || '',
                difficulty: initialData.difficulty || 'medium',
                points: initialData.points || 1,
                options: restoredOptions
            });
        }
    }, [initialData]);

    const handleQuestionChange = (field, value) => {
        setQuestion({...question, [field]: value});
    };

    const handleOptionChange = (index, field, value) => {
        const newOptions = [...question.options];

        if (field === 'is_correct' && value === true) {
            newOptions.forEach(opt => {
                opt.is_correct = false;
            });
        }

        newOptions[index][field] = value;
        setQuestion({...question, options: newOptions});
    };

    const handleSave = () => {
        if (!question.text.trim()) {
            alert('Введите текст вопроса');
            return;
        }

        const filledOptions = question.options
            .filter(opt => opt.text.trim() !== '')
            .map((opt, index) => ({
                ...opt,
                order: index + 1
            }));

        if (filledOptions.length === 0) {
            alert('Добавьте хотя бы один вариант ответа');
            return;
        }

        const hasCorrectAnswer = filledOptions.some(opt => opt.is_correct);
        if (!hasCorrectAnswer) {
            alert('Выберите правильный вариант ответа');
            return;
        }

        onSave({
            ...question,
            options: filledOptions
        });
    };

    const addOption = () => {
        if (question.options.length >= 6) {
            alert('Максимум 6 вариантов ответа');
            return;
        }

        const newOptions = [...question.options, {
            text: '',
            is_correct: false,
            order: question.options.length + 1
        }];
        setQuestion({...question, options: newOptions});
    };

    const removeOption = (index) => {
        if (question.options.length <= 2) {
            alert('Должно быть минимум 2 варианта ответа');
            return;
        }

        const newOptions = question.options.filter((_, i) => i !== index)
            .map((opt, i) => ({...opt, order: i + 1}));
        setQuestion({...question, options: newOptions});
    };

    return (
        <div className={styles.questionForm}>
            <div className={styles.formHeader}>
                <h3>{initialData ? 'Редактирование вопроса' : 'Новый вопрос'}</h3>
            </div>

            <div className={styles.formGroup}>
                <label>Текст вопроса *</label>
                <textarea
                    value={question.text}
                    onChange={(e) => handleQuestionChange('text', e.target.value)}
                    placeholder="Введите текст вопроса..."
                    rows="3"
                />
            </div>

            <div className={styles.formGroup}>
                <label>Объяснение (опционально)</label>
                <textarea
                    value={question.explanation}
                    onChange={(e) => handleQuestionChange('explanation', e.target.value)}
                    placeholder="Объяснение правильного ответа..."
                    rows="2"
                />
            </div>

            <div className={styles.formRow}>
                <div className={styles.formGroup}>
                    <label>Сложность</label>
                    <select
                        value={question.difficulty}
                        onChange={(e) => handleQuestionChange('difficulty', e.target.value)}
                    >
                        <option value="easy">🟢 Легкий</option>
                        <option value="medium">🟡 Средний</option>
                        <option value="hard">🔴 Сложный</option>
                    </select>
                </div>

                <div className={styles.formGroup}>
                    <label>Баллы</label>
                    <input
                        type="number"
                        min="1"
                        max="100"
                        value={question.points}
                        onChange={(e) => handleQuestionChange('points', parseInt(e.target.value) || 1)}
                    />
                </div>
            </div>

            <div className={styles.optionsSection}>
                <div className={styles.optionsHeader}>
                    <h4>Варианты ответов *</h4>
                    <button
                        type="button"
                        onClick={addOption}
                        className={styles.addOptionButton}
                    >
                        + Добавить вариант
                    </button>
                </div>

                {question.options.map((option, index) => (
                    <div key={index} className={styles.optionItem}>
                        <div className={styles.optionInputs}>
                            <input
                                type="text"
                                value={option.text}
                                onChange={(e) => handleOptionChange(index, 'text', e.target.value)}
                                placeholder={`Вариант ответа ${index + 1}...`}
                                className={styles.optionText}
                            />

                            <label className={styles.correctLabel}>
                                <input
                                    type="radio"
                                    name="correct-option"
                                    checked={option.is_correct}
                                    onChange={(e) => handleOptionChange(index, 'is_correct', e.target.checked)}
                                />
                                Правильный
                            </label>

                            {question.options.length > 2 && (
                                <button
                                    type="button"
                                    onClick={() => removeOption(index)}
                                    className={styles.removeOptionButton}
                                    title="Удалить вариант"
                                >
                                    🗑️
                                </button>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            <div className={styles.formActions}>
                <button
                    type="button"
                    onClick={onCancel}
                    className={styles.cancelButton}
                >
                    Отмена
                </button>
                <button
                    type="button"
                    onClick={handleSave}
                    className={styles.saveButton}
                >
                    {initialData ? 'Сохранить изменения' : 'Добавить вопрос'}
                </button>
            </div>
        </div>
    );
};

export default QuestionForm;