import axios from 'axios'

const API_BASE_URL = '/api'

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

export const generateFinalVideo = async (id) => {
  const response = await api.post(`/parables/${id}/generate-final`)
  return response.data
}

export const deleteParable = async (id) => {
  const response = await api.delete(`/parables/${id}`)
  return response.data
}

export default api

