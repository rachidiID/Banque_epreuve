import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { epreuvesAPI } from '@/api/epreuves'
import { commentairesAPI } from '@/api/commentaires'
import { evaluationsAPI } from '@/api/evaluations'
import { useAuth } from '@/contexts/AuthContext'
import toast from 'react-hot-toast'
import { FaDownload, FaStar, FaClock, FaCalendar, FaBook, FaEye } from 'react-icons/fa'
import { format } from 'date-fns'
import { fr } from 'date-fns/locale'
import PDFViewer from '@/components/PDFViewer'

const EpreuveDetailPage = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [commentText, setCommentText] = useState('')
  const [commentNoteUtilite, setCommentNoteUtilite] = useState<number>(0)
  const [commentRecommande, setCommentRecommande] = useState<boolean | null>(null)
  const [commentDifficulte, setCommentDifficulte] = useState<number>(0)
  const [showPDFViewer, setShowPDFViewer] = useState(true)
  const [rating, setRating] = useState({
    note_difficulte: 3,
    note_pertinence: 3,
  })

  // Valider l'ID
  const epreuveId = id ? Number(id) : null
  
  useEffect(() => {
    if (!epreuveId || isNaN(epreuveId)) {
      toast.error('ID d\'épreuve invalide')
      navigate('/epreuves')
    }
  }, [epreuveId, navigate])

  const { data: epreuve, isLoading, error } = useQuery({
    queryKey: ['epreuve', epreuveId],
    queryFn: () => epreuvesAPI.getEpreuve(epreuveId!),
    enabled: !!epreuveId && !isNaN(epreuveId),
  })

  const { data: commentaires } = useQuery({
    queryKey: ['commentaires', epreuveId],
    queryFn: () => commentairesAPI.getCommentaires(epreuveId!),
    enabled: !!epreuveId && !isNaN(epreuveId),
  })

  const { data: similarEpreuves } = useQuery({
    queryKey: ['similar', epreuveId],
    queryFn: () => epreuvesAPI.getSimilarEpreuves(epreuveId!),
    enabled: !!epreuveId && !isNaN(epreuveId),
  })

  const addCommentMutation = useMutation({
    mutationFn: (data: { contenu: string; note_utilite?: number; recommande?: boolean; niveau_difficulte_ressenti?: number }) =>
      commentairesAPI.createCommentaire(epreuveId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['commentaires', epreuveId] })
      setCommentText('')
      setCommentNoteUtilite(0)
      setCommentRecommande(null)
      setCommentDifficulte(0)
      toast.success('Commentaire ajouté')
    },
  })

  const addEvaluationMutation = useMutation({
    mutationFn: (data: any) => evaluationsAPI.createOrUpdateEvaluation(epreuveId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['epreuve', epreuveId] })
      toast.success('Évaluation enregistrée')
    },
  })

  const handleDownload = async () => {
    if (!epreuveId) return
    
    try {
      await epreuvesAPI.downloadEpreuve(epreuveId)
      toast.success('Téléchargement démarré')
    } catch (error) {
      console.error('Erreur téléchargement:', error)
      toast.error('Erreur lors du téléchargement')
    }
  }

  // Gestion des erreurs de chargement
  if (error) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-red-600 mb-4">Erreur</h2>
        <p className="text-gray-600 mb-4">Impossible de charger l'épreuve</p>
        <Link to="/epreuves" className="btn-primary">
          Retour aux épreuves
        </Link>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!epreuve) {
    return <div className="text-center py-12">Épreuve non trouvée</div>
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="card">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h1 className="text-3xl font-bold mb-2">{epreuve.titre}</h1>
            <p className="text-gray-600 mb-4">{epreuve.description}</p>
          </div>
          <div className="flex gap-2">
            <button 
              onClick={() => setShowPDFViewer(!showPDFViewer)} 
              className="btn-secondary flex items-center space-x-2"
            >
              <FaEye />
              <span>{showPDFViewer ? 'Masquer' : 'Voir'} PDF</span>
            </button>
            <button onClick={handleDownload} className="btn-primary flex items-center space-x-2">
              <FaDownload />
              <span>Télécharger</span>
            </button>
          </div>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
          <div className="flex items-center space-x-2">
            <FaBook className="text-primary-600" />
            <span className="font-semibold">{epreuve.matiere}</span>
          </div>
          <div className="flex items-center space-x-2">
            <FaCalendar className="text-primary-600" />
            <span>{epreuve.niveau} - {epreuve.annee_academique}</span>
          </div>
          <div className="flex items-center space-x-2">
            <FaClock className="text-primary-600" />
            <span>{epreuve.type_epreuve}</span>
          </div>
          <div className="flex items-center space-x-2">
            <span>👁 {epreuve.nb_vues} vues - ⬇ {epreuve.nb_telechargements} téléchargements</span>
          </div>
        </div>
      </div>

      {/* PDF Viewer */}
      {showPDFViewer && epreuve.preview_url && (
        <PDFViewer 
          url={epreuve.preview_url} 
          onDownload={handleDownload}
          filename={`${epreuve.titre}.pdf`}
        />
      )}

      {/* Evaluation Form */}
      <div className="card">
        <h2 className="text-2xl font-bold mb-4">Évaluer cette épreuve</h2>
        <div className="grid md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              Difficulté (1=facile, 5=difficile)
            </label>
            <input
              type="range"
              min="1"
              max="5"
              step="1"
              value={rating.note_difficulte}
              onChange={(e) =>
                setRating((prev) => ({ ...prev, note_difficulte: Number(e.target.value) }))
              }
              className="w-full"
            />
            <div className="text-right text-sm text-gray-600">{rating.note_difficulte} / 5</div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">
              Pertinence (1=peu pertinent, 5=très pertinent)
            </label>
            <input
              type="range"
              min="1"
              max="5"
              step="1"
              value={rating.note_pertinence}
              onChange={(e) =>
                setRating((prev) => ({ ...prev, note_pertinence: Number(e.target.value) }))
              }
              className="w-full"
            />
            <div className="text-right text-sm text-gray-600">{rating.note_pertinence} / 5</div>
          </div>
        </div>
        <button onClick={() => addEvaluationMutation.mutate(rating)} className="btn-primary">
          Enregistrer l'évaluation
        </button>
      </div>

      {/* Comments */}
      <div className="card">
        <h2 className="text-2xl font-bold mb-4">
          Commentaires ({commentaires?.length || 0})
        </h2>

        <div className="mb-6 space-y-4">
          <textarea
            value={commentText}
            onChange={(e) => setCommentText(e.target.value)}
            placeholder="Partagez votre avis sur cette épreuve..."
            className="input-field min-h-[100px]"
          />

          {/* Champs enrichis pour le modèle de recommandation */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-xl">
            <div>
              <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
                Utilité de l'épreuve
              </label>
              <div className="flex gap-1">
                {[1, 2, 3, 4, 5].map((n) => (
                  <button
                    key={n}
                    type="button"
                    onClick={() => setCommentNoteUtilite(n === commentNoteUtilite ? 0 : n)}
                    className={`w-9 h-9 rounded-lg text-sm font-bold transition-all ${
                      n <= commentNoteUtilite
                        ? 'bg-amber-500 text-white shadow-md'
                        : 'bg-gray-200 dark:bg-gray-600 text-gray-500 dark:text-gray-400 hover:bg-gray-300'
                    }`}
                  >
                    {n}
                  </button>
                ))}
              </div>
              <span className="text-xs text-gray-400 mt-1 block">1=pas utile, 5=très utile</span>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
                Difficulté ressentie
              </label>
              <div className="flex gap-1">
                {[1, 2, 3, 4, 5].map((n) => (
                  <button
                    key={n}
                    type="button"
                    onClick={() => setCommentDifficulte(n === commentDifficulte ? 0 : n)}
                    className={`w-9 h-9 rounded-lg text-sm font-bold transition-all ${
                      n <= commentDifficulte
                        ? 'bg-purple-500 text-white shadow-md'
                        : 'bg-gray-200 dark:bg-gray-600 text-gray-500 dark:text-gray-400 hover:bg-gray-300'
                    }`}
                  >
                    {n}
                  </button>
                ))}
              </div>
              <span className="text-xs text-gray-400 mt-1 block">1=facile, 5=très difficile</span>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
                Recommander ?
              </label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setCommentRecommande(commentRecommande === true ? null : true)}
                  className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                    commentRecommande === true
                      ? 'bg-green-500 text-white shadow-md'
                      : 'bg-gray-200 dark:bg-gray-600 text-gray-500 dark:text-gray-400 hover:bg-gray-300'
                  }`}
                >
                  👍 Oui
                </button>
                <button
                  type="button"
                  onClick={() => setCommentRecommande(commentRecommande === false ? null : false)}
                  className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                    commentRecommande === false
                      ? 'bg-red-500 text-white shadow-md'
                      : 'bg-gray-200 dark:bg-gray-600 text-gray-500 dark:text-gray-400 hover:bg-gray-300'
                  }`}
                >
                  👎 Non
                </button>
              </div>
            </div>
          </div>

          <button
            onClick={() => {
              const data: any = { contenu: commentText }
              if (commentNoteUtilite > 0) data.note_utilite = commentNoteUtilite
              if (commentRecommande !== null) data.recommande = commentRecommande
              if (commentDifficulte > 0) data.niveau_difficulte_ressenti = commentDifficulte
              addCommentMutation.mutate(data)
            }}
            disabled={!commentText.trim()}
            className="btn-primary disabled:opacity-50"
          >
            Publier le commentaire
          </button>
        </div>

        <div className="space-y-4">
          {commentaires && Array.isArray(commentaires) && commentaires.map((comment) => (
            <div key={comment.id} className="border-l-2 border-primary-200 pl-4">
              <div className="flex items-center space-x-2 mb-1">
                <span className="font-semibold">{comment.user_username || comment.user?.username}</span>
                <span className="text-sm text-gray-500">
                  {format(new Date(comment.created_at), 'PPp', { locale: fr })}
                </span>
              </div>
              <p className="text-gray-700 dark:text-gray-300">{comment.contenu}</p>
              {/* Afficher les notes si présentes */}
              <div className="flex flex-wrap gap-2 mt-1">
                {comment.note_utilite && (
                  <span className="text-xs px-2 py-0.5 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 rounded-full">
                    Utilité: {comment.note_utilite}/5
                  </span>
                )}
                {comment.niveau_difficulte_ressenti && (
                  <span className="text-xs px-2 py-0.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-full">
                    Difficulté: {comment.niveau_difficulte_ressenti}/5
                  </span>
                )}
                {comment.recommande !== null && comment.recommande !== undefined && (
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    comment.recommande
                      ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                      : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
                  }`}>
                    {comment.recommande ? '👍 Recommandé' : '👎 Non recommandé'}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Similar Epreuves */}
      {similarEpreuves && similarEpreuves.length > 0 && (
        <div>
          <h2 className="text-2xl font-bold mb-4">Épreuves similaires</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {similarEpreuves.slice(0, 4).map((similar) => (
              <Link
                key={similar.id}
                to={`/epreuves/${similar.id}`}
                className="card hover:shadow-lg transition-shadow"
              >
                <h3 className="font-bold mb-2">{similar.titre}</h3>
                <p className="text-sm text-gray-600">{similar.matiere}</p>
                <div className="flex items-center justify-between text-xs text-gray-500 mt-2">
                  <span>{similar.niveau}</span>
                  <span>{similar.annee_academique}</span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default EpreuveDetailPage
