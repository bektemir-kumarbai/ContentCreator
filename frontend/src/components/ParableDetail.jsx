import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  getParable,
  processParable,
  uploadVideoFragment,
  generateFinalVideo,
  deleteParable
} from '../api'

function ParableDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [parable, setParable] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [uploadingVideos, setUploadingVideos] = useState({})
  const [generatingFinal, setGeneratingFinal] = useState(false)

  useEffect(() => {
    loadParable()
    // Автообновление каждые 5 секунд если идёт обработка
    const interval = setInterval(() => {
      if (parable && ['processing', 'generating_final'].includes(parable.status)) {
        loadParable()
      }
    }, 5000)
    return () => clearInterval(interval)
  }, [id, parable?.status])

  const loadParable = async () => {
    try {
      setLoading(true)
      const data = await getParable(id)
      setParable(data)
    } catch (err) {
      setError('Ошибка загрузки притчи')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleProcess = async () => {
    try {
      setError(null)
      setSuccess(null)
      await processParable(id)
      setSuccess('Обработка запущена! Это может занять несколько минут...')
      setTimeout(() => loadParable(), 2000)
    } catch (err) {
      setError('Ошибка запуска обработки')
      console.error(err)
    }
  }

  const handleVideoUpload = async (sceneOrder, file) => {
    try {
      setUploadingVideos(prev => ({ ...prev, [sceneOrder]: true }))
      setError(null)
      await uploadVideoFragment(id, sceneOrder, file)
      setSuccess(`Видео для сцены ${sceneOrder + 1} загружено!`)
      setTimeout(() => {
        loadParable()
        setSuccess(null)
      }, 2000)
    } catch (err) {
      setError(`Ошибка загрузки видео для сцены ${sceneOrder + 1}`)
      console.error(err)
    } finally {
      setUploadingVideos(prev => ({ ...prev, [sceneOrder]: false }))
    }
  }

  const handleGenerateFinal = async () => {
    try {
      setGeneratingFinal(true)
      setError(null)
      await generateFinalVideo(id)
      setSuccess('Генерация финального видео запущена!')
      setTimeout(() => loadParable(), 2000)
    } catch (err) {
      setError('Ошибка генерации финального видео')
      console.error(err)
    } finally {
      setGeneratingFinal(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm('Вы уверены, что хотите удалить эту притчу?')) {
      return
    }
    try {
      await deleteParable(id)
      navigate('/')
    } catch (err) {
      setError('Ошибка удаления притчи')
      console.error(err)
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

  if (!parable) {
    return <div className="error">Притча не найдена</div>
  }

  return (
    <div>
      <button className="btn back-button" onClick={() => navigate('/')}>
        ← Назад к списку
      </button>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h2>{parable.title_original}</h2>
            <span className={`status ${parable.status}`}>
              {getStatusText(parable.status)}
            </span>
          </div>
          <button className="btn btn-danger" onClick={handleDelete}>
            🗑️ Удалить
          </button>
        </div>

        {error && <div className="error">{error}</div>}
        {success && <div className="success">{success}</div>}

        <div style={{ marginTop: '1.5rem' }}>
          <h3>Оригинальный текст</h3>
          <p style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6', color: '#555' }}>
            {parable.text_original}
          </p>
        </div>

        {parable.status === 'draft' && (
          <div className="actions">
            <button className="btn btn-primary" onClick={handleProcess}>
              🚀 Запустить обработку
            </button>
          </div>
        )}
      </div>

      {parable.text_for_tts && (
        <div className="card">
          <h3>Текст для озвучки</h3>
          <p style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6', color: '#555' }}>
            {parable.text_for_tts}
          </p>
        </div>
      )}

      {(parable.youtube_title || parable.youtube_description) && (
        <div className="card">
          <div className="metadata-section">
            <h3>Метаданные для YouTube</h3>
            {parable.youtube_title && (
              <p><strong>Заголовок:</strong> {parable.youtube_title}</p>
            )}
            {parable.youtube_description && (
              <p><strong>Описание:</strong> {parable.youtube_description}</p>
            )}
            {parable.youtube_hashtags && (
              <p><strong>Хэштеги:</strong> {parable.youtube_hashtags}</p>
            )}
          </div>
        </div>
      )}

      {parable.generated_images && parable.generated_images.length > 0 && (
        <div className="card">
          <h3>Сгенерированные изображения</h3>
          <div className="images-grid">
            {parable.generated_images.map((image) => (
              <div key={image.id} className="image-item">
                <img src={`/${image.image_path}`} alt={`Сцена ${image.scene_order + 1}`} />
                <div className="scene-number">Сцена {image.scene_order + 1}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {parable.audio_files && parable.audio_files.length > 0 && (
        <div className="card">
          <h3>Аудио озвучка</h3>
          <div className="audio-player">
            <audio controls>
              <source src={`/${parable.audio_files[0].audio_path}`} type="audio/mpeg" />
              Ваш браузер не поддерживает аудио.
            </audio>
            {parable.audio_files[0].duration && (
              <p style={{ marginTop: '0.5rem', color: '#666' }}>
                Длительность: {parable.audio_files[0].duration.toFixed(1)} секунд
              </p>
            )}
          </div>
        </div>
      )}

      {parable.status === 'awaiting_videos' && parable.generated_images && (
        <div className="card">
          <h3>Загрузка видеофрагментов</h3>
          <p style={{ color: '#666', marginBottom: '1rem' }}>
            Отправьте каждое изображение в Grok для создания видео, затем загрузите полученные видео здесь.
          </p>
          <div className="upload-section">
            {parable.generated_images.map((image) => {
              const hasVideo = parable.video_fragments?.some(
                vf => vf.scene_order === image.scene_order
              )
              return (
                <div key={image.id} className="upload-item">
                  <span style={{ fontWeight: '600', minWidth: '100px' }}>
                    Сцена {image.scene_order + 1}:
                  </span>
                  {hasVideo ? (
                    <span style={{ color: '#155724', fontWeight: '600' }}>✅ Загружено</span>
                  ) : (
                    <>
                      <input
                        type="file"
                        accept="video/*"
                        onChange={(e) => {
                          if (e.target.files[0]) {
                            handleVideoUpload(image.scene_order, e.target.files[0])
                          }
                        }}
                        disabled={uploadingVideos[image.scene_order]}
                      />
                      {uploadingVideos[image.scene_order] && (
                        <span style={{ color: '#856404' }}>Загрузка...</span>
                      )}
                    </>
                  )}
                </div>
              )
            })}
          </div>

          {parable.video_fragments?.length === parable.generated_images.length && (
            <div className="actions">
              <button
                className="btn btn-success"
                onClick={handleGenerateFinal}
                disabled={generatingFinal}
              >
                {generatingFinal ? '⏳ Генерация...' : '🎬 Сгенерировать финальное видео'}
              </button>
            </div>
          )}
        </div>
      )}

      {parable.final_video_path && (
        <div className="card">
          <h3>Финальное видео</h3>
          <div className="video-player">
            <video controls>
              <source src={`/${parable.final_video_path}`} type="video/mp4" />
              Ваш браузер не поддерживает видео.
            </video>
            {parable.final_video_duration && (
              <p style={{ marginTop: '1rem', fontSize: '1.1rem', color: '#667eea' }}>
                ⏱️ Длительность: {parable.final_video_duration.toFixed(1)} секунд
              </p>
            )}
            <div className="actions" style={{ justifyContent: 'center', marginTop: '1rem' }}>
              <a
                href={`/${parable.final_video_path}`}
                download={`${parable.title_original}.mp4`}
                className="btn btn-success"
              >
                ⬇️ Скачать видео
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ParableDetail

