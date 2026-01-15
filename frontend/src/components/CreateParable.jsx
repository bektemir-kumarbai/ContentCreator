import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createParable } from '../api'

function CreateParable() {
  const [title, setTitle] = useState('')
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!title.trim() || !text.trim()) {
      setError('Заполните все поля')
      return
    }

    try {
      setLoading(true)
      setError(null)
      const parable = await createParable({
        title_original: title,
        text_original: text
      })
      navigate(`/parable/${parable.id}`)
    } catch (err) {
      setError('Ошибка создания притчи')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <button className="btn back-button" onClick={() => navigate('/')}>
        ← Назад к списку
      </button>

      <div className="card">
        <h2>Создать новую притчу</h2>
        
        {error && <div className="error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="title">Заголовок притчи</label>
            <input
              id="title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Введите заголовок..."
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="text">Текст притчи</label>
            <textarea
              id="text"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Введите текст притчи..."
              disabled={loading}
            />
          </div>

          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Создание...' : '✨ Создать притчу'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default CreateParable

