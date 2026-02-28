import { useState, useRef } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useQuery } from '@tanstack/react-query'
import { epreuvesAPI } from '@/api/epreuves'
import { authAPI } from '@/api/auth'
import { FaUser, FaBook, FaEye, FaDownload, FaCamera, FaPen, FaSave, FaTimes, FaTrash } from 'react-icons/fa'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'

const NIVEAU_OPTIONS = [
  { value: 'P1', label: 'Prépa 1' },
  { value: 'P2', label: 'Prépa 2' },
  { value: 'L3', label: 'Licence 3' },
  { value: 'M1', label: 'Master 1' },
  { value: 'M2', label: 'Master 2' },
]

const FILIERE_OPTIONS = [
  { value: 'MATH', label: 'Mathématiques' },
  { value: 'INFO', label: 'Informatique' },
  { value: 'PHYSIQUE', label: 'Physique' },
  { value: 'CHIMIE', label: 'Chimie' },
  { value: 'RO', label: 'Recherche Opérationnelle' },
  { value: 'STAT_PROB', label: 'Statistique et Probabilité' },
  { value: 'MATH_FOND', label: 'Mathématique Fondamentale' },
]

const ProfilePage = () => {
  const { user, setUser } = useAuth()
  const [isEditing, setIsEditing] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [photoPreview, setPhotoPreview] = useState<string | null>(null)
  const [photoFile, setPhotoFile] = useState<File | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [formData, setFormData] = useState({
    username: user?.username || '',
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    niveau: user?.niveau || '',
    filiere: user?.filiere || '',
  })

  const { data: recentEpreuves } = useQuery({
    queryKey: ['recent-epreuves'],
    queryFn: () => epreuvesAPI.getEpreuves({ page: 1, ordering: '-created_at' }),
  })

  if (!user) {
    return <div className="text-center py-12">Chargement...</div>
  }

  const handlePhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        toast.error('La photo ne doit pas dépasser 5 MB')
        return
      }
      setPhotoFile(file)
      const reader = new FileReader()
      reader.onload = () => setPhotoPreview(reader.result as string)
      reader.readAsDataURL(file)
    }
  }

  const handleDeletePhoto = async () => {
    try {
      await authAPI.deletePhoto()
      setUser({ ...user, photo_profil_url: null })
      setPhotoPreview(null)
      setPhotoFile(null)
      toast.success('Photo supprimée')
    } catch {
      toast.error('Erreur lors de la suppression')
    }
  }

  const handleSave = async () => {
    setIsSaving(true)
    try {
      const data = new FormData()
      Object.entries(formData).forEach(([key, value]) => {
        if (value) data.append(key, value)
      })
      if (photoFile) {
        data.append('photo_profil', photoFile)
      }
      const updatedUser = await authAPI.updateProfile(data)
      setUser(updatedUser)
      setIsEditing(false)
      setPhotoFile(null)
      setPhotoPreview(null)
      toast.success('Profil mis à jour avec succès')
    } catch (error: any) {
      const errMsg = error.response?.data
      if (errMsg && typeof errMsg === 'object') {
        const firstKey = Object.keys(errMsg)[0]
        const msg = Array.isArray(errMsg[firstKey]) ? errMsg[firstKey][0] : errMsg[firstKey]
        toast.error(`${firstKey}: ${msg}`)
      } else {
        toast.error('Erreur lors de la mise à jour')
      }
    } finally {
      setIsSaving(false)
    }
  }

  const handleCancel = () => {
    setIsEditing(false)
    setPhotoFile(null)
    setPhotoPreview(null)
    setFormData({
      username: user.username,
      first_name: user.first_name,
      last_name: user.last_name,
      niveau: user.niveau || '',
      filiere: user.filiere || '',
    })
  }

  const startEditing = () => {
    setFormData({
      username: user.username,
      first_name: user.first_name,
      last_name: user.last_name,
      niveau: user.niveau || '',
      filiere: user.filiere || '',
    })
    setIsEditing(true)
  }

  const displayPhoto = photoPreview || user.photo_profil_url

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* En-tête du profil avec gradient */}
      <div className="relative rounded-3xl overflow-hidden shadow-xl">
        {/* Bannière gradient */}
        <div className="h-40 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-500"></div>

        <div className="bg-white dark:bg-gray-800 px-6 pb-6 pt-0 relative">
          {/* Photo de profil */}
          <div className="flex flex-col sm:flex-row items-center sm:items-end gap-4 -mt-16 mb-4">
            <div className="relative group">
              <div className="w-32 h-32 rounded-full border-4 border-white dark:border-gray-800 shadow-lg overflow-hidden bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center">
                {displayPhoto ? (
                  <img src={displayPhoto} alt="Photo de profil" className="w-full h-full object-cover" />
                ) : (
                  <FaUser className="text-5xl text-white" />
                )}
              </div>
              {isEditing && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="w-32 h-32 rounded-full bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
                  >
                    <FaCamera className="text-white text-2xl" />
                  </button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    className="hidden"
                    onChange={handlePhotoChange}
                  />
                </div>
              )}
              {isEditing && user.photo_profil_url && !photoFile && (
                <button
                  onClick={handleDeletePhoto}
                  className="absolute -bottom-1 -right-1 bg-red-500 text-white rounded-full p-2 shadow-md hover:bg-red-600 transition-colors"
                  title="Supprimer la photo"
                >
                  <FaTrash className="text-xs" />
                </button>
              )}
            </div>

            <div className="text-center sm:text-left flex-1 sm:pb-2">
              {isEditing ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">Nom d'utilisateur</label>
                    <input
                      type="text"
                      value={formData.username}
                      onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">Email (non modifiable)</label>
                    <input
                      type="email"
                      value={user.email}
                      disabled
                      className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-100 dark:bg-gray-600 text-gray-500 dark:text-gray-400 cursor-not-allowed"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">Prénom</label>
                    <input
                      type="text"
                      value={formData.first_name}
                      onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">Nom</label>
                    <input
                      type="text"
                      value={formData.last_name}
                      onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  </div>
                </div>
              ) : (
                <>
                  <h1 className="text-3xl font-bold text-gray-800 dark:text-white">
                    {user.first_name || user.last_name
                      ? `${user.first_name} ${user.last_name}`.trim()
                      : user.username}
                  </h1>
                  <p className="text-gray-500 dark:text-gray-400">@{user.username}</p>
                  <p className="text-gray-400 dark:text-gray-500 text-sm">{user.email}</p>
                </>
              )}
            </div>

            {/* Boutons d'action */}
            <div className="flex gap-2 sm:pb-2">
              {isEditing ? (
                <>
                  <button
                    onClick={handleSave}
                    disabled={isSaving}
                    className="flex items-center gap-2 bg-gradient-to-r from-green-500 to-emerald-600 text-white px-5 py-2.5 rounded-xl font-semibold hover:from-green-600 hover:to-emerald-700 transition-all shadow-md disabled:opacity-50"
                  >
                    <FaSave /> {isSaving ? 'Enregistrement...' : 'Enregistrer'}
                  </button>
                  <button
                    onClick={handleCancel}
                    className="flex items-center gap-2 bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 px-5 py-2.5 rounded-xl font-semibold hover:bg-gray-300 dark:hover:bg-gray-500 transition-all"
                  >
                    <FaTimes /> Annuler
                  </button>
                </>
              ) : (
                <button
                  onClick={startEditing}
                  className="flex items-center gap-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white px-5 py-2.5 rounded-xl font-semibold hover:from-indigo-600 hover:to-purple-700 transition-all shadow-md"
                >
                  <FaPen /> Modifier
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Informations détaillées */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {isEditing ? (
          <>
            <div className="bg-gradient-to-br from-indigo-50 to-blue-50 dark:from-indigo-900/30 dark:to-blue-900/20 p-5 rounded-2xl border border-indigo-100 dark:border-indigo-800">
              <div className="text-sm font-semibold text-indigo-600 dark:text-indigo-400 mb-2">Niveau</div>
              <select
                value={formData.niveau}
                onChange={(e) => setFormData({ ...formData, niveau: e.target.value })}
                className="w-full px-3 py-2 border border-indigo-200 dark:border-indigo-700 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">-- Choisir --</option>
                {NIVEAU_OPTIONS.map((n) => (
                  <option key={n.value} value={n.value}>{n.label}</option>
                ))}
              </select>
            </div>
            <div className="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/30 dark:to-pink-900/20 p-5 rounded-2xl border border-purple-100 dark:border-purple-800">
              <div className="text-sm font-semibold text-purple-600 dark:text-purple-400 mb-2">Filière</div>
              <select
                value={formData.filiere}
                onChange={(e) => setFormData({ ...formData, filiere: e.target.value })}
                className="w-full px-3 py-2 border border-purple-200 dark:border-purple-700 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 focus:ring-2 focus:ring-purple-500"
              >
                <option value="">-- Choisir --</option>
                {FILIERE_OPTIONS.map((f) => (
                  <option key={f.value} value={f.value}>{f.label}</option>
                ))}
              </select>
            </div>
            <div className="bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-900/30 dark:to-orange-900/20 p-5 rounded-2xl border border-amber-100 dark:border-amber-800">
              <div className="text-sm font-semibold text-amber-600 dark:text-amber-400 mb-2">Membre depuis</div>
              <div className="text-xl font-bold text-gray-800 dark:text-white">
                {new Date(user.date_joined || user.date_inscription || Date.now()).toLocaleDateString('fr-FR', {
                  year: 'numeric',
                  month: 'long',
                })}
              </div>
            </div>
          </>
        ) : (
          <>
            <div className="bg-gradient-to-br from-indigo-50 to-blue-50 dark:from-indigo-900/30 dark:to-blue-900/20 p-5 rounded-2xl border border-indigo-100 dark:border-indigo-800">
              <div className="text-sm font-semibold text-indigo-600 dark:text-indigo-400 mb-1">Niveau</div>
              <div className="text-xl font-bold text-gray-800 dark:text-white">
                {user.niveau ? getNiveauLabel(user.niveau) : 'Non défini'}
              </div>
            </div>
            <div className="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/30 dark:to-pink-900/20 p-5 rounded-2xl border border-purple-100 dark:border-purple-800">
              <div className="text-sm font-semibold text-purple-600 dark:text-purple-400 mb-1">Filière</div>
              <div className="text-xl font-bold text-gray-800 dark:text-white">
                {user.filiere ? getFiliereLabel(user.filiere) : 'Non définie'}
              </div>
            </div>
            <div className="bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-900/30 dark:to-orange-900/20 p-5 rounded-2xl border border-amber-100 dark:border-amber-800">
              <div className="text-sm font-semibold text-amber-600 dark:text-amber-400 mb-1">Membre depuis</div>
              <div className="text-xl font-bold text-gray-800 dark:text-white">
                {new Date(user.date_joined || user.date_inscription || Date.now()).toLocaleDateString('fr-FR', {
                  year: 'numeric',
                  month: 'long',
                })}
              </div>
            </div>
          </>
        )}
      </div>

      {/* Statistiques colorées */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
        <h2 className="text-2xl font-bold mb-6 bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
          Mes statistiques
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-5 bg-gradient-to-br from-blue-100 to-indigo-100 dark:from-blue-900/40 dark:to-indigo-900/40 rounded-2xl">
            <div className="w-14 h-14 mx-auto mb-3 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
              <FaBook className="text-2xl text-white" />
            </div>
            <div className="text-2xl font-bold text-gray-800 dark:text-white">-</div>
            <div className="text-sm text-gray-500 dark:text-gray-400">Consultées</div>
          </div>
          <div className="text-center p-5 bg-gradient-to-br from-emerald-100 to-green-100 dark:from-emerald-900/40 dark:to-green-900/40 rounded-2xl">
            <div className="w-14 h-14 mx-auto mb-3 bg-gradient-to-br from-emerald-500 to-green-600 rounded-xl flex items-center justify-center shadow-lg">
              <FaDownload className="text-2xl text-white" />
            </div>
            <div className="text-2xl font-bold text-gray-800 dark:text-white">-</div>
            <div className="text-sm text-gray-500 dark:text-gray-400">Téléchargements</div>
          </div>
          <div className="text-center p-5 bg-gradient-to-br from-purple-100 to-violet-100 dark:from-purple-900/40 dark:to-violet-900/40 rounded-2xl">
            <div className="w-14 h-14 mx-auto mb-3 bg-gradient-to-br from-purple-500 to-violet-600 rounded-xl flex items-center justify-center shadow-lg">
              <FaEye className="text-2xl text-white" />
            </div>
            <div className="text-2xl font-bold text-gray-800 dark:text-white">-</div>
            <div className="text-sm text-gray-500 dark:text-gray-400">Évaluations</div>
          </div>
          <div className="text-center p-5 bg-gradient-to-br from-orange-100 to-amber-100 dark:from-orange-900/40 dark:to-amber-900/40 rounded-2xl">
            <div className="w-14 h-14 mx-auto mb-3 bg-gradient-to-br from-orange-500 to-amber-600 rounded-xl flex items-center justify-center shadow-lg">
              <FaBook className="text-2xl text-white" />
            </div>
            <div className="text-2xl font-bold text-gray-800 dark:text-white">-</div>
            <div className="text-sm text-gray-500 dark:text-gray-400">Commentaires</div>
          </div>
        </div>
      </div>

      {/* Épreuves récentes */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
        <h2 className="text-2xl font-bold mb-6 bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
          Épreuves disponibles
        </h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {recentEpreuves?.results.slice(0, 6).map((epreuve) => (
            <Link
              key={epreuve.id}
              to={`/epreuves/${epreuve.id}`}
              className="p-4 rounded-xl bg-gradient-to-br from-gray-50 to-white dark:from-gray-700 dark:to-gray-750 border border-gray-100 dark:border-gray-600 hover:shadow-lg hover:border-indigo-200 dark:hover:border-indigo-600 transition-all group"
            >
              <div className="flex items-center gap-2 mb-2">
                <span className="px-2 py-0.5 bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300 text-xs font-semibold rounded-full">{epreuve.niveau}</span>
                <span className="text-xs text-gray-400">{epreuve.type_epreuve}</span>
              </div>
              <h3 className="font-bold mb-2 text-gray-800 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">{epreuve.titre}</h3>
              <p className="text-sm text-gray-500 mb-2">{epreuve.matiere}</p>
              <div className="flex items-center justify-between text-xs text-gray-400">
                <span>{epreuve.annee_academique}</span>
                <div className="flex items-center space-x-3">
                  <span className="flex items-center gap-1"><FaEye className="text-blue-400" /> {epreuve.nb_vues}</span>
                  <span className="flex items-center gap-1"><FaDownload className="text-green-400" /> {epreuve.nb_telechargements}</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
        <div className="text-center mt-6">
          <Link to="/epreuves" className="inline-flex items-center gap-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white px-6 py-3 rounded-xl font-semibold hover:from-indigo-600 hover:to-purple-700 transition-all shadow-md">
            <FaBook /> Voir toutes les épreuves
          </Link>
        </div>
      </div>
    </div>
  )
}

// Fonctions utilitaires
function getNiveauLabel(niveau: string): string {
  const niveaux: Record<string, string> = {
    P1: 'Prépa 1',
    P2: 'Prépa 2',
    L3: 'Licence 3',
    M1: 'Master 1',
    M2: 'Master 2',
  }
  return niveaux[niveau] || niveau
}

function getFiliereLabel(filiere: string): string {
  const filieres: Record<string, string> = {
    MATH: 'Mathématiques',
    INFO: 'Informatique',
    PHYSIQUE: 'Physique',
    CHIMIE: 'Chimie',
    RO: 'Recherche Opérationnelle',
    STAT_PROB: 'Statistique et Probabilité',
    MATH_FOND: 'Mathématique Fondamentale',
  }
  return filieres[filiere] || filiere
}

export default ProfilePage
