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
    // Ouvrir le lien de téléchargement dans un nouvel onglet
    // (gère la redirection Cloudinary automatiquement)
    const token = localStorage.getItem('access_token')
    try {
      const response = await apiClient.get(`/epreuves/${id}/download/`, {
        maxRedirects: 0,
        validateStatus: (status: number) => status >= 200 && status < 400,
      })
      // Si redirection (302), ouvrir l'URL Cloudinary directement
      if (response.status >= 300 && response.headers?.location) {
        window.open(response.headers.location, '_blank')
      }
    } catch (error: any) {
      // Axios traite les redirections automatiquement dans le navigateur
      // Fallback : ouvrir directement en ajoutant le token
      const downloadUrl = `/api/epreuves/${id}/download/`
      const link = document.createElement('a')
      link.href = downloadUrl
      link.target = '_blank'
      document.body.appendChild(link)
      link.click()
      link.remove()
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
