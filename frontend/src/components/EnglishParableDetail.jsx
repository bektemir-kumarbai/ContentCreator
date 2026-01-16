import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  getEnglishParable,
  processEnglishParable,
  uploadEnglishAudio,
  uploadEnglishVideoFragment,
  generateEnglishFinalVideo,
  regenerateEnglishImages,
  updateEnglishVideoDuration
} from '../api'

const STATIC_BASE_URL = 'http://localhost:8000'

function EnglishParableDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [englishParable, setEnglishParable] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [uploadingVideos, setUploadingVideos] = useState({})
  const [uploadingAudio, setUploadingAudio] = useState(false)
  const [draggingScenes, setDraggingScenes] = useState({})
  const [generatingFinal, setGeneratingFinal] = useState(false)
  const [regeneratingImages, setRegeneratingImages] = useState(false)
  const [titleVariants, setTitleVariants] = useState([])

  useEffect(() => {
    loadEnglishParable()
    loadTitleVariants()
    const interval = setInterval(() => {
      if (englishParable && ['processing', 'generating_final'].includes(englishParable.status)) {
        loadEnglishParable()
        loadTitleVariants()
      }
    }, 5000)
    return () => clearInterval(interval)
  }, [id, englishParable?.status])

  const loadEnglishParable = async () => {
    try {
      setLoading(true)
      const data = await getEnglishParable(id)
      setEnglishParable(data)
    } catch (err) {
      setError('Error loading English version')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const loadTitleVariants = async () => {
    try {
      const response = await fetch(`http://localhost:8000/parables/${id}/english/title-variants`)
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
      await processEnglishParable(id)
      setSuccess('Processing started! This may take a few minutes...')
      setTimeout(() => loadEnglishParable(), 2000)
    } catch (err) {
      setError('Error starting processing')
      console.error(err)
    }
  }

  const handleRegenerateImages = async () => {
    try {
      setRegeneratingImages(true)
      setError(null)
      await regenerateEnglishImages(id)
      setSuccess('Image regeneration started!')
      setTimeout(() => loadEnglishParable(), 2000)
    } catch (err) {
      setError('Error regenerating images')
      console.error(err)
    } finally {
      setRegeneratingImages(false)
    }
  }

  const handleVideoUpload = async (sceneOrder, file) => {
    try {
      setUploadingVideos(prev => ({ ...prev, [sceneOrder]: true }))
      setError(null)
      await uploadEnglishVideoFragment(id, sceneOrder, file)
      setSuccess(`Video for scene ${sceneOrder + 1} uploaded!`)
      setTimeout(() => {
        loadEnglishParable()
        setSuccess(null)
      }, 2000)
    } catch (err) {
      setError(`Error uploading video for scene ${sceneOrder + 1}`)
      console.error(err)
    } finally {
      setUploadingVideos(prev => ({ ...prev, [sceneOrder]: false }))
    }
  }

  const handleDurationChange = async (videoFragmentId, targetDuration) => {
    try {
      const value = targetDuration === '' ? null : parseFloat(targetDuration)
      await updateEnglishVideoDuration(id, videoFragmentId, value)
      await loadEnglishParable()
    } catch (err) {
      setError('Error updating duration')
      console.error(err)
    }
  }

  const handleAudioUpload = async (file) => {
    try {
      setUploadingAudio(true)
      setError(null)
      await uploadEnglishAudio(id, file)
      setSuccess('Audio uploaded successfully!')
      setTimeout(() => {
        loadEnglishParable()
        setSuccess(null)
      }, 2000)
    } catch (err) {
      setError('Error uploading audio')
      console.error(err)
    } finally {
      setUploadingAudio(false)
    }
  }

  const handleGenerateFinal = async () => {
    try {
      setGeneratingFinal(true)
      setError(null)
      await generateEnglishFinalVideo(id)
      setSuccess('Final video generation started!')
      setTimeout(() => loadEnglishParable(), 2000)
    } catch (err) {
      setError('Error generating final video')
      console.error(err)
    } finally {
      setGeneratingFinal(false)
    }
  }

  const getStatusText = (status) => {
    const statusMap = {
      draft: 'Draft',
      processing: 'Processing...',
      awaiting_videos: 'Awaiting Videos',
      generating_final: 'Generating Video...',
      completed: 'Completed',
      error: 'Error'
    }
    return statusMap[status] || status
  }

  if (loading) {
    return <div className="loading">Loading...</div>
  }

  if (!englishParable) {
    return <div className="error">English version not found</div>
  }

  return (
    <div>
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem' }}>
        <button className="btn" onClick={() => navigate(`/parable/${id}`)}>
          ← Back to Russian version
        </button>
        <button className="btn" onClick={() => navigate('/')}>
          🏠 Home
        </button>
      </div>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h2>🇬🇧 English Version</h2>
            <span className={`status ${englishParable.status}`}>
              {getStatusText(englishParable.status)}
            </span>
          </div>
        </div>

        {error && <div className="error">{error}</div>}
        {success && <div className="success">{success}</div>}

        {englishParable.status === 'draft' && (
          <div className="actions">
            <button className="btn btn-primary" onClick={handleProcess}>
              🚀 Start Processing
            </button>
          </div>
        )}
      </div>

      {englishParable.text_translated && (
        <div className="card">
          <h3>Translated Text</h3>
          <p style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6', color: '#555' }}>
            {englishParable.text_translated}
          </p>
        </div>
      )}

      {englishParable.hook_text && (
        <div className="card" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
          <h3>⚡ Hook (first 3 seconds)</h3>
          <p style={{ fontSize: '1.2em', fontWeight: 'bold', lineHeight: '1.6' }}>
            {englishParable.hook_text}
          </p>
          <small style={{ opacity: 0.9 }}>Catchy opening for maximum retention</small>
        </div>
      )}

      {englishParable.text_for_tts && (
        <div className="card">
          <h3>Text for Voice-over (with emotional tags)</h3>
          <p style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6', color: '#555' }}>
            {englishParable.text_for_tts}
          </p>
        </div>
      )}

      {titleVariants.length > 0 && (
        <div className="card">
          <h3>📊 A/B Testing Titles</h3>
          <p style={{ color: '#666', marginBottom: '1rem' }}>
            LLM generated 5 variants and automatically selected the best one:
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
                    ✓ SELECTED BY AI
                  </span>
                )}
                <div style={{ fontSize: '0.75rem', color: '#888', marginBottom: '0.25rem', textTransform: 'uppercase' }}>
                  {variant.variant_type === 'question' && '❓ Question'}
                  {variant.variant_type === 'intrigue' && '🔮 Intrigue'}
                  {variant.variant_type === 'emotion' && '💔 Emotion'}
                  {variant.variant_type === 'numbers' && '🔢 Numbers'}
                  {variant.variant_type === 'provocation' && '⚡ Provocation'}
                </div>
                <div style={{ fontSize: '1.1rem', fontWeight: variant.is_selected ? 'bold' : 'normal' }}>
                  {variant.variant_text}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {(englishParable.youtube_title || englishParable.youtube_description) && (
        <div className="card">
          <div className="metadata-section">
            <h3>YouTube Metadata</h3>
            {englishParable.youtube_title && (
              <p><strong>Title:</strong> {englishParable.youtube_title}</p>
            )}
            {englishParable.youtube_description && (
              <p><strong>Description:</strong> {englishParable.youtube_description}</p>
            )}
            {englishParable.youtube_hashtags && (
              <p><strong>Hashtags:</strong> {englishParable.youtube_hashtags}</p>
            )}
          </div>
        </div>
      )}

      {englishParable.image_prompts && englishParable.image_prompts.length > 0 && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3>Generated Images</h3>
            <button 
              className="btn btn-primary" 
              onClick={handleRegenerateImages}
              disabled={regeneratingImages}
              style={{ fontSize: '0.9rem', padding: '0.5rem 1rem' }}
            >
              {regeneratingImages ? '⏳ Generating...' : '🔄 Regenerate Images'}
            </button>
          </div>
          
          {englishParable.generated_images && englishParable.generated_images.length > 0 ? (
            <>
              <p style={{ color: '#666', marginBottom: '1rem' }}>
                Generated {englishParable.generated_images.length} of {englishParable.image_prompts.length} images
              </p>
              <div className="images-grid">
                {englishParable.generated_images
                  .sort((a, b) => a.scene_order - b.scene_order) // Сортируем: -1 (хук) первым, потом 0, 1, 2...
                  .map((image) => {
                  const prompt = englishParable.image_prompts.find(p => p.scene_order === image.scene_order)
                  
                  // Определяем название сцены
                  const sceneLabel = image.scene_order === -1 ? '⚡ HOOK' : `Scene ${image.scene_order + 1}`
                  
                  return (
                    <div key={image.id} className="image-item">
                      <img src={`${STATIC_BASE_URL}/${image.image_path}`} alt={sceneLabel} />
                      <div className="scene-number">{sceneLabel}</div>
                      
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
                ⚠️ Images not generated
              </p>
              <p style={{ color: '#856404', marginBottom: '1rem' }}>
                Prompts ready: {englishParable.image_prompts.length}
              </p>
              <button 
                className="btn btn-primary" 
                onClick={handleRegenerateImages}
                disabled={regeneratingImages}
              >
                {regeneratingImages ? '⏳ Generating...' : '🎨 Generate Images'}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Audio Section - Always show */}
      <div className="card">
        <h3>🎙️ Audio Voice-over</h3>
        
        {englishParable.audio_files && englishParable.audio_files.length > 0 ? (
          <>
            <div className="audio-player">
              <audio controls>
                <source src={`${STATIC_BASE_URL}/${englishParable.audio_files[0].audio_path}`} type="audio/mpeg" />
                Your browser does not support audio.
              </audio>
              {englishParable.audio_files[0].duration && (
                <p style={{ marginTop: '0.5rem', color: '#666' }}>
                  Duration: {englishParable.audio_files[0].duration.toFixed(1)} seconds
                </p>
              )}
            </div>
            
            <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
              <p style={{ color: '#666', marginBottom: '0.5rem' }}>Replace audio:</p>
              <input 
                type="file" 
                accept="audio/*" 
                onChange={(e) => e.target.files[0] && handleAudioUpload(e.target.files[0])} 
                disabled={uploadingAudio}
              />
              {uploadingAudio && <span style={{ marginLeft: '1rem', color: '#856404' }}>⏳ Uploading...</span>}
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
              ⏸️ No audio file yet
            </p>
            <p style={{ color: '#856404', marginBottom: '1rem' }}>
              Upload audio file or generate it automatically
            </p>
            <input 
              type="file" 
              accept="audio/*" 
              onChange={(e) => e.target.files[0] && handleAudioUpload(e.target.files[0])} 
              disabled={uploadingAudio}
            />
            {uploadingAudio && <span style={{ marginLeft: '1rem', color: '#856404' }}>⏳ Uploading...</span>}
          </div>
        )}
      </div>

      {/* Video Upload Section - Always show if images exist */}
      {englishParable.generated_images && englishParable.generated_images.length > 0 && (
        <div className="card">
          <h3>📹 Upload Video Fragments</h3>
          <p style={{ color: '#666', marginBottom: '1rem' }}>
            Send each image to your video generation model (Runway, Pika, etc.) using the prompts, then upload or drag & drop the videos here.
          </p>
          <div className="upload-section">
            {englishParable.generated_images.map((image) => {
              const videoFragment = englishParable.video_fragments?.find(
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
                ? '⚡ HOOK' 
                : `Scene ${image.scene_order + 1}`
              
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
                        <span style={{ color: '#155724', fontWeight: '600' }}>✅ Uploaded</span>
                        {videoFragment.duration && (
                          <span style={{ color: '#666', fontSize: '0.9rem' }}>
                            (Current: {videoFragment.duration.toFixed(2)}s)
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
                          <span style={{ color: '#856404' }}>⏳ Uploading...</span>
                        )}
                        {isDragging && (
                          <span style={{ color: '#667eea', fontWeight: '600' }}>📥 Drop video here</span>
                        )}
                      </>
                    )}
                  </div>
                  {hasVideo && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.5rem' }}>
                      <label style={{ fontSize: '0.9rem', color: '#666' }}>
                        Target duration (sec):
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        min="0.1"
                        value={videoFragment.target_duration || ''}
                        onChange={(e) => handleDurationChange(videoFragment.id, e.target.value)}
                        placeholder="Auto"
                        style={{
                          width: '100px',
                          padding: '0.25rem 0.5rem',
                          border: '1px solid #ddd',
                          borderRadius: '4px',
                          fontSize: '0.9rem'
                        }}
                      />
                      <span style={{ fontSize: '0.8rem', color: '#999' }}>
                        (leave empty for automatic processing)
                      </span>
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          {englishParable.video_fragments?.length === englishParable.generated_images.length && (
            <div className="actions">
              <button
                className="btn btn-success"
                onClick={handleGenerateFinal}
                disabled={generatingFinal}
              >
                {generatingFinal ? '⏳ Generating...' : '🎬 Generate Final Video'}
              </button>
            </div>
          )}
        </div>
      )}

      {englishParable.final_video_path && (
        <div className="card">
          <h3>Final Video</h3>
          <div className="video-player">
            <video controls>
              <source src={`${STATIC_BASE_URL}/${englishParable.final_video_path}`} type="video/mp4" />
              Your browser does not support video.
            </video>
            {englishParable.final_video_duration && (
              <p style={{ marginTop: '1rem', fontSize: '1.1rem', color: '#667eea' }}>
                ⏱️ Duration: {englishParable.final_video_duration.toFixed(1)} seconds
              </p>
            )}
            <div className="actions" style={{ justifyContent: 'center', marginTop: '1rem' }}>
              <a
                href={`${STATIC_BASE_URL}/${englishParable.final_video_path}`}
                download="english_version.mp4"
                className="btn btn-success"
              >
                ⬇️ Download Video
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default EnglishParableDetail

