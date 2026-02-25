export interface User {
  id: number
  email: string
  username: string
  first_name: string
  last_name: string
  niveau?: string
  filiere?: string
  date_joined?: string
  date_inscription?: string
}

export interface Epreuve {
  id: number
  titre: string
  description: string | null
  matiere: string
  niveau: string
  type_epreuve: string
  annee_academique: string
  professeur: string | null
  fichier_pdf: string | null
  taille_fichier?: number
  taille_fichier_mb?: number
  hash_fichier?: string
  nb_pages?: number
  texte_extrait?: string
  is_approved?: boolean
  uploaded_by?: number
  uploaded_by_username?: string
  fichier_url?: string
  download_url?: string
  preview_url?: string
  created_at: string
  updated_at: string
  nb_vues: number
  nb_telechargements: number
  note_moyenne_difficulte?: number
  note_moyenne_pertinence?: number
}

export interface Commentaire {
  id: number
  epreuve: number
  user: User
  contenu: string
  parent: number | null
  created_at: string
  replies?: Commentaire[]
}

export interface Evaluation {
  id: number
  epreuve: number
  user: number
  note: number
  difficulte: number
  qualite: number
  pertinence: number
  created_at: string
}

export interface Solution {
  id: number
  epreuve: number
  titre: string
  fichier_pdf: string
  uploaded_by: User
  created_at: string
}



export interface LoginCredentials {
  username: string
  password: string
}

export interface RegisterData {
  email: string
  username: string
  password: string
  first_name: string
  last_name: string
  user_type: 'student' | 'teacher'
}

export interface AuthResponse {
  access: string
  refresh: string
  user: User
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}
