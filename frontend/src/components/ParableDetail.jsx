import { useState, useEffect } from 'react'
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
  const [uploadingAudio, setUploadingAudio] = useState(false)
  const [generatingFinal, setGeneratingFinal] = useState(false)
  const [regeneratingImages, setRegeneratingImages] = useState(false)
  const [showEnglish, setShowEnglish] = useState(false)

  useEffect(() => {
    loadParable()
    loadEnglishVersion()
    // Автообновление каждые 5 секунд если идёт обработка
    const interval = setInterval(() => {
      if (parable && ['processing', 'generating_final'].includes(parable.status)) {
        loadParable()
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
                {parable.generated_images.map((image) => (
                  <div key={image.id} className="image-item">
                    <img src={`${STATIC_BASE_URL}/${image.image_path}`} alt={`Сцена ${image.scene_order + 1}`} />
                    <div className="scene-number">Сцена {image.scene_order + 1}</div>
                  </div>
                ))}
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

      {/* ENGLISH VERSION */}
      {/* Английская версия - всегда доступна */}
      <div className="card" style={{ marginTop: '2rem', borderTop: '3px solid #007bff' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2 style={{ color: '#007bff' }}>🇬🇧 English Version</h2>
          <button
            className="btn btn-secondary"
            onClick={() => setShowEnglish(!showEnglish)}
            style={{ fontSize: '0.9rem', padding: '0.5rem 1rem' }}
          >
            {showEnglish ? '▲ Скрыть' : '▼ Показать'}
          </button>
        </div>

        {showEnglish && (
          <>
            {!englishVersion ? (
              <div style={{ padding: '2rem', textAlign: 'center', backgroundColor: '#e7f3ff', borderRadius: '8px', border: '1px solid #007bff' }}>
                <p style={{ color: '#004085', fontSize: '1.1rem', marginBottom: '1rem' }}>
                  📝 Английская версия ещё не создана
                </p>
                <button className="btn btn-primary" onClick={handleCreateEnglishVersion}>
                  🌍 Создать английскую версию
                </button>
              </div>
              ) : (
                <>
                  <div style={{ padding: '1rem', backgroundColor: englishVersion.status === 'error' ? '#f8d7da' : '#d1ecf1', borderRadius: '8px', marginBottom: '1rem' }}>
                    <p style={{ margin: 0 }}>
                      <strong>Статус:</strong> {getStatusText(englishVersion.status)}
                      {englishVersion.current_step > 0 && ` (Шаг ${englishVersion.current_step}/5)`}
                    </p>
                  </div>

                  {englishVersion.status === 'draft' && (
                    <button className="btn btn-primary" onClick={handleProcessEnglishVersion} style={{ marginBottom: '1rem' }}>
                      🚀 Запустить обработку
                    </button>
                  )}

                  {englishVersion.text_for_tts && (
                    <div style={{ padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '8px', marginBottom: '1rem' }}>
                      <h4>📝 English TTS Text</h4>
                      <p style={{ whiteSpace: 'pre-wrap' }}>{englishVersion.text_for_tts}</p>
                    </div>
                  )}

                  {englishVersion.generated_images && englishVersion.generated_images.length > 0 && (
                    <div style={{ marginBottom: '1rem' }}>
                      <h4>🎨 Images ({englishVersion.generated_images.length})</h4>
                      <div className="images-grid">
                        {englishVersion.generated_images.map((image) => (
                          <div key={image.id} className="image-item">
                            <img src={`${STATIC_BASE_URL}/${image.image_path}`} alt={`Scene ${image.scene_order + 1}`} />
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Audio - всегда показываем */}
                  <div style={{ padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '8px', marginBottom: '1rem' }}>
                    <h4>🎙️ Audio</h4>
                    {englishVersion.audio_files?.length > 0 ? (
                      <>
                        <audio controls>
                          <source src={`${STATIC_BASE_URL}/${englishVersion.audio_files[0].audio_path}`} type="audio/mpeg" />
                        </audio>
                        <div style={{ marginTop: '1rem' }}>
                          <p style={{ color: '#666', marginBottom: '0.5rem' }}>Replace audio:</p>
                          <input type="file" accept="audio/*" onChange={(e) => e.target.files[0] && handleEnglishAudioUpload(e.target.files[0])} disabled={uploadingAudio} />
                          {uploadingAudio && <span style={{ marginLeft: '1rem' }}>⏳ Uploading...</span>}
                        </div>
                      </>
                    ) : (
                      <div>
                        <p style={{ color: '#856404' }}>⏸️ Waiting for audio</p>
                        <input type="file" accept="audio/*" onChange={(e) => e.target.files[0] && handleEnglishAudioUpload(e.target.files[0])} disabled={uploadingAudio} />
                        {uploadingAudio && <span style={{ marginLeft: '1rem' }}>⏳ Uploading...</span>}
                      </div>
                    )}
                  </div>

                  {/* Video Fragments - всегда показываем если есть изображения */}
                  {englishVersion.generated_images && englishVersion.generated_images.length > 0 && (
                    <div style={{ padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '8px', marginBottom: '1rem' }}>
                      <h4>📹 Upload Video Fragments</h4>
                      <p style={{ color: '#666', marginBottom: '1rem' }}>
                        Send each image to Grok to create video, then upload the videos here.
                      </p>
                      <div className="upload-section">
                        {englishVersion.generated_images.map((image) => {
                          const hasVideo = englishVersion.video_fragments?.some(
                            vf => vf.scene_order === image.scene_order
                          )
                          return (
                            <div key={image.id} className="upload-item">
                              <span style={{ fontWeight: '600', minWidth: '100px' }}>
                                Scene {image.scene_order + 1}:
                              </span>
                              {hasVideo ? (
                                <span style={{ color: '#155724', fontWeight: '600' }}>✅ Uploaded</span>
                              ) : (
                                <>
                                  <input
                                    type="file"
                                    accept="video/*"
                                    onChange={(e) => {
                                      if (e.target.files[0]) {
                                        handleEnglishVideoUpload(image.scene_order, e.target.files[0])
                                      }
                                    }}
                                    disabled={uploadingVideos[`en_${image.scene_order}`]}
                                  />
                                  {uploadingVideos[`en_${image.scene_order}`] && (
                                    <span style={{ color: '#856404' }}>Uploading...</span>
                                  )}
                                </>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )}

                  {/* Generate Final Video - показываем если все видео загружены */}
                  {englishVersion.video_fragments?.length > 0 && 
                   englishVersion.video_fragments?.length === englishVersion.generated_images?.length && (
                    <div style={{ padding: '1rem', backgroundColor: '#d4edda', borderRadius: '8px', marginBottom: '1rem' }}>
                      <p style={{ color: '#155724', marginBottom: '1rem' }}>
                        ✅ All video fragments uploaded! Ready to generate final video.
                      </p>
                      <button
                        className="btn btn-success"
                        onClick={handleGenerateEnglishFinal}
                        disabled={generatingFinal}
                      >
                        {generatingFinal ? '⏳ Generating...' : '🎬 Generate Final Video'}
                      </button>
                    </div>
                  )}

                  {englishVersion.final_video_path && (
                    <div style={{ padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
                      <h4>🎬 Final Video</h4>
                      <video controls style={{ width: '100%', maxWidth: '600px' }}>
                        <source src={`${STATIC_BASE_URL}/${englishVersion.final_video_path}`} type="video/mp4" />
                      </video>
                      {englishVersion.final_video_duration && (
                        <p style={{ marginTop: '0.5rem', color: '#666' }}>
                          Duration: {englishVersion.final_video_duration.toFixed(1)} seconds
                        </p>
                      )}
                      <div style={{ marginTop: '1rem' }}>
                        <a
                          href={`${STATIC_BASE_URL}/${englishVersion.final_video_path}`}
                          download="english_video.mp4"
                          className="btn btn-success"
                        >
                          ⬇️ Download Video
                        </a>
                      </div>
                    </div>
                  )}
                </>
              )}
            </>
          )}
        </div>
    </div>
  )
}

export default ParableDetail

