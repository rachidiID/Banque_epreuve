import apiClient from './client'
import type { Epreuve } from '@/types'

interface RecommendationItem {
  epreuve_id: number
  score: number
  titre: string
  matiere: string
  niveau: string
  type_epreuve: string
  annee_academique: string
  professeur: string | null
  nb_vues: number
  nb_telechargements: number
  note_moyenne_pertinence: number | null
}

interface RecommendationResponse {
  user_id: number
  username: string
  niveau: string | null
  count: number
  recommendations: RecommendationItem[]
}

interface SimilarResponse {
  epreuve_id: number
  epreuve_titre: string
  count: number
  similar_epreuves: RecommendationItem[]
}

/** Convertit un item de recommandation en objet Epreuve-like */
function toEpreuve(item: RecommendationItem): Epreuve {
  return {
    id: item.epreuve_id,
    titre: item.titre,
    matiere: item.matiere,
    niveau: item.niveau,
    type_epreuve: item.type_epreuve,
    annee_academique: item.annee_academique,
    professeur: item.professeur,
    nb_vues: item.nb_vues || 0,
    nb_telechargements: item.nb_telechargements || 0,
    note_moyenne_pertinence: item.note_moyenne_pertinence ?? undefined,
    description: null,
    fichier_pdf: null,
    created_at: '',
    updated_at: '',
  }
}

export const recommendationsAPI = {
  getRecommendations: async (limit: number = 10): Promise<Epreuve[]> => {
    try {
      const response = await apiClient.get<RecommendationResponse>('/recommendations/personalized/', {
        params: { top_k: limit },
      })
      return response.data.recommendations.map(toEpreuve).filter(ep => ep && ep.id)
    } catch (error) {
      console.error('Error fetching recommendations:', error)
      return []
    }
  },

  getSimilarEpreuves: async (epreuveId: number, limit: number = 10): Promise<Epreuve[]> => {
    try {
      const response = await apiClient.get<SimilarResponse>('/recommendations/similar/', {
        params: { epreuve_id: epreuveId, top_k: limit },
      })
      return response.data.similar_epreuves.map(toEpreuve).filter(ep => ep && ep.id)
    } catch (error) {
      console.error('Error fetching similar epreuves:', error)
      return []
    }
  },
}
