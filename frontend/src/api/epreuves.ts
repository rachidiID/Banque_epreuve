import apiClient from './client'
import type { Epreuve, PaginatedResponse } from '@/types'

interface EpreuvesParams {
  page?: number
  search?: string
  matiere?: string
  niveau?: string
  type_epreuve?: string
  annee_academique?: string
  ordering?: string
}

export const epreuvesAPI = {
  getEpreuves: async (params: EpreuvesParams = {}): Promise<PaginatedResponse<Epreuve>> => {
    const response = await apiClient.get<PaginatedResponse<Epreuve>>('/epreuves/', { params })
    return response.data
  },

  getEpreuve: async (id: number): Promise<Epreuve> => {
    const response = await apiClient.get<Epreuve>(`/epreuves/${id}/`)
    return response.data
  },

  createEpreuve: async (data: FormData): Promise<Epreuve> => {
    const response = await apiClient.post<Epreuve>('/epreuves/', data, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  uploadEpreuve: async (data: FormData): Promise<any> => {
    const response = await apiClient.post('/epreuves/upload/', data, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    // Le backend retourne { message: string, epreuve: Epreuve }
    return response.data
  },

  updateEpreuve: async (id: number, data: Partial<Epreuve>): Promise<Epreuve> => {
    const response = await apiClient.patch<Epreuve>(`/epreuves/${id}/`, data)
    return response.data
  },

  deleteEpreuve: async (id: number): Promise<void> => {
    await apiClient.delete(`/epreuves/${id}/`)
  },

  downloadEpreuve: async (id: number): Promise<void> => {
    try {
      // Appel authentifié à l'endpoint download (retourne JSON avec l'URL)
      const response = await apiClient.get(`/epreuves/${id}/download/`)
      const data = response.data
      
      if (data.url) {
        // URL Cloudinary : ouvrir directement dans un nouvel onglet
        window.open(data.url, '_blank')
      } else {
        // Réponse non-JSON (fichier local servi directement) — fallback blob
        throw new Error('local-file')
      }
    } catch (error: any) {
      // Fallback : utiliser les données détail de l'épreuve
      try {
        const response = await apiClient.get(`/epreuves/${id}/`)
        const fileUrl = response.data.fichier_url || response.data.preview_url
        if (fileUrl && fileUrl.startsWith('http')) {
          window.open(fileUrl, '_blank')
          return
        }
      } catch (e) {
        // ignore
      }
      console.error('Erreur téléchargement:', error)
      throw error
    }
  },

  previewEpreuve: async (id: number): Promise<string> => {
    // Récupérer l'URL du PDF pour le viewer
    const response = await apiClient.get(`/epreuves/${id}/`)
    return response.data.preview_url || response.data.fichier_url || ''
  },

  recordView: async (id: number): Promise<void> => {
    await apiClient.post(`/epreuves/${id}/view/`)
  },

  getSimilarEpreuves: async (id: number): Promise<Epreuve[]> => {
    try {
      const response = await apiClient.get('/recommendations/similar/', {
        params: { epreuve_id: id, top_k: 10 }
      })
      
      // Vérifier la structure de la réponse
      if (response.data?.similar_items && Array.isArray(response.data.similar_items)) {
        return response.data.similar_items
          .map((item: any) => item.epreuve)
          .filter((epreuve: any) => epreuve && epreuve.id)
      }
      
      // Si la réponse est directement un tableau d'épreuves
      if (Array.isArray(response.data)) {
        return response.data.filter((epreuve: any) => epreuve && epreuve.id)
      }
      
      return []
    } catch (error) {
      console.error('Error fetching similar epreuves:', error)
      return []
    }
  },
}
