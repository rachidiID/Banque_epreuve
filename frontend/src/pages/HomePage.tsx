import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '@/contexts/AuthContext'
import { epreuvesAPI } from '@/api/epreuves'
import { recommendationsAPI } from '@/api/recommendations'
import { FaBook, FaSearch, FaStar, FaUsers, FaArrowRight, FaDownload, FaEye } from 'react-icons/fa'

const HomePage = () => {
  const { isAuthenticated, user } = useAuth()
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')

  const { data: recentEpreuves } = useQuery({
    queryKey: ['epreuves', 'recent'],
    queryFn: () => epreuvesAPI.getEpreuves({ ordering: '-created_at', page: 1 }),
  })

  const { data: recommendations } = useQuery({
    queryKey: ['recommendations', user?.id],
    queryFn: () => recommendationsAPI.getRecommendations(6),
    enabled: isAuthenticated,
  })

  return (
    <div className="space-y-16">
      {/* Hero Section */}
      <section className="relative text-center py-20 bg-gradient-to-br from-primary-600 via-primary-700 to-primary-900 text-white rounded-3xl overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-10 left-10 w-32 h-32 bg-white rounded-full blur-3xl"></div>
          <div className="absolute bottom-10 right-20 w-48 h-48 bg-accent-400 rounded-full blur-3xl"></div>
        </div>
        <div className="relative z-10">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-extrabold mb-4 leading-tight">
            Banque d'Épreuves<br />
            <span className="text-accent-300">IMSP</span>
          </h1>
          <p className="text-lg md:text-xl mb-8 text-primary-100 max-w-2xl mx-auto">
            Partagez, découvrez et préparez-vous avec des épreuves académiques.
            Recommandations intelligentes personnalisées.
          </p>

          {/* Barre de recherche responsive */}
          <form
            onSubmit={(e) => {
              e.preventDefault()
              if (searchQuery.trim()) {
                navigate(`/epreuves?search=${encodeURIComponent(searchQuery.trim())}`)
              } else {
                navigate('/epreuves')
              }
            }}
            className="max-w-xl mx-auto mb-6 px-4 sm:px-0"
          >
            <div className="relative flex items-center">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Rechercher une épreuve, matière, professeur..."
                className="w-full pl-5 pr-14 py-3.5 sm:py-4 rounded-2xl text-gray-800 bg-white/95 backdrop-blur-sm shadow-xl border-0 focus:ring-2 focus:ring-accent-400 focus:outline-none text-sm sm:text-base placeholder-gray-400"
              />
              <button
                type="submit"
                className="absolute right-2 bg-gradient-to-r from-accent-500 to-accent-600 text-white p-2.5 sm:p-3 rounded-xl hover:from-accent-600 hover:to-accent-700 transition-all shadow-md"
              >
                <FaSearch className="text-sm sm:text-base" />
              </button>
            </div>
          </form>

          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center px-4 sm:px-0">
            <Link to="/epreuves" className="bg-white text-primary-700 px-6 sm:px-8 py-3 rounded-xl font-bold hover:bg-gray-100 inline-flex items-center justify-center space-x-2 transition-all shadow-lg hover:shadow-xl text-sm sm:text-base">
              <FaSearch />
              <span>Explorer les épreuves</span>
            </Link>
            {!isAuthenticated && (
              <Link to="/register" className="bg-accent-500 text-white px-6 sm:px-8 py-3 rounded-xl font-bold hover:bg-accent-600 inline-flex items-center justify-center space-x-2 transition-all shadow-lg hover:shadow-xl text-sm sm:text-base">
                <FaUsers />
                <span>Créer un compte</span>
              </Link>
            )}
          </div>
        </div>
      </section>

      {/* Stats Bar */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { icon: FaBook, label: 'Épreuves', value: recentEpreuves?.count || '—', color: 'primary' },
          { icon: FaStar, label: 'IA Recommandation', value: 'Actif', color: 'accent' },
          { icon: FaUsers, label: 'Communauté', value: 'IMSP', color: 'success' },
          { icon: FaDownload, label: 'Téléchargements', value: '∞', color: 'primary' },
        ].map((stat, i) => (
          <div key={i} className="card text-center py-4">
            <stat.icon className={`text-2xl text-${stat.color}-500 mx-auto mb-2`} />
            <div className="text-2xl font-bold text-gray-800">{stat.value}</div>
            <div className="text-sm text-gray-500">{stat.label}</div>
          </div>
        ))}
      </section>

      {/* Features */}
      <section className="grid md:grid-cols-3 gap-8">
        <div className="card-hover text-center group">
          <div className="w-16 h-16 bg-primary-100 rounded-2xl flex items-center justify-center mx-auto mb-4 group-hover:bg-primary-200 transition-colors">
            <FaBook className="text-2xl text-primary-600" />
          </div>
          <h3 className="text-xl font-bold mb-2">Bibliothèque complète</h3>
          <p className="text-gray-500">
            Accédez à une vaste collection d'épreuves couvrant toutes les matières et niveaux de l'IMSP
          </p>
        </div>

        <div className="card-hover text-center group">
          <div className="w-16 h-16 bg-accent-100 rounded-2xl flex items-center justify-center mx-auto mb-4 group-hover:bg-accent-200 transition-colors">
            <FaStar className="text-2xl text-accent-600" />
          </div>
          <h3 className="text-xl font-bold mb-2">Recommandations IA</h3>
          <p className="text-gray-500">
            Notre système intelligent vous suggère les épreuves les plus pertinentes selon votre profil
          </p>
        </div>

        <div className="card-hover text-center group">
          <div className="w-16 h-16 bg-success-100 rounded-2xl flex items-center justify-center mx-auto mb-4 group-hover:bg-green-200 transition-colors">
            <FaUsers className="text-2xl text-success-600" />
          </div>
          <h3 className="text-xl font-bold mb-2">Communauté active</h3>
          <p className="text-gray-500">
            Partagez vos connaissances, évaluez et commentez les épreuves avec d'autres étudiants
          </p>
        </div>
      </section>

      {/* Recommendations for authenticated users */}
      {isAuthenticated && recommendations && recommendations.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl md:text-3xl font-bold">
              <span className="gradient-text">Recommandé pour vous</span>
            </h2>
            <Link to="/epreuves" className="text-primary-600 hover:text-primary-700 flex items-center space-x-1 font-medium text-sm">
              <span>Voir tout</span>
              <FaArrowRight className="text-xs" />
            </Link>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {recommendations.filter(epreuve => epreuve && epreuve.id).map((epreuve) => (
              <Link
                key={epreuve.id}
                to={`/epreuves/${epreuve.id}`}
                className="card-hover"
              >
                <div className="flex items-start justify-between mb-3">
                  <span className="badge-primary">{epreuve.niveau}</span>
                  <span className="badge-accent">{epreuve.type_epreuve}</span>
                </div>
                <h3 className="font-bold text-lg mb-2 text-gray-800">{epreuve.titre}</h3>
                <p className="text-gray-500 text-sm mb-3">{epreuve.matiere}</p>
                <div className="flex items-center justify-between text-xs text-gray-400">
                  <span>{epreuve.annee_academique}</span>
                  <div className="flex items-center space-x-3">
                    <span className="flex items-center space-x-1"><FaEye /><span>{epreuve.nb_vues}</span></span>
                    <span className="flex items-center space-x-1"><FaDownload /><span>{epreuve.nb_telechargements}</span></span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Recent Epreuves */}
      <section>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl md:text-3xl font-bold">Épreuves récentes</h2>
          <Link to="/epreuves" className="text-primary-600 hover:text-primary-700 flex items-center space-x-1 font-medium text-sm">
            <span>Voir tout</span>
            <FaArrowRight className="text-xs" />
          </Link>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-5">
          {recentEpreuves?.results.filter(epreuve => epreuve && epreuve.id).slice(0, 8).map((epreuve) => (
            <Link
              key={epreuve.id}
              to={`/epreuves/${epreuve.id}`}
              className="card-hover"
            >
              <div className="flex items-center gap-2 mb-2">
                <span className="badge-primary text-xs">{epreuve.niveau}</span>
                <span className="text-xs text-gray-400">{epreuve.type_epreuve}</span>
              </div>
              <h3 className="font-semibold mb-1 text-gray-800 text-sm leading-tight">{epreuve.titre}</h3>
              <p className="text-xs text-gray-500 mb-2">{epreuve.matiere}</p>
              <div className="flex items-center justify-between text-xs text-gray-400">
                <span>{epreuve.annee_academique}</span>
                <div className="flex items-center space-x-2">
                  <span className="flex items-center space-x-0.5"><FaEye className="text-[10px]" /><span>{epreuve.nb_vues}</span></span>
                  <span className="flex items-center space-x-0.5"><FaDownload className="text-[10px]" /><span>{epreuve.nb_telechargements}</span></span>
                </div>
              </div>
            </Link>
          ))}
        </div>
        <div className="text-center mt-10">
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
