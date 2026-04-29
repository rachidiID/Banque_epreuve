import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { authAPI } from '@/api/auth'
import toast from 'react-hot-toast'
import { FaUser, FaArrowRight, FaTimes } from 'react-icons/fa'

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

interface ProfileCompletionModalProps {
  onClose: () => void
}

/**
 * Modal affiché lors de la première connexion si le profil est incomplet.
 * Permet de renseigner niveau et filière pour améliorer les recommandations.
 */
const ProfileCompletionModal = ({ onClose }: ProfileCompletionModalProps) => {
  const { user, setUser } = useAuth()
  const navigate = useNavigate()
  const [niveau, setNiveau] = useState(user?.niveau || '')
  const [filiere, setFiliere] = useState(user?.filiere || '')
  const [isSaving, setIsSaving] = useState(false)

  const handleSave = async () => {
    if (!niveau || !filiere) {
      toast.error('Veuillez sélectionner votre niveau et votre filière')
      return
    }
    setIsSaving(true)
    try {
      const formData = new FormData()
      formData.append('niveau', niveau)
      formData.append('filiere', filiere)
      const updatedUser = await authAPI.updateProfile(formData)
      setUser(updatedUser)
      toast.success('Profil complété ! Les recommandations sont maintenant personnalisées.')
      onClose()
    } catch {
      toast.error('Erreur lors de la sauvegarde')
    } finally {
      setIsSaving(false)
    }
  }

  const handleSkip = () => {
    // Marquer comme ignoré pour 7 jours
    localStorage.setItem('profile_completion_skipped', Date.now().toString())
    onClose()
  }

  const handleGoToProfile = () => {
    onClose()
    navigate('/profile')
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-md w-full p-6 relative animate-in fade-in zoom-in duration-300">
        <button
          onClick={handleSkip}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
        >
          <FaTimes />
        </button>

        <div className="text-center mb-6">
          <div className="w-16 h-16 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center mx-auto mb-4">
            <FaUser className="text-2xl text-primary-600 dark:text-primary-400" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Complétez votre profil
          </h2>
          <p className="text-gray-500 dark:text-gray-400 mt-2 text-sm">
            Renseignez votre niveau et filière pour obtenir des recommandations
            d'épreuves personnalisées.
          </p>
        </div>

        <div className="space-y-4 mb-6">
          <div>
            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Votre niveau académique *
            </label>
            <div className="grid grid-cols-5 gap-2">
              {NIVEAU_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setNiveau(opt.value)}
                  className={`py-2 px-1 rounded-xl text-xs font-semibold transition-all ${
                    niveau === opt.value
                      ? 'bg-primary-600 text-white shadow-md'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-primary-50 dark:hover:bg-primary-900/30'
                  }`}
                >
                  {opt.value}
                </button>
              ))}
            </div>
            {niveau && (
              <p className="text-xs text-primary-600 mt-1">
                {NIVEAU_OPTIONS.find((o) => o.value === niveau)?.label}
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Votre filière *
            </label>
            <div className="grid grid-cols-1 gap-2">
              {FILIERE_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setFiliere(opt.value)}
                  className={`py-2.5 px-4 rounded-xl text-sm font-medium transition-all text-left ${
                    filiere === opt.value
                      ? 'bg-primary-600 text-white shadow-md'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-primary-50 dark:hover:bg-primary-900/30'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="flex gap-3">
          <button
            onClick={handleSave}
            disabled={isSaving || !niveau || !filiere}
            className="flex-1 btn-primary flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSaving ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
            ) : (
              <>
                <span>Enregistrer</span>
                <FaArrowRight className="text-sm" />
              </>
            )}
          </button>
          <button
            onClick={handleSkip}
            className="px-4 py-2 text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
          >
            Plus tard
          </button>
        </div>

        <div className="mt-4 text-center">
          <button
            onClick={handleGoToProfile}
            className="text-xs text-primary-600 hover:text-primary-700 dark:text-primary-400"
          >
            Gérer mon profil complet →
          </button>
        </div>
      </div>
    </div>
  )
}

export default ProfileCompletionModal
