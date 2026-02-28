import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '@/contexts/AuthContext'
import { useNavigate } from 'react-router-dom'
import apiClient from '@/api/client'
import toast from 'react-hot-toast'
import type { Epreuve } from '@/types'
import {
  FaDatabase, FaUsers, FaBook, FaChartBar, FaSync,
  FaCommentAlt, FaStar, FaCog, FaRocket,
  FaDownload, FaCloudDownloadAlt, FaFileCsv,
  FaCheck, FaTimesCircle, FaExclamationTriangle,
} from 'react-icons/fa'

interface DashboardStats {
  total_users: number
  total_epreuves: number
  total_interactions: number
  total_evaluations: number
  total_commentaires: number
  pending_count: number
  epreuves_par_matiere: Array<{ matiere: string; count: number }>
  epreuves_par_niveau: Array<{ niveau: string; count: number }>
  top_epreuves: Array<{ id: number; titre: string; matiere: string; niveau: string; nb_telechargements: number; nb_vues: number }>
  users_par_filiere?: Array<{ filiere: string; count: number }>
  users_par_niveau?: Array<{ niveau: string; count: number }>
}

interface GenerateResult {
  message: string
  summary: {
    users_created: number
    epreuves_created: number
    interactions_created: number
    evaluations_created: number
    commentaires_created: number
  }
  totals: {
    total_users: number
    total_epreuves: number
    total_interactions: number
    total_evaluations: number
    total_commentaires: number
  }
}

const AdminPage = () => {
  const { user } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [isGenerating, setIsGenerating] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
  const [generateConfig, setGenerateConfig] = useState({
    users: 30,
    epreuves: 25,
    interactions: 1000,
  })

  // Redirect if not admin
  if (user && !(user as any).is_staff) {
    navigate('/')
    return null
  }

  const { data: stats, refetch: refetchStats, isLoading: statsLoading } = useQuery<DashboardStats>({
    queryKey: ['admin-stats'],
    queryFn: async () => {
      const response = await apiClient.get('/admin/stats/')
      return response.data
    },
  })

  // Épreuves en attente de modération
  const { data: pendingData, refetch: refetchPending, isLoading: pendingLoading } = useQuery<{ count: number; results: Epreuve[] }>({
    queryKey: ['admin-pending'],
    queryFn: async () => {
      const response = await apiClient.get('/admin/pending/')
      return response.data
    },
  })

  const handleApprove = async (id: number) => {
    try {
      await apiClient.post(`/admin/epreuves/${id}/approve/`)
      toast.success('Épreuve approuvée !')
      refetchPending()
      refetchStats()
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Erreur')
    }
  }

  const handleReject = async (id: number) => {
    if (!confirm('Êtes-vous sûr de vouloir rejeter et supprimer cette épreuve ?')) return
    try {
      await apiClient.post(`/admin/epreuves/${id}/reject/`)
      toast.success('Épreuve rejetée et supprimée')
      refetchPending()
      refetchStats()
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Erreur')
    }
  }

  const handleGenerate = async () => {
    setIsGenerating(true)
    try {
      const response = await apiClient.post<GenerateResult>('/admin/generate-data/', generateConfig)
      const result = response.data
      toast.success(
        `Données générées ! ${result.summary.epreuves_created} épreuves, ${result.summary.users_created} utilisateurs, ${result.summary.interactions_created} interactions`,
        { duration: 5000 }
      )
      refetchStats()
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Erreur lors de la génération')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleExport = async (format: 'json' | 'csv') => {
    setIsExporting(true)
    try {
      const response = await apiClient.get(`/admin/export-data/?format=${format}`, {
        responseType: 'blob',
      })
      const blob = new Blob([response.data])
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = format === 'json' ? 'banque_epreuves_export.json' : 'banque_epreuves_export.zip'
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      toast.success(`Export ${format.toUpperCase()} téléchargé !`)
    } catch (error: any) {
      // Quand responseType est 'blob', les erreurs sont aussi des blobs
      let errorMsg = "Erreur lors de l'export"
      if (error.response?.data instanceof Blob) {
        try {
          const text = await error.response.data.text()
          const parsed = JSON.parse(text)
          errorMsg = parsed.error || errorMsg
        } catch { /* ignore parse error */ }
      } else {
        errorMsg = error.response?.data?.error || errorMsg
      }
      toast.error(errorMsg)
    } finally {
      setIsExporting(false)
    }
  }

  const niveauColors: Record<string, string> = {
    P1: 'bg-teal-100 text-teal-700',
    P2: 'bg-cyan-100 text-cyan-700',
    L3: 'bg-purple-100 text-purple-700',
    M1: 'bg-pink-100 text-pink-700',
    M2: 'bg-red-100 text-red-700',
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold gradient-text">Panneau d'administration</h1>
          <p className="text-gray-500 mt-1">Gérez les données et consultez les statistiques</p>
        </div>
        <button
          onClick={() => refetchStats()}
          className="btn-secondary flex items-center space-x-2"
          disabled={statsLoading}
        >
          <FaSync className={statsLoading ? 'animate-spin' : ''} />
          <span>Actualiser</span>
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
        {[
          { icon: FaUsers, label: 'Utilisateurs', value: stats?.total_users ?? '—', color: 'primary' },
          { icon: FaBook, label: 'Épreuves', value: stats?.total_epreuves ?? '—', color: 'accent' },
          { icon: FaExclamationTriangle, label: 'En attente', value: stats?.pending_count ?? '—', color: 'yellow' },
          { icon: FaChartBar, label: 'Interactions', value: stats?.total_interactions ?? '—', color: 'indigo' },
          { icon: FaStar, label: 'Évaluations', value: stats?.total_evaluations ?? '—', color: 'green' },
          { icon: FaCommentAlt, label: 'Commentaires', value: stats?.total_commentaires ?? '—', color: 'purple' },
        ].map((stat, i) => (
          <div key={i} className="card text-center">
            <stat.icon className={`text-xl text-${stat.color}-500 mx-auto mb-2`} />
            <div className="text-2xl font-bold text-gray-800">{typeof stat.value === 'number' ? stat.value.toLocaleString() : stat.value}</div>
            <div className="text-xs text-gray-500 mt-1">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Modération Section */}
      <div className="card border-2 border-yellow-200 bg-yellow-50/50 dark:bg-yellow-900/10 dark:border-yellow-700">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-yellow-500 rounded-xl flex items-center justify-center flex-shrink-0">
              <FaExclamationTriangle className="text-white text-lg" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100">Modération des épreuves</h2>
              <p className="text-gray-500 dark:text-gray-400 text-sm">
                {pendingData?.count ?? 0} épreuve(s) en attente de validation
              </p>
            </div>
          </div>
          <button
            onClick={() => refetchPending()}
            className="btn-secondary text-sm flex items-center space-x-1"
            disabled={pendingLoading}
          >
            <FaSync className={pendingLoading ? 'animate-spin' : ''} />
            <span>Actualiser</span>
          </button>
        </div>

        {pendingData?.results && pendingData.results.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-yellow-200 dark:border-yellow-800">
                  <th className="text-left py-2 px-3 font-semibold text-gray-600 dark:text-gray-400">Titre</th>
                  <th className="text-left py-2 px-3 font-semibold text-gray-600 dark:text-gray-400">Matière</th>
                  <th className="text-left py-2 px-3 font-semibold text-gray-600 dark:text-gray-400">Niveau</th>
                  <th className="text-left py-2 px-3 font-semibold text-gray-600 dark:text-gray-400">Uploadé par</th>
                  <th className="text-left py-2 px-3 font-semibold text-gray-600 dark:text-gray-400">Date</th>
                  <th className="text-right py-2 px-3 font-semibold text-gray-600 dark:text-gray-400">Actions</th>
                </tr>
              </thead>
              <tbody>
                {pendingData.results.map((ep) => (
                  <tr key={ep.id} className="border-b border-gray-50 dark:border-gray-700 hover:bg-yellow-50/50 dark:hover:bg-yellow-900/10">
                    <td className="py-3 px-3 font-medium text-gray-800 dark:text-gray-200 max-w-[200px] truncate">{ep.titre}</td>
                    <td className="py-3 px-3 text-gray-600 dark:text-gray-400">{ep.matiere}</td>
                    <td className="py-3 px-3">
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${niveauColors[ep.niveau] || 'bg-gray-100 text-gray-600'}`}>
                        {ep.niveau}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-gray-600 dark:text-gray-400">{ep.uploaded_by_username || '—'}</td>
                    <td className="py-3 px-3 text-gray-500 dark:text-gray-400 text-xs">
                      {new Date(ep.created_at).toLocaleDateString('fr-FR')}
                    </td>
                    <td className="py-3 px-3 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() => handleApprove(ep.id)}
                          className="inline-flex items-center space-x-1 px-3 py-1.5 bg-green-500 text-white text-xs font-medium rounded-lg hover:bg-green-600 transition-colors"
                          title="Approuver"
                        >
                          <FaCheck />
                          <span>Approuver</span>
                        </button>
                        <button
                          onClick={() => handleReject(ep.id)}
                          className="inline-flex items-center space-x-1 px-3 py-1.5 bg-red-500 text-white text-xs font-medium rounded-lg hover:bg-red-600 transition-colors"
                          title="Rejeter"
                        >
                          <FaTimesCircle />
                          <span>Rejeter</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-6 text-gray-400 dark:text-gray-500">
            <FaCheck className="text-3xl mx-auto mb-2 text-green-400" />
            <p>Aucune épreuve en attente de modération</p>
          </div>
        )}
      </div>

      {/* Generate Data Section */}
      <div className="card border-2 border-dashed border-primary-200 bg-primary-50/50 dark:bg-primary-900/20 dark:border-primary-700">
        <div className="flex items-start space-x-4">
          <div className="w-12 h-12 bg-primary-600 rounded-xl flex items-center justify-center flex-shrink-0">
            <FaDatabase className="text-white text-lg" />
          </div>
          <div className="flex-1">
            <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100 mb-1">Générer des données synthétiques</h2>
            <p className="text-gray-500 text-sm mb-4">
              Peuplez la base de données avec des utilisateurs, épreuves, interactions, évaluations et commentaires de test.
              Les données générées sont similaires à celles créées en local.
            </p>

            <div className="grid grid-cols-3 gap-4 mb-4">
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Utilisateurs</label>
                <input
                  type="number"
                  min="1"
                  max="500"
                  value={generateConfig.users}
                  onChange={(e) => setGenerateConfig({ ...generateConfig, users: parseInt(e.target.value) || 1 })}
                  className="input-field text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Épreuves</label>
                <input
                  type="number"
                  min="1"
                  max="300"
                  value={generateConfig.epreuves}
                  onChange={(e) => setGenerateConfig({ ...generateConfig, epreuves: parseInt(e.target.value) || 1 })}
                  className="input-field text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Interactions</label>
                <input
                  type="number"
                  min="10"
                  max="50000"
                  value={generateConfig.interactions}
                  onChange={(e) => setGenerateConfig({ ...generateConfig, interactions: parseInt(e.target.value) || 10 })}
                  className="input-field text-sm"
                />
              </div>
            </div>

            <button
              onClick={handleGenerate}
              disabled={isGenerating}
              className="btn-primary flex items-center space-x-2 disabled:opacity-50"
            >
              {isGenerating ? (
                <>
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  <span>Génération en cours...</span>
                </>
              ) : (
                <>
                  <FaRocket />
                  <span>Générer les données</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Charts / Breakdowns */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Export des données */}
        <div className="card border-2 border-dashed border-green-200 bg-green-50/50">
          <div className="flex items-start space-x-4">
            <div className="w-12 h-12 bg-green-600 rounded-xl flex items-center justify-center flex-shrink-0">
              <FaCloudDownloadAlt className="text-white text-lg" />
            </div>
            <div className="flex-1">
              <h2 className="text-xl font-bold text-gray-800 mb-1">Exporter les données</h2>
              <p className="text-gray-500 text-sm mb-4">
                Téléchargez toutes les données (utilisateurs, épreuves, interactions, évaluations)
                pour entraîner le modèle ML en local.
              </p>
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={() => handleExport('json')}
                  disabled={isExporting}
                  className="btn-success flex items-center space-x-2 disabled:opacity-50"
                >
                  <FaDownload />
                  <span>{isExporting ? 'Export...' : 'Export JSON'}</span>
                </button>
                <button
                  onClick={() => handleExport('csv')}
                  disabled={isExporting}
                  className="btn-accent flex items-center space-x-2 disabled:opacity-50"
                >
                  <FaFileCsv />
                  <span>{isExporting ? 'Export...' : 'Export CSV (ZIP)'}</span>
                </button>
              </div>
              <p className="text-xs text-gray-400 mt-3">
                En local : <code className="bg-gray-100 px-1 rounded">python manage.py import_data banque_epreuves_export.json</code>
              </p>
            </div>
          </div>
        </div>

        {/* Épreuves par matière */}
        <div className="card">
          <h3 className="font-bold text-lg mb-4 flex items-center space-x-2">
            <FaBook className="text-primary-500" />
            <span>Épreuves par matière</span>
          </h3>
          {stats?.epreuves_par_matiere && stats.epreuves_par_matiere.length > 0 ? (
            <div className="space-y-3">
              {stats.epreuves_par_matiere.map((item, i) => {
                const max = stats.epreuves_par_matiere[0].count || 1
                const pct = (item.count / max) * 100
                return (
                  <div key={i}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="font-medium text-gray-700">{item.matiere}</span>
                      <span className="text-gray-500">{item.count}</span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-primary-500 to-primary-600 h-2 rounded-full transition-all"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <p className="text-gray-400 text-sm text-center py-4">Aucune donnée</p>
          )}
        </div>

        {/* Épreuves par niveau */}
        <div className="card">
          <h3 className="font-bold text-lg mb-4 flex items-center space-x-2">
            <FaChartBar className="text-accent-500" />
            <span>Épreuves par niveau</span>
          </h3>
          {stats?.epreuves_par_niveau && stats.epreuves_par_niveau.length > 0 ? (
            <div className="flex items-end justify-around h-48 pt-4">
              {stats.epreuves_par_niveau.map((item, i) => {
                const max = Math.max(...stats.epreuves_par_niveau.map(n => n.count)) || 1
                const height = (item.count / max) * 100
                return (
                  <div key={i} className="flex flex-col items-center">
                    <span className="text-xs font-bold text-gray-600 mb-1">{item.count}</span>
                    <div
                      className="w-12 bg-gradient-to-t from-accent-500 to-accent-400 rounded-t-lg transition-all"
                      style={{ height: `${Math.max(height, 5)}%` }}
                    />
                    <span className={`text-xs font-semibold mt-2 px-2 py-0.5 rounded-full ${niveauColors[item.niveau] || 'bg-gray-100 text-gray-600'}`}>
                      {item.niveau}
                    </span>
                  </div>
                )
              })}
            </div>
          ) : (
            <p className="text-gray-400 text-sm text-center py-4">Aucune donnée</p>
          )}
        </div>
      </div>

      {/* Top Épreuves */}
      {stats?.top_epreuves && stats.top_epreuves.length > 0 && (
        <div className="card">
          <h3 className="font-bold text-lg mb-4 flex items-center space-x-2">
            <FaStar className="text-yellow-500" />
            <span>Top épreuves</span>
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left py-2 px-3 font-semibold text-gray-600">#</th>
                  <th className="text-left py-2 px-3 font-semibold text-gray-600">Titre</th>
                  <th className="text-left py-2 px-3 font-semibold text-gray-600">Matière</th>
                  <th className="text-left py-2 px-3 font-semibold text-gray-600">Niveau</th>
                  <th className="text-right py-2 px-3 font-semibold text-gray-600">Téléch.</th>
                  <th className="text-right py-2 px-3 font-semibold text-gray-600">Vues</th>
                </tr>
              </thead>
              <tbody>
                {stats.top_epreuves.map((ep, i) => (
                  <tr key={ep.id} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-2 px-3 font-bold text-primary-600">{i + 1}</td>
                    <td className="py-2 px-3 font-medium text-gray-800">{ep.titre}</td>
                    <td className="py-2 px-3 text-gray-600">{ep.matiere}</td>
                    <td className="py-2 px-3">
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${niveauColors[ep.niveau] || 'bg-gray-100 text-gray-600'}`}>
                        {ep.niveau}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-right font-medium">{ep.nb_telechargements}</td>
                    <td className="py-2 px-3 text-right text-gray-600">{ep.nb_vues}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Quick Links */}
      <div className="card bg-gray-50">
        <h3 className="font-bold text-lg mb-3 flex items-center space-x-2">
          <FaCog className="text-gray-500" />
          <span>Liens rapides</span>
        </h3>
        <div className="flex flex-wrap gap-3">
          <a
            href="/admin/"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-secondary text-sm"
          >
            Django Admin
          </a>
          <a
            href="/api/docs/"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-secondary text-sm"
          >
            API Documentation (Swagger)
          </a>
        </div>
      </div>
    </div>
  )
}

export default AdminPage
