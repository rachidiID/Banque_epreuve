import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { FaCloudUploadAlt, FaFilePdf, FaTimes, FaCheckCircle } from 'react-icons/fa'
import { epreuvesAPI } from '@/api/epreuves'

interface UploadFormData {
  titre: string
  matiere: string
  niveau: string
  type_epreuve: string
  annee_academique: string
  professeur?: string
  description?: string
}

const UploadEpreuvePage = () => {
  const navigate = useNavigate()
  const { register, handleSubmit, formState: { errors } } = useForm<UploadFormData>()
  const [pdfFile, setPdfFile] = useState<File | null>(null)
  const [dragActive, setDragActive] = useState(false)

  const uploadMutation = useMutation({
    mutationFn: (formData: FormData) => epreuvesAPI.uploadEpreuve(formData),
    onSuccess: (response: any) => {
      toast.success('Épreuve uploadée avec succès !')
      // Le backend retourne { message, epreuve: { id, ... } }
      const epreuveId = response.epreuve?.id || response.id
      if (epreuveId) {
        navigate(`/epreuves/${epreuveId}`)
      } else {
        console.error('ID de l\'épreuve non trouvé dans la réponse:', response)
        toast.error('Épreuve uploadée mais impossible de rediriger')
        navigate('/epreuves')
      }
    },
    onError: (error: any) => {
      console.error('Erreur upload:', error)
      const details = error.response?.data?.details
      const errorMessage = error.response?.data?.error || error.response?.data?.detail || 'Erreur lors de l\'upload'
      
      if (details) {
        // Afficher les erreurs de validation spécifiques
        Object.entries(details).forEach(([field, messages]: [string, any]) => {
          const msg = Array.isArray(messages) ? messages.join(', ') : messages
          toast.error(`${field}: ${msg}`)
        })
      } else {
        toast.error(errorMessage)
      }
    },
  })

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0])
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0])
    }
  }

  const handleFileSelect = (file: File) => {
    if (file.type !== 'application/pdf') {
      toast.error('Seuls les fichiers PDF sont acceptés')
      return
    }
    if (file.size > 10 * 1024 * 1024) {
      toast.error('Le fichier ne doit pas dépasser 10 MB')
      return
    }
    setPdfFile(file)
    toast.success('Fichier sélectionné')
  }

  const onSubmit = async (data: UploadFormData) => {
    if (!pdfFile) {
      toast.error('Veuillez sélectionner un fichier PDF')
      return
    }

    const formData = new FormData()
    formData.append('fichier_pdf', pdfFile)
    formData.append('titre', data.titre)
    formData.append('matiere', data.matiere)
    formData.append('niveau', data.niveau)
    formData.append('type_epreuve', data.type_epreuve)
    formData.append('annee_academique', data.annee_academique)
    if (data.professeur) formData.append('professeur', data.professeur)
    if (data.description) formData.append('description', data.description)

    uploadMutation.mutate(formData)
  }

  return (
    <div className="max-w-4xl mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Uploader une épreuve</h1>
        <p className="text-gray-600">Partagez vos épreuves avec la communauté</p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Zone de drop */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">1. Sélectionner le fichier PDF</h2>
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-all ${
              dragActive 
                ? 'border-primary-500 bg-primary-50 scale-[1.02]' 
                : 'border-gray-300 hover:border-gray-400'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            {!pdfFile ? (
              <>
                <FaCloudUploadAlt className="text-6xl text-gray-400 mx-auto mb-4" />
                <p className="text-lg font-medium mb-2">Glissez votre fichier PDF ici</p>
                <p className="text-sm text-gray-500 mb-4">ou</p>
                <label className="btn-primary cursor-pointer inline-block">
                  Choisir un fichier
                  <input
                    type="file"
                    accept="application/pdf"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                </label>
                <p className="text-xs text-gray-500 mt-4">
                  <span className="font-medium">Formats acceptés :</span> PDF uniquement
                  <br />
                  <span className="font-medium">Taille max :</span> 10 MB
                </p>
              </>
            ) : (
              <div className="flex items-center justify-center gap-4">
                <FaFilePdf className="text-5xl text-red-500" />
                <div className="text-left flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <FaCheckCircle className="text-green-500" />
                    <p className="font-medium">{pdfFile.name}</p>
                  </div>
                  <p className="text-sm text-gray-500">
                    {(pdfFile.size / (1024 * 1024)).toFixed(2)} MB
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setPdfFile(null)}
                  className="text-red-500 hover:text-red-700 transition-colors"
                >
                  <FaTimes className="text-xl" />
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Formulaire */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">2. Informations sur l'épreuve</h2>
          <div className="space-y-4">
            {/* Titre */}
            <div>
              <label className="block text-sm font-medium mb-1">
                Titre de l'épreuve <span className="text-red-500">*</span>
              </label>
              <input
                {...register('titre', { required: 'Le titre est requis' })}
                className="input-field"
                placeholder="Ex: Partiel Analyse Mathématique L3"
              />
              {errors.titre && (
                <p className="text-red-500 text-sm mt-1">{errors.titre.message}</p>
              )}
            </div>

            {/* Matière et Niveau */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">
                  Matière <span className="text-red-500">*</span>
                </label>
                <input
                  {...register('matiere', { required: 'La matière est requise' })}
                  className="input-field"
                  placeholder="Ex: Mathématiques"
                  list="matieres-suggestions"
                />
                <datalist id="matieres-suggestions">
                  <option value="Mathématiques" />
                  <option value="Informatique" />
                  <option value="Physique" />
                  <option value="Chimie" />
                  <option value="Biologie" />
                </datalist>
                {errors.matiere && (
                  <p className="text-red-500 text-sm mt-1">{errors.matiere.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">
                  Niveau <span className="text-red-500">*</span>
                </label>
                <select
                  {...register('niveau', { required: 'Le niveau est requis' })}
                  className="input-field"
                >
                  <option value="">Sélectionner...</option>
                  <option value="L1">Licence 1</option>
                  <option value="L2">Licence 2</option>
                  <option value="L3">Licence 3</option>
                  <option value="M1">Master 1</option>
                  <option value="M2">Master 2</option>
                </select>
                {errors.niveau && (
                  <p className="text-red-500 text-sm mt-1">{errors.niveau.message}</p>
                )}
              </div>
            </div>

            {/* Type et Année */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">
                  Type d'épreuve <span className="text-red-500">*</span>
                </label>
                <select
                  {...register('type_epreuve', { required: 'Le type est requis' })}
                  className="input-field"
                >
                  <option value="">Sélectionner...</option>
                  <option value="PARTIEL">Partiel</option>
                  <option value="EXAMEN">Examen</option>
                  <option value="TD">TD</option>
                  <option value="CC">Contrôle Continu</option>
                  <option value="RATTRAPAGE">Rattrapage</option>
                </select>
                {errors.type_epreuve && (
                  <p className="text-red-500 text-sm mt-1">{errors.type_epreuve.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">
                  Année académique <span className="text-red-500">*</span>
                </label>
                <input
                  {...register('annee_academique', { required: 'L\'année est requise' })}
                  className="input-field"
                  placeholder="Ex: 2024-2025"
                />
                {errors.annee_academique && (
                  <p className="text-red-500 text-sm mt-1">{errors.annee_academique.message}</p>
                )}
              </div>
            </div>

            {/* Professeur */}
            <div>
              <label className="block text-sm font-medium mb-1">
                Professeur <span className="text-gray-400">(optionnel)</span>
              </label>
              <input
                {...register('professeur')}
                className="input-field"
                placeholder="Ex: Dr. ZINSOU"
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium mb-1">
                Description <span className="text-gray-400">(optionnel)</span>
              </label>
              <textarea
                {...register('description')}
                className="input-field"
                rows={4}
                placeholder="Décrivez brièvement le contenu de l'épreuve, les chapitres couverts, etc."
              />
            </div>
          </div>
        </div>

        {/* Note d'information */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-medium text-blue-900 mb-2">📌 Note importante</h3>
          <p className="text-sm text-blue-800">
            Votre épreuve sera soumise à modération avant d'être publiée. 
            Assurez-vous que le contenu est approprié et que vous avez le droit de le partager.
          </p>
        </div>

        {/* Boutons */}
        <div className="flex justify-end gap-4">
          <button
            type="button"
            onClick={() => navigate('/epreuves')}
            className="btn-secondary"
            disabled={uploadMutation.isPending}
          >
            Annuler
          </button>
          <button
            type="submit"
            className="btn-primary flex items-center gap-2"
            disabled={uploadMutation.isPending || !pdfFile}
          >
            {uploadMutation.isPending ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                <span>Upload en cours...</span>
              </>
            ) : (
              <>
                <FaCloudUploadAlt />
                <span>Publier l'épreuve</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}

export default UploadEpreuvePage
