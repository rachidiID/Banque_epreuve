import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { useAuth } from '@/contexts/AuthContext'
import type { RegisterData } from '@/types'
import { FaUser, FaLock, FaEnvelope, FaBook, FaGraduationCap } from 'react-icons/fa'

const RegisterPage = () => {
  const navigate = useNavigate()
  const { register: registerUser } = useAuth()
  const [isLoading, setIsLoading] = useState(false)

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<RegisterData>()

  const password = watch('password')

  const onSubmit = async (data: RegisterData) => {
    setIsLoading(true)
    try {
      await registerUser(data)
      navigate('/')
    } catch (error) {
      console.error('Register error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-[70vh] flex items-center justify-center py-8">
      <div className="w-full max-w-lg">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-primary-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <FaGraduationCap className="text-2xl text-white" />
          </div>
          <h1 className="text-3xl font-extrabold gradient-text">Créer un compte</h1>
          <p className="text-gray-500 mt-2">Rejoignez la communauté IMSP</p>
        </div>

        <div className="card">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Row: First Name / Last Name */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1.5">Prénom</label>
                <input
                  type="text"
                  {...register('first_name', { required: 'Prénom requis' })}
                  className="input-field"
                  placeholder="Jean"
                />
                {errors.first_name && <p className="text-red-500 text-xs mt-1">{errors.first_name.message}</p>}
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1.5">Nom</label>
                <input
                  type="text"
                  {...register('last_name', { required: 'Nom requis' })}
                  className="input-field"
                  placeholder="Dupont"
                />
                {errors.last_name && <p className="text-red-500 text-xs mt-1">{errors.last_name.message}</p>}
              </div>
            </div>

            {/* Username */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">Nom d'utilisateur</label>
              <div className="relative">
                <FaUser className="absolute left-3.5 top-3.5 text-gray-400 text-sm" />
                <input
                  type="text"
                  {...register('username', {
                    required: "Nom d'utilisateur requis",
                    minLength: { value: 3, message: 'Minimum 3 caractères' },
                  })}
                  className="input-field pl-10"
                  placeholder="jean.dupont"
                />
              </div>
              {errors.username && <p className="text-red-500 text-xs mt-1">{errors.username.message}</p>}
            </div>

            {/* Email */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">Email</label>
              <div className="relative">
                <FaEnvelope className="absolute left-3.5 top-3.5 text-gray-400 text-sm" />
                <input
                  type="email"
                  {...register('email', {
                    required: 'Email requis',
                    pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: 'Email invalide' },
                  })}
                  className="input-field pl-10"
                  placeholder="jean@imsp.bj"
                />
              </div>
              {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>}
            </div>

            {/* Row: Niveau / Filière */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1.5">Niveau</label>
                <select {...register('niveau')} className="input-field">
                  <option value="">Sélectionner</option>
                  <option value="L1">Licence 1</option>
                  <option value="L2">Licence 2</option>
                  <option value="L3">Licence 3</option>
                  <option value="M1">Master 1</option>
                  <option value="M2">Master 2</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1.5">Filière</label>
                <select {...register('filiere')} className="input-field">
                  <option value="">Sélectionner</option>
                  <option value="MATH">Mathématiques</option>
                  <option value="INFO">Informatique</option>
                  <option value="PHYSIQUE">Physique</option>
                  <option value="CHIMIE">Chimie</option>
                </select>
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">Mot de passe</label>
              <div className="relative">
                <FaLock className="absolute left-3.5 top-3.5 text-gray-400 text-sm" />
                <input
                  type="password"
                  {...register('password', {
                    required: 'Mot de passe requis',
                    minLength: { value: 8, message: 'Minimum 8 caractères' },
                  })}
                  className="input-field pl-10"
                  placeholder="••••••••"
                />
              </div>
              {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>}
            </div>

            {/* Confirm Password */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">Confirmer le mot de passe</label>
              <div className="relative">
                <FaLock className="absolute left-3.5 top-3.5 text-gray-400 text-sm" />
                <input
                  type="password"
                  {...register('password_confirm', {
                    required: 'Confirmation requise',
                    validate: (value) => value === password || 'Les mots de passe ne correspondent pas',
                  })}
                  className="input-field pl-10"
                  placeholder="••••••••"
                />
              </div>
              {errors.password_confirm && <p className="text-red-500 text-xs mt-1">{errors.password_confirm.message}</p>}
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full btn-primary py-3 text-base mt-2 disabled:opacity-50"
            >
              {isLoading ? (
                <span className="inline-flex items-center space-x-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  <span>Création du compte...</span>
                </span>
              ) : "S'inscrire"}
            </button>
          </form>

          <div className="mt-6 text-center text-sm">
            <p className="text-gray-500">
              Déjà un compte ?{' '}
              <Link to="/login" className="text-primary-600 hover:text-primary-700 font-semibold">
                Se connecter
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default RegisterPage
