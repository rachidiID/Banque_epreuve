import apiClient from './client'
import type { Evaluation } from '@/types'

interface EvaluationData {
  note_difficulte: number
  note_pertinence: number
}

export const evaluationsAPI = {
  createOrUpdateEvaluation: async (epreuveId: number, data: EvaluationData): Promise<Evaluation> => {
    const response = await apiClient.post<Evaluation>(`/evaluations/`, {
      ...data,
      epreuve: epreuveId
    })
    return response.data
  },

  getUserEvaluation: async (epreuveId: number): Promise<Evaluation | null> => {
    try {
      const response = await apiClient.get<Evaluation[]>(`/evaluations/`, {
        params: { epreuve: epreuveId }
      })
      return response.data.length > 0 ? response.data[0] : null
    } catch (error) {
      return null
    }
  },

  getEvaluationStats: async (epreuveId: number): Promise<any> => {
    try {
      const response = await apiClient.get(`/evaluations/`, {
        params: { epreuve: epreuveId }
      })
      return response.data
    } catch (error) {
      return { count: 0, avg_difficulte: 0, avg_pertinence: 0 }
    }
  },
}
