import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '@/contexts/AuthContext'
import { epreuvesAPI } from '@/api/epreuves'
import { recommendationsAPI } from '@/api/recommendations'
import { FaBook, FaSearch, FaStar, FaUsers } from 'react-icons/fa'

const HomePage = () => {
  const { isAuthenticated, user } = useAuth()

  const { data: recentEpreuves } = useQuery({
    queryKey: ['epreuves', 'recent'],
    queryFn: () => epreuvesAPI.getEpreuves({ ordering: '-created_at', page: 1 }),
  })

  const { data: recommendations } = useQuery({
    queryKey: ['recommendations', user?.id],
    queryFn: () => recommendationsAPI.getRecommendations(5),
    enabled: isAuthenticated,
  })

  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <section className="text-center py-16 bg-gradient-to-r from-primary-600 to-primary-800 text-white rounded-lg">
        <h1 className="text-5xl font-bold mb-4">Banque d'Épreuves Collaborative</h1>
        <p className="text-xl mb-8">
          Partagez, découvrez et préparez-vous avec des milliers d'épreuves académiques
        </p>
        <Link to="/epreuves" className="bg-white text-primary-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 inline-block">
          Explorer les épreuves
        </Link>
      </section>

      {/* Features */}
      <section className="grid md:grid-cols-3 gap-8">
        <div className="card text-center">
          <FaBook className="text-5xl text-primary-600 mx-auto mb-4" />
          <h3 className="text-xl font-bold mb-2">Bibliothèque complète</h3>
          <p className="text-gray-600">
            Accédez à une vaste collection d'épreuves couvrant toutes les matières et niveaux
          </p>
        </div>

        <div className="card text-center">
          <FaStar className="text-5xl text-primary-600 mx-auto mb-4" />
          <h3 className="text-xl font-bold mb-2">Recommandations personnalisées</h3>
          <p className="text-gray-600">
            Notre IA vous suggère les épreuves les plus pertinentes selon votre profil
          </p>
        </div>

        <div className="card text-center">
          <FaUsers className="text-5xl text-primary-600 mx-auto mb-4" />
          <h3 className="text-xl font-bold mb-2">Communauté active</h3>
          <p className="text-gray-600">
            Partagez vos connaissances et collaborez avec d'autres étudiants et enseignants
          </p>
        </div>
      </section>

      {/* Recommendations for authenticated users */}
      {isAuthenticated && recommendations && recommendations.length > 0 && (
        <section>
          <h2 className="text-3xl font-bold mb-6">Recommandé pour vous</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {recommendations.filter(epreuve => epreuve && epreuve.id).map((epreuve) => (
              <Link
                key={epreuve.id}
                to={`/epreuves/${epreuve.id}`}
                className="card hover:shadow-lg transition-shadow"
              >
                <h3 className="font-bold text-lg mb-2">{epreuve.titre}</h3>
                <p className="text-gray-600 text-sm mb-2">{epreuve.matiere}</p>
                <div className="flex items-center justify-between text-sm text-gray-500">
                  <span>{epreuve.niveau}</span>
                  <span>{epreuve.annee_academique}</span>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Recent Epreuves */}
      <section>
        <h2 className="text-3xl font-bold mb-6">Épreuves récentes</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {recentEpreuves?.results.filter(epreuve => epreuve && epreuve.id).slice(0, 8).map((epreuve) => (
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
            </Link>
          ))}
        </div>
        <div className="text-center mt-8">
          <Link to="/epreuves" className="btn-primary inline-flex items-center space-x-2">
            <FaSearch />
            <span>Voir toutes les épreuves</span>
          </Link>
        </div>
      </section>
    </div>
  )
}

export default HomePage
