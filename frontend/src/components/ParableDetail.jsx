import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  getParable,
  processParable,
  regenerateImages,
  uploadAudio,
  uploadVideoFragment,
  generateFinalVideo,
  deleteParable,
  createEnglishVersion,
  getEnglishVersion,
  processEnglishVersion,
  uploadEnglishAudio,
  uploadEnglishVideoFragment,
  generateEnglishFinalVideo,
  updateVideoDuration,
  STATIC_BASE_URL
} from '../api'

function ParableDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [parable, setParable] = useState(null)
  const [englishVersion, setEnglishVersion] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [uploadingVideos, setUploadingVideos] = useState({})
  const [draggingScenes, setDraggingScenes] = useState({})
  const [uploadingAudio, setUploadingAudio] = useState(false)
  const [titleVariants, setTitleVariants] = useState([])
  const [selectedMusic, setSelectedMusic] = useState(null)
  const [generatingFinal, setGeneratingFinal] = useState(false)
  const [regeneratingImages, setRegeneratingImages] = useState(false)

  useEffect(() => {
    loadParable()
    loadEnglishVersion()
    loadTitleVariants()
    // Автообновление каждые 5 секунд если идёт обработка
    const interval = setInterval(() => {
      if (parable && ['processing', 'generating_final'].includes(parable.status)) {
        loadParable()
        loadTitleVariants()
      }
      if (englishVersion && ['processing', 'generating_final'].includes(englishVersion.status)) {
        loadEnglishVersion()
      }
    }, 5000)
    return () => clearInterval(interval)
  }, [id, parable?.status, englishVersion?.status])

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

  const loadEnglishVersion = async () => {
    try {
      const data = await getEnglishVersion(id)
      setEnglishVersion(data)
    } catch (err) {
      // Английская версия может не существовать, это нормально
      setEnglishVersion(null)
    }
  }

  const loadTitleVariants = async () => {
    try {
      const response = await fetch(`http://localhost:8000/parables/${id}/title-variants`)
      if (response.ok) {
        const data = await response.json()
        setTitleVariants(data)
      }
    } catch (err) {
      console.error('Error loading title variants:', err)
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

  const handleAudioUpload = async (file) => {
    try {
      setUploadingAudio(true)
      setError(null)
      await uploadAudio(id, file)
      setSuccess('Аудио загружено успешно!')
      setTimeout(() => {
        loadParable()
        setSuccess(null)
      }, 2000)
    } catch (err) {
      setError('Ошибка загрузки аудио')
      console.error(err)
    } finally {
      setUploadingAudio(false)
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

  const handleDurationChange = async (videoFragmentId, targetDuration) => {
    try {
      const value = targetDuration === '' ? null : parseFloat(targetDuration)
      await updateVideoDuration(id, videoFragmentId, value)
      await loadParable()
    } catch (err) {
      setError('Ошибка обновления длительности')
      console.error(err)
    }
  }

  const handleRegenerateImages = async () => {
    try {
      setRegeneratingImages(true)
      setError(null)
      await regenerateImages(id)
      setSuccess('Перегенерация изображений запущена! Это может занять несколько минут...')
      setTimeout(() => loadParable(), 2000)
    } catch (err) {
      setError('Ошибка перегенерации изображений')
      console.error(err)
    } finally {
      setRegeneratingImages(false)
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

  // ═══════════════════════════════════════════════════════════════
  // ENGLISH VERSION HANDLERS
  // ═══════════════════════════════════════════════════════════════

  const handleCreateEnglishVersion = async () => {
    try {
      setError(null)
      setSuccess(null)
      await createEnglishVersion(id)
      setSuccess('Английская версия создана!')
      setTimeout(() => {
        loadEnglishVersion()
        setSuccess(null)
      }, 2000)
    } catch (err) {
      setError('Ошибка создания английской версии')
      console.error(err)
    }
  }

  const handleProcessEnglishVersion = async () => {
    try {
      setError(null)
      setSuccess(null)
      await processEnglishVersion(id)
      setSuccess('Обработка английской версии запущена!')
      setTimeout(() => loadEnglishVersion(), 2000)
    } catch (err) {
      setError('Ошибка запуска обработки английской версии')
      console.error(err)
    }
  }

  const handleEnglishAudioUpload = async (file) => {
    try {
      setUploadingAudio(true)
      setError(null)
      await uploadEnglishAudio(id, file)
      setSuccess('Английское аудио загружено успешно!')
      setTimeout(() => {
        loadEnglishVersion()
        setSuccess(null)
      }, 2000)
    } catch (err) {
      setError('Ошибка загрузки английского аудио')
      console.error(err)
    } finally {
      setUploadingAudio(false)
    }
  }

  const handleEnglishVideoUpload = async (sceneOrder, file) => {
    try {
      setUploadingVideos(prev => ({ ...prev, [`en_${sceneOrder}`]: true }))
      setError(null)
      await uploadEnglishVideoFragment(id, sceneOrder, file)
      setSuccess(`English video for scene ${sceneOrder + 1} uploaded!`)
      setTimeout(() => {
        loadEnglishVersion()
        setSuccess(null)
      }, 2000)
    } catch (err) {
      setError(`Ошибка загрузки английского видео для сцены ${sceneOrder + 1}`)
      console.error(err)
    } finally {
      setUploadingVideos(prev => ({ ...prev, [`en_${sceneOrder}`]: false }))
    }
  }

  const handleGenerateEnglishFinal = async () => {
    try {
      setGeneratingFinal(true)
      setError(null)
      await generateEnglishFinalVideo(id)
      setSuccess('Генерация английского финального видео запущена!')
      setTimeout(() => loadEnglishVersion(), 2000)
    } catch (err) {
      setError('Ошибка генерации английского финального видео')
      console.error(err)
    } finally {
      setGeneratingFinal(false)
    }
  }

  const getStatusText = (status) => {
    const statusMap = {
      draft: 'Черновик',
      processing: 'Обработка...',
      awaiting_audio: 'Ожидание аудио',
      awaiting_videos: 'Ожидание видео',
      generating_final: 'Генерация видео...',
      completed: 'Готово',
      error: 'Ошибка'
    }
    return statusMap[status] || status
  }

  const getStepName = (step) => {
    const stepNames = {
      0: 'Ожидание',
      1: 'Переписывание текста для TTS',
      2: 'Генерация метаданных и промптов',
      3: 'Генерация изображений',
      4: 'Подготовка аудио (ручная загрузка)',
      5: 'Завершено'
    }
    return stepNames[step] || 'Неизвестный шаг'
  }

  if (loading) {
    return <div className="loading">Загрузка...</div>
  }

  if (!parable) {
    return <div className="error">Притча не найдена</div>
  }

  return (
    <div>
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem' }}>
        <button className="btn back-button" onClick={() => navigate('/')}>
          ← Назад к списку
        </button>
        {englishVersion ? (
          <button 
            className="btn btn-success" 
            onClick={() => navigate(`/parable/${id}/english`)}
          >
            🇬🇧 English Version
          </button>
        ) : (
          <button 
            className="btn btn-primary" 
            onClick={handleCreateEnglishVersion}
          >
            🌍 Create English Version
          </button>
        )}
      </div>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h2>🇷🇺 {parable.title_original}</h2>
            <span className={`status ${parable.status}`}>
              {getStatusText(parable.status)}
            </span>
            {parable.status === 'processing' && parable.current_step > 0 && (
              <div style={{ marginTop: '0.5rem', fontSize: '0.9rem', color: '#666' }}>
                📍 {getStepName(parable.current_step)} ({parable.current_step}/4)
              </div>
            )}
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

        {parable.status === 'error' && (
          <div className="card" style={{ backgroundColor: '#fff3cd', borderColor: '#ffc107' }}>
            <h3 style={{ color: '#856404' }}>⚠️ Ошибка обработки</h3>
            {parable.error_message && (
              <div style={{ 
                backgroundColor: '#fff', 
                padding: '1rem', 
                borderRadius: '4px', 
                marginBottom: '1rem',
                fontFamily: 'monospace',
                fontSize: '0.9rem',
                color: '#721c24'
              }}>
                {parable.error_message}
              </div>
            )}
            <p style={{ color: '#856404', marginBottom: '1rem' }}>
              Обработка остановилась на шаге {parable.current_step || 0}. 
              Вы можете возобновить обработку с этого места.
            </p>
            <div className="actions">
              <button className="btn btn-primary" onClick={handleProcess}>
                🔄 Возобновить обработку
              </button>
            </div>
          </div>
        )}
      </div>

      {parable.hook_text && (
        <div className="card" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
          <h3>⚡ Хук (первые 3 секунды)</h3>
          <p style={{ fontSize: '1.2em', fontWeight: 'bold', lineHeight: '1.6' }}>
            {parable.hook_text}
          </p>
          <small style={{ opacity: 0.9 }}>Цепляющее начало для максимального retention</small>
        </div>
      )}

      {parable.text_for_tts && (
        <div className="card">
          <h3>Текст для озвучки</h3>
          <p style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6', color: '#555' }}>
            {parable.text_for_tts}
          </p>
        </div>
      )}

      {titleVariants.length > 0 && (
        <div className="card">
          <h3>📊 A/B тестирование заголовков</h3>
          <p style={{ color: '#666', marginBottom: '1rem' }}>
            LLM сгенерировал 5 вариантов и автоматически выбрал лучший:
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {titleVariants.map((variant) => (
              <div
                key={variant.id}
                style={{
                  padding: '1rem',
                  border: variant.is_selected ? '2px solid #4CAF50' : '1px solid #ddd',
                  borderRadius: '8px',
                  background: variant.is_selected ? '#f1f8f4' : '#fff',
                  position: 'relative'
                }}
              >
                {variant.is_selected && (
                  <span style={{
                    position: 'absolute',
                    top: '0.5rem',
                    right: '0.5rem',
                    background: '#4CAF50',
                    color: 'white',
                    padding: '0.25rem 0.5rem',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                    fontWeight: 'bold'
                  }}>
                    ✓ ВЫБРАН AI
                  </span>
                )}
                <div style={{ fontSize: '0.75rem', color: '#888', marginBottom: '0.25rem', textTransform: 'uppercase' }}>
                  {variant.variant_type === 'question' && '❓ Вопрос'}
                  {variant.variant_type === 'intrigue' && '🔮 Интрига'}
                  {variant.variant_type === 'emotion' && '💔 Эмоция'}
                  {variant.variant_type === 'numbers' && '🔢 С цифрами'}
                  {variant.variant_type === 'provocation' && '⚡ Провокация'}
                </div>
                <div style={{ fontSize: '1.1rem', fontWeight: variant.is_selected ? 'bold' : 'normal' }}>
                  {variant.variant_text}
                </div>
              </div>
            ))}
          </div>
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

      {parable.image_prompts && parable.image_prompts.length > 0 && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3>Сгенерированные изображения</h3>
            <button 
              className="btn btn-primary" 
              onClick={handleRegenerateImages}
              disabled={regeneratingImages}
              style={{ fontSize: '0.9rem', padding: '0.5rem 1rem' }}
            >
              {regeneratingImages ? '⏳ Генерация...' : '🔄 Перегенерировать изображения'}
            </button>
          </div>
          
          {parable.generated_images && parable.generated_images.length > 0 ? (
            <>
              <p style={{ color: '#666', marginBottom: '1rem' }}>
                Сгенерировано {parable.generated_images.length} из {parable.image_prompts.length} изображений
              </p>
              <div className="images-grid">
                {parable.generated_images
                  .sort((a, b) => a.scene_order - b.scene_order) // Сортируем: -1 (хук) первым, потом 0, 1, 2...
                  .map((image) => {
                  // Находим соответствующий промпт для этого изображения
                  const prompt = parable.image_prompts.find(p => p.scene_order === image.scene_order)
                  
                  // Определяем название сцены
                  const sceneLabel = image.scene_order === -1 ? '⚡ ХУК' : `Сцена ${image.scene_order + 1}`
                  
                  return (
                    <div key={image.id} className="image-item">
                      <img src={`${STATIC_BASE_URL}/${image.image_path}`} alt={sceneLabel} />
                      <div className="scene-number">{sceneLabel}</div>
                      
                      {/* Промпты для изображения и видео */}
                      {prompt && (
                        <div style={{ 
                          padding: '0.75rem', 
                          backgroundColor: '#f8f9fa', 
                          fontSize: '0.85rem',
                          borderTop: '1px solid #e0e0e0'
                        }}>
                          <div style={{ marginBottom: '0.5rem' }}>
                            <strong style={{ color: '#667eea' }}>🖼️ Image Prompt:</strong>
                            <p style={{ margin: '0.25rem 0 0 0', color: '#555' }}>{prompt.prompt_text}</p>
                          </div>
                          {prompt.video_prompt_text && (
                            <div>
                              <strong style={{ color: '#11998e' }}>🎬 Video Prompt:</strong>
                              <p style={{ margin: '0.25rem 0 0 0', color: '#555' }}>{prompt.video_prompt_text}</p>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </>
          ) : (
            <div style={{ 
              padding: '2rem', 
              textAlign: 'center', 
              backgroundColor: '#fff3cd', 
              borderRadius: '8px',
              border: '1px solid #ffc107'
            }}>
              <p style={{ color: '#856404', fontSize: '1.1rem', marginBottom: '1rem' }}>
                ⚠️ Изображения не сгенерированы
              </p>
              <p style={{ color: '#856404', marginBottom: '1rem' }}>
                Промптов готово: {parable.image_prompts.length}
              </p>
              <button 
                className="btn btn-primary" 
                onClick={handleRegenerateImages}
                disabled={regeneratingImages}
              >
                {regeneratingImages ? '⏳ Генерация...' : '🎨 Сгенерировать изображения'}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Секция аудио - всегда показываем */}
      <div className="card">
        <h3>🎙️ Аудио озвучка</h3>
        
        {parable.audio_files && parable.audio_files.length > 0 ? (
          <>
            <div className="audio-player">
              <audio controls>
                <source src={`${STATIC_BASE_URL}/${parable.audio_files[0].audio_path}`} type="audio/mpeg" />
                Ваш браузер не поддерживает аудио.
              </audio>
              {parable.audio_files[0].duration && (
                <p style={{ marginTop: '0.5rem', color: '#666' }}>
                  Длительность: {parable.audio_files[0].duration.toFixed(1)} секунд
                </p>
              )}
            </div>
            
            <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: '#d1ecf1', borderRadius: '8px' }}>
              <p style={{ color: '#0c5460', marginBottom: '0.5rem' }}>
                💡 Вы можете заменить аудио, загрузив новый файл:
              </p>
              <input
                type="file"
                accept="audio/*"
                onChange={(e) => {
                  if (e.target.files[0]) {
                    handleAudioUpload(e.target.files[0])
                  }
                }}
                disabled={uploadingAudio}
                style={{ marginTop: '0.5rem' }}
              />
              {uploadingAudio && <span style={{ marginLeft: '1rem', color: '#856404' }}>Загрузка...</span>}
            </div>
          </>
        ) : (
          <div style={{ 
            padding: '2rem', 
            textAlign: 'center', 
            backgroundColor: '#fff3cd', 
            borderRadius: '8px',
            border: '1px solid #ffc107'
          }}>
            <p style={{ color: '#856404', fontSize: '1.1rem', marginBottom: '1rem' }}>
              ⏸️ Аудио ожидает загрузки
            </p>
            <p style={{ color: '#856404', marginBottom: '1rem' }}>
              Озвучьте текст для TTS (выше) и загрузите аудиофайл:
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
              <input
                type="file"
                accept="audio/*,.mp3,.wav,.m4a"
                onChange={(e) => {
                  if (e.target.files[0]) {
                    handleAudioUpload(e.target.files[0])
                  }
                }}
                disabled={uploadingAudio}
                style={{ fontSize: '1rem' }}
              />
              {uploadingAudio && <span style={{ color: '#856404' }}>⏳ Загрузка...</span>}
              <p style={{ fontSize: '0.9rem', color: '#666', marginTop: '0.5rem' }}>
                Поддерживаемые форматы: MP3, WAV, M4A
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Секция видеофрагментов - всегда показываем если есть изображения */}
      {parable.generated_images && parable.generated_images.length > 0 && (
        <div className="card">
          <h3>Загрузка видеофрагментов</h3>
          <p style={{ color: '#666', marginBottom: '1rem' }}>
            Отправьте каждое изображение в Grok для создания видео, затем загрузите или перетащите полученные видео сюда.
          </p>
          <div className="upload-section">
            {parable.generated_images.map((image) => {
              const videoFragment = parable.video_fragments?.find(
                vf => vf.scene_order === image.scene_order
              )
              const hasVideo = !!videoFragment
              const isDragging = draggingScenes[image.scene_order] || false
              
              const handleDragOver = (e) => {
                e.preventDefault()
                setDraggingScenes(prev => ({ ...prev, [image.scene_order]: true }))
              }
              
              const handleDragLeave = (e) => {
                e.preventDefault()
                setDraggingScenes(prev => ({ ...prev, [image.scene_order]: false }))
              }
              
              const handleDrop = (e) => {
                e.preventDefault()
                setDraggingScenes(prev => ({ ...prev, [image.scene_order]: false }))
                const file = e.dataTransfer.files[0]
                if (file && file.type.startsWith('video/')) {
                  handleVideoUpload(image.scene_order, file)
                }
              }
              
              const sceneLabel = image.scene_order === -1 
                ? '⚡ ХУК' 
                : `Сцена ${image.scene_order + 1}`
              
              return (
                <div 
                  key={image.id} 
                  className="upload-item"
                  style={{
                    border: isDragging ? '2px dashed #667eea' : '1px solid #e0e0e0',
                    backgroundColor: isDragging ? '#f0f4ff' : 'white',
                    transition: 'all 0.3s ease',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.5rem',
                    padding: '1rem'
                  }}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', width: '100%' }}>
                    <span style={{ fontWeight: '600', minWidth: '100px' }}>
                      {sceneLabel}:
                    </span>
                    {hasVideo ? (
                      <>
                        <span style={{ color: '#155724', fontWeight: '600' }}>✅ Загружено</span>
                        {videoFragment.duration && (
                          <span style={{ color: '#666', fontSize: '0.9rem' }}>
                            (Текущая: {videoFragment.duration.toFixed(2)}s)
                          </span>
                        )}
                      </>
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
                          style={{ flex: 1 }}
                        />
                        {uploadingVideos[image.scene_order] && (
                          <span style={{ color: '#856404' }}>⏳ Загрузка...</span>
                        )}
                        {isDragging && (
                          <span style={{ color: '#667eea', fontWeight: '600' }}>📥 Перетащите видео сюда</span>
                        )}
                      </>
                    )}
                  </div>
                  {hasVideo && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.5rem' }}>
                      <label style={{ fontSize: '0.9rem', color: '#666' }}>
                        Целевая длительность (сек):
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        min="0.1"
                        value={videoFragment.target_duration || ''}
                        onChange={(e) => handleDurationChange(videoFragment.id, e.target.value)}
                        placeholder="Авто"
                        style={{
                          width: '100px',
                          padding: '0.25rem 0.5rem',
                          border: '1px solid #ddd',
                          borderRadius: '4px',
                          fontSize: '0.9rem'
                        }}
                      />
                      <span style={{ fontSize: '0.8rem', color: '#999' }}>
                        (оставьте пустым для автоматической обработки)
                      </span>
                    </div>
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
              <source src={`${STATIC_BASE_URL}/${parable.final_video_path}`} type="video/mp4" />
              Ваш браузер не поддерживает видео.
            </video>
            {parable.final_video_duration && (
              <p style={{ marginTop: '1rem', fontSize: '1.1rem', color: '#667eea' }}>
                ⏱️ Длительность: {parable.final_video_duration.toFixed(1)} секунд
              </p>
            )}
            <div className="actions" style={{ justifyContent: 'center', marginTop: '1rem' }}>
              <a
                href={`${STATIC_BASE_URL}/${parable.final_video_path}`}
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

