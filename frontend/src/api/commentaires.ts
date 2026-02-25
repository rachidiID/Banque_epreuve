import apiClient from './client'
import type { Commentaire } from '@/types'

export const commentairesAPI = {
  getCommentaires: async (epreuveId: number): Promise<Commentaire[]> => {
    try {
      const response = await apiClient.get<Commentaire[]>(`/commentaires/`, {
        params: { epreuve: epreuveId }
      })
      // Vérifier si la réponse est un tableau
      if (Array.isArray(response.data)) {
        return response.data
      }
      // Si c'est un objet paginé, extraire les résultats
      if (response.data && typeof response.data === 'object' && 'results' in response.data) {
        return (response.data as any).results || []
      }
      return []
    } catch (error) {
      console.error('Error fetching commentaires:', error)
      return []
    }
  },

  createCommentaire: async (epreuveId: number, data: { contenu: string; parent?: number }): Promise<Commentaire> => {
    const response = await apiClient.post<Commentaire>(`/commentaires/`, {
      ...data,
      epreuve: epreuveId
    })
    return response.data
  },

  updateCommentaire: async (id: number, contenu: string): Promise<Commentaire> => {
    const response = await apiClient.patch<Commentaire>(`/commentaires/${id}/`, { contenu })
    return response.data
  },

  deleteCommentaire: async (id: number): Promise<void> => {
    await apiClient.delete(`/commentaires/${id}/`)
  },
}
