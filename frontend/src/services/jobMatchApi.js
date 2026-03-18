import apiClient from './apiClient'

export async function evaluateCandidate(payload) {
  const { data } = await apiClient.post('/evaluate', payload)
  return data
}

export async function listCandidates() {
  const { data } = await apiClient.get('/candidates')
  return data
}

export async function topCandidates(limit = 3) {
  const { data } = await apiClient.get('/candidates/top', {
    params: { limit },
  })
  return data
}

export async function getCandidate(name) {
  const { data } = await apiClient.get(`/candidates/${encodeURIComponent(name)}`)
  return data
}

export async function deleteCandidate(name) {
  const { data } = await apiClient.delete(`/candidates/${encodeURIComponent(name)}`)
  return data
}
