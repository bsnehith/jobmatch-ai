import axios from 'axios'

const timeoutMs = Number(import.meta.env.VITE_API_TIMEOUT_MS || 120000)

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000/api',
  timeout: Number.isFinite(timeoutMs) ? timeoutMs : 120000,
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED') {
      return Promise.reject(
        new Error('Request timed out. Increase VITE_API_TIMEOUT_MS or try again.')
      )
    }

    const message =
      error.response?.data?.message ||
      error.response?.data?.error ||
      error.message ||
      'Request failed'

    return Promise.reject(new Error(message))
  }
)

export default apiClient
