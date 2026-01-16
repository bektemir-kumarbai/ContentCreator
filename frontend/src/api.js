import axios from 'axios'

// API base URL для запросов
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Base URL для статических файлов (изображения, аудио, видео)
export const STATIC_BASE_URL = API_BASE_URL

const api = axios.create({
  baseURL: API_BASE_URL,
})

export const getParables = async () => {
  const response = await api.get('/parables')
  return response.data
}

export const getParable = async (id) => {
  const response = await api.get(`/parables/${id}`)
  return response.data
}

export const createParable = async (data) => {
  const response = await api.post('/parables', data)
  return response.data
}

export const processParable = async (id) => {
  const response = await api.post(`/parables/${id}/process`)
  return response.data
}

export const uploadAudio = async (id, file) => {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await api.post(
    `/parables/${id}/audio/upload`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  )
  return response.data
}

export const uploadVideoFragment = async (id, sceneOrder, file) => {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await api.post(
    `/parables/${id}/videos/upload?scene_order=${sceneOrder}`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  )
  return response.data
}

export const regenerateImages = async (id) => {
  const response = await api.post(`/parables/${id}/regenerate-images`)
  return response.data
}

export const generateFinalVideo = async (id) => {
  const response = await api.post(`/parables/${id}/generate-final`)
  return response.data
}

export const deleteParable = async (id) => {
  const response = await api.delete(`/parables/${id}`)
  return response.data
}

// ═══════════════════════════════════════════════════════════════
// ENGLISH VERSION API
// ═══════════════════════════════════════════════════════════════

export const createEnglishVersion = async (id) => {
  const response = await api.post(`/parables/${id}/english/create`)
  return response.data
}

export const getEnglishParable = async (id) => {
  const response = await api.get(`/parables/${id}/english`)
  return response.data
}

export const getEnglishVersion = async (id) => {
  const response = await api.get(`/parables/${id}/english`)
  return response.data
}

export const processEnglishParable = async (id) => {
  const response = await api.post(`/parables/${id}/english/process`)
  return response.data
}

export const processEnglishVersion = async (id) => {
  const response = await api.post(`/parables/${id}/english/process`)
  return response.data
}

export const regenerateEnglishImages = async (id) => {
  const response = await api.post(`/parables/${id}/english/regenerate-images`)
  return response.data
}

export const uploadEnglishAudio = async (id, file) => {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await api.post(
    `/parables/${id}/english/audio/upload`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  )
  return response.data
}

export const uploadEnglishVideoFragment = async (id, sceneOrder, file) => {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await api.post(
    `/parables/${id}/english/videos/upload?scene_order=${sceneOrder}`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  )
  return response.data
}

export const generateEnglishFinalVideo = async (id) => {
  const response = await api.post(`/parables/${id}/english/generate-final`)
  return response.data
}

export default api

