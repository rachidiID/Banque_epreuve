import { useAuth } from '@/contexts/AuthContext'
import { useQuery } from '@tanstack/react-query'
import { epreuvesAPI } from '@/api/epreuves'
import { FaUser, FaBook, FaEye, FaDownload } from 'react-icons/fa'
import { Link } from 'react-router-dom'

const ProfilePage = () => {
  const { user } = useAuth()

  // Récupérer les épreuves consultées par l'utilisateur
  const { data: recentEpreuves } = useQuery({
    queryKey: ['recent-epreuves'],
    queryFn: () => epreuvesAPI.getEpreuves({ page: 1, ordering: '-created_at' }),
  })

  if (!user) {
    return <div className="text-center py-12">Chargement...</div>
  }

  return (
    <div className="space-y-8">
      {/* En-tête du profil */}
      <div className="card">
        <div className="flex items-center space-x-4 mb-6">
          <div className="w-20 h-20 rounded-full bg-primary-100 flex items-center justify-center">
            <FaUser className="text-4xl text-primary-600" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">{user.username}</h1>
            <p className="text-gray-600">{user.email}</p>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-4">
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="text-sm text-gray-600 mb-1">Niveau</div>
            <div className="text-xl font-bold">
              {user.niveau ? getNiveauLabel(user.niveau) : 'Non défini'}
            </div>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="text-sm text-gray-600 mb-1">Filière</div>
            <div className="text-xl font-bold">
              {user.filiere ? getFiliereLabel(user.filiere) : 'Non définie'}
            </div>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="text-sm text-gray-600 mb-1">Membre depuis</div>
            <div className="text-xl font-bold">
              {new Date(user.date_joined || Date.now()).toLocaleDateString('fr-FR', {
                year: 'numeric',
                month: 'long',
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Statistiques */}
      <div className="card">
        <h2 className="text-2xl font-bold mb-6">Mes statistiques</h2>
        <div className="grid md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <FaBook className="text-3xl text-blue-600 mx-auto mb-2" />
            <div className="text-2xl font-bold">-</div>
            <div className="text-sm text-gray-600">Épreuves consultées</div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <FaDownload className="text-3xl text-green-600 mx-auto mb-2" />
            <div className="text-2xl font-bold">-</div>
            <div className="text-sm text-gray-600">Téléchargements</div>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <FaEye className="text-3xl text-purple-600 mx-auto mb-2" />
            <div className="text-2xl font-bold">-</div>
            <div className="text-sm text-gray-600">Évaluations données</div>
          </div>
          <div className="text-center p-4 bg-orange-50 rounded-lg">
            <FaBook className="text-3xl text-orange-600 mx-auto mb-2" />
            <div className="text-2xl font-bold">-</div>
            <div className="text-sm text-gray-600">Commentaires</div>
          </div>
        </div>
      </div>

      {/* Épreuves récentes */}
      <div className="card">
        <h2 className="text-2xl font-bold mb-6">Épreuves disponibles</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {recentEpreuves?.results.slice(0, 6).map((epreuve) => (
            <Link
              key={epreuve.id}
              to={`/epreuves/${epreuve.id}`}
              className="card hover:shadow-lg transition-shadow"
            >
              <h3 className="font-bold mb-2">{epreuve.titre}</h3>
              <p className="text-sm text-gray-600 mb-2">{epreuve.matiere}</p>
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span>{epreuve.niveau}</span>
                <span>{epreuve.annee_academique}</span>
              </div>
              <div className="flex items-center space-x-4 text-xs text-gray-600 mt-2">
                <span>👁 {epreuve.nb_vues}</span>
                <span>⬇ {epreuve.nb_telechargements}</span>
              </div>
            </Link>
          ))}
        </div>
        <div className="text-center mt-6">
          <Link to="/epreuves" className="btn-primary">
            Voir toutes les épreuves
          </Link>
        </div>
      </div>
    </div>
  )
}

// Fonctions utilitaires
function getNiveauLabel(niveau: string): string {
  const niveaux: Record<string, string> = {
    L1: 'Licence 1',
    L2: 'Licence 2',
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
  }
  return filieres[filiere] || filiere
}

export default ProfilePage
