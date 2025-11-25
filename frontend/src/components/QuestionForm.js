import React, { useState } from 'react';
import styles from '../styles/QuestionForm.module.css';

const QuestionForm = ({ onSave, onCancel, initialData }) => {
  const [question, setQuestion] = useState(initialData || {
    text: '',
    explanation: '',
    difficulty: 'medium',
    points: 1,
    options: [
      { text: '', is_correct: false, order: 1 },
      { text: '', is_correct: false, order: 2 },
      { text: '', is_correct: false, order: 3 },
      { text: '', is_correct: false, order: 4 }
    ]
  });

  const handleOptionChange = (index, field, value) => {
    const newOptions = [...question.options];

    if (field === 'is_correct') {
      // Сбрасываем все is_correct и устанавливаем только для выбранного
      newOptions.forEach(opt => { opt.is_correct = false; });
      newOptions[index].is_correct = value;
    } else {
      newOptions[index][field] = value;
    }

    setQuestion({ ...question, options: newOptions });
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    const hasCorrectAnswer = question.options.some(opt => opt.is_correct);
    if (!hasCorrectAnswer) {
      alert('Выберите правильный вариант ответа');
      return;
    }

    // Проверяем, что все варианты заполнены
    const allOptionsFilled = question.options.every(opt => opt.text.trim() !== '');
    if (!allOptionsFilled) {
      alert('Заполните все варианты ответов');
      return;
    }

    if (!question.text.trim()) {
      alert('Введите текст вопроса');
      return;
    }

    onSave(question);
  };

  return (
    <div className={styles.questionForm}>
      <h3>{initialData ? 'Редактировать вопрос' : 'Новый вопрос'}</h3>

      <form onSubmit={handleSubmit}>
        <div className={styles.formGroup}>
          <label>Текст вопроса *</label>
          <textarea
            value={question.text}
            onChange={(e) => setQuestion({ ...question, text: e.target.value })}
            placeholder="Введите текст вопроса..."
            rows="3"
            required
          />
        </div>

        <div className={styles.formRow}>
          <div className={styles.formGroup}>
            <label>Сложность</label>
            <select
              value={question.difficulty}
              onChange={(e) => setQuestion({ ...question, difficulty: e.target.value })}
            >
              <option value="easy">Лёгкий</option>
              <option value="medium">Средний</option>
              <option value="hard">Сложный</option>
            </select>
          </div>

          <div className={styles.formGroup}>
            <label>Баллы</label>
            <input
              type="number"
              min="1"
              max="100"
              value={question.points}
              onChange={(e) => setQuestion({ ...question, points: parseInt(e.target.value) || 1 })}
            />
          </div>
        </div>

        <div className={styles.formGroup}>
          <label>Объяснение (необязательно)</label>
          <textarea
            value={question.explanation}
            onChange={(e) => setQuestion({ ...question, explanation: e.target.value })}
            placeholder="Объяснение правильного ответа..."
            rows="2"
          />
        </div>

        <div className={styles.optionsSection}>
          <label>Варианты ответов *</label>
          {question.options.map((option, index) => (
            <div key={index} className={styles.optionItem}>
              <input
                type="radio"
                name="correctAnswer"
                checked={option.is_correct}
                onChange={(e) => handleOptionChange(index, 'is_correct', e.target.checked)}
                className={styles.correctRadio}
              />
              <input
                type="text"
                value={option.text}
                onChange={(e) => handleOptionChange(index, 'text', e.target.value)}
                placeholder={`Вариант ${index + 1}`}
                className={styles.optionInput}
              />
              <span className={styles.optionNumber}>{index + 1}</span>
            </div>
          ))}
        </div>

        <div className={styles.formActions}>
          <button type="button" onClick={onCancel} className={styles.cancelButton}>
            Отмена
          </button>
          <button type="submit" className={styles.saveButton}>
            {initialData ? 'Обновить' : 'Добавить'} вопрос
          </button>
        </div>
      </form>
    </div>
  );
};

export default QuestionForm;