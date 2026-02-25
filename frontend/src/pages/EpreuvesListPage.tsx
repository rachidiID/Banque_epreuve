import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { epreuvesAPI } from '@/api/epreuves'
import { FaSearch, FaFilter } from 'react-icons/fa'

const EpreuvesListPage = () => {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [filters, setFilters] = useState({
    matiere: '',
    niveau: '',
    type_epreuve: '',
    annee_academique: '',
    ordering: '-created_at',
  })

  const { data: epreuvesData, isLoading } = useQuery({
    queryKey: ['epreuves', page, search, filters],
    queryFn: () =>
      epreuvesAPI.getEpreuves({
        page,
        search,
        ...Object.fromEntries(Object.entries(filters).filter(([_, v]) => v !== '')),
      }),
  })

  const handleFilterChange = (key: string, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
    setPage(1)
  }

  return (
    <div className="space-y-6">
      <h1 className="text-4xl font-bold">Bibliothèque d'Épreuves</h1>

      {/* Search and Filters */}
      <div className="card">
        <div className="grid md:grid-cols-2 lg:grid-cols-6 gap-4">
          {/* Search */}
          <div className="lg:col-span-2">
            <div className="relative">
              <FaSearch className="absolute left-3 top-3 text-gray-400" />
              <input
                type="text"
                placeholder="Rechercher..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value)
                  setPage(1)
                }}
                className="input-field pl-10"
              />
            </div>
          </div>

          {/* Matiere Filter */}
          <input
            type="text"
            placeholder="Matière..."
            value={filters.matiere}
            onChange={(e) => handleFilterChange('matiere', e.target.value)}
            className="input-field"
          />

          {/* Niveau Filter */}
          <select
            value={filters.niveau}
            onChange={(e) => handleFilterChange('niveau', e.target.value)}
            className="input-field"
          >
            <option value="">Tous les niveaux</option>
            <option value="L1">Licence 1</option>
            <option value="L2">Licence 2</option>
            <option value="L3">Licence 3</option>
            <option value="M1">Master 1</option>
            <option value="M2">Master 2</option>
          </select>

          {/* Type Filter */}
          <select
            value={filters.type_epreuve}
            onChange={(e) => handleFilterChange('type_epreuve', e.target.value)}
            className="input-field"
          >
            <option value="">Tous les types</option>
            <option value="PARTIEL">Partiel</option>
            <option value="EXAMEN">Examen</option>
            <option value="TD">TD</option>
            <option value="RATTRAPAGE">Rattrapage</option>
            <option value="CC">Contrôle Continu</option>
          </select>

          {/* Sort */}
          <select
            value={filters.ordering}
            onChange={(e) => handleFilterChange('ordering', e.target.value)}
            className="input-field"
          >
            <option value="-created_at">Plus récents</option>
            <option value="created_at">Plus anciens</option>
            <option value="-nb_vues">Plus vus</option>
            <option value="-nb_telechargements">Plus téléchargés</option>
          </select>
        </div>
      </div>

      {/* Results */}
      {isLoading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
        </div>
      ) : (
        <>
          <div className="flex items-center justify-between">
            <p className="text-gray-600">
              {epreuvesData?.count || 0} épreuve(s) trouvée(s)
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {epreuvesData?.results.map((epreuve) => (
              <div key={epreuve.id} className="card hover:shadow-lg transition-shadow">
                <Link to={`/epreuves/${epreuve.id}`}>
                  <h3 className="font-bold text-lg mb-2 hover:text-primary-600">
                    {epreuve.titre}
                  </h3>
                </Link>
                <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                  {epreuve.description}
                </p>
                <div className="flex items-center justify-between text-sm text-gray-500 mb-2">
                  <span className="font-semibold">{epreuve.matiere}</span>
                  <span>{epreuve.type_epreuve}</span>
                </div>
                <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
                  <span>{epreuve.niveau}</span>
                  <span>{epreuve.annee_academique}</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4 text-xs text-gray-600">
                    <span>👁 {epreuve.nb_vues}</span>
                    <span>⬇ {epreuve.nb_telechargements}</span>
                  </div>
                  <Link
                    to={`/epreuves/${epreuve.id}`}
                    className="text-primary-600 hover:text-primary-700 text-sm font-semibold"
                  >
                    Voir détails
                  </Link>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {epreuvesData && epreuvesData.count > 10 && (
            <div className="flex items-center justify-center space-x-4">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={!epreuvesData.previous}
                className="btn-secondary disabled:opacity-50"
              >
                Précédent
              </button>
              <span className="text-gray-600">
                Page {page} sur {Math.ceil(epreuvesData.count / 10)}
              </span>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={!epreuvesData.next}
                className="btn-secondary disabled:opacity-50"
              >
                Suivant
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default EpreuvesListPage
