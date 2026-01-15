import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getParables } from '../api'

function ParablesList() {
  const [parables, setParables] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    loadParables()
  }, [])

  const loadParables = async () => {
    try {
      setLoading(true)
      const data = await getParables()
      setParables(data)
    } catch (err) {
      setError('Ошибка загрузки притч')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const getStatusText = (status) => {
    const statusMap = {
      draft: 'Черновик',
      processing: 'Обработка...',
      awaiting_videos: 'Ожидание видео',
      generating_final: 'Генерация видео...',
      completed: 'Готово',
      error: 'Ошибка'
    }
    return statusMap[status] || status
  }

  if (loading) {
    return <div className="loading">Загрузка...</div>
  }

  return (
    <div>
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2>Мои притчи</h2>
          <button className="btn btn-primary" onClick={() => navigate('/create')}>
            ➕ Создать новую притчу
          </button>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      {parables.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
          <p style={{ fontSize: '1.2rem', color: '#666' }}>
            У вас пока нет притч. Создайте первую!
          </p>
        </div>
      ) : (
        <div className="parables-grid">
          {parables.map((parable) => (
            <div
              key={parable.id}
              className="parable-card"
              onClick={() => navigate(`/parable/${parable.id}`)}
            >
              <h3>{parable.title_original}</h3>
              <span className={`status ${parable.status}`}>
                {getStatusText(parable.status)}
              </span>
              <p style={{ color: '#666', fontSize: '0.9rem' }}>
                {new Date(parable.created_at).toLocaleDateString('ru-RU', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric'
                })}
              </p>
              {parable.final_video_duration && (
                <p style={{ marginTop: '0.5rem', fontWeight: '600', color: '#667eea' }}>
                  ⏱️ {parable.final_video_duration.toFixed(1)}с
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default ParablesList

