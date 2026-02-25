import apiClient from './client'
import type { Epreuve } from '@/types'

interface RecommendationResponse {
  user_id: number
  username: string
  niveau: string | null
  count: number
  recommendations: Array<{
    epreuve: Epreuve
    score: number
    reason: string
  }>
}

export const recommendationsAPI = {
  getRecommendations: async (limit: number = 10): Promise<Epreuve[]> => {
    try {
      const response = await apiClient.get<RecommendationResponse>('/recommendations/personalized/', {
        params: { top_k: limit },
      })
      // Extraire uniquement les épreuves et filtrer les valeurs nulles/undefined
      return response.data.recommendations
        .map(rec => rec.epreuve)
        .filter(epreuve => epreuve && epreuve.id)
    } catch (error) {
      console.error('Error fetching recommendations:', error)
      return []
    }
  },

  getSimilarEpreuves: async (epreuveId: number, limit: number = 10): Promise<Epreuve[]> => {
    try {
      const response = await apiClient.get<{ similar_items: Array<{ epreuve: Epreuve }> }>('/recommendations/similar/', {
        params: { epreuve_id: epreuveId, top_k: limit },
      })
      return response.data.similar_items
        .map(item => item.epreuve)
        .filter(epreuve => epreuve && epreuve.id)
    } catch (error) {
      console.error('Error fetching similar epreuves:', error)
      return []
    }
  },
}
