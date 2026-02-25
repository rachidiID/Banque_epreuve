import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { useAuth } from '@/contexts/AuthContext'
import type { LoginCredentials } from '@/types'
import { FaUser, FaLock, FaBook } from 'react-icons/fa'

const LoginPage = () => {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [isLoading, setIsLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginCredentials>()

  const onSubmit = async (data: LoginCredentials) => {
    setIsLoading(true)
    try {
      await login(data)
      navigate('/')
    } catch (error) {
      console.error('Login error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-[70vh] flex items-center justify-center">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-primary-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <FaBook className="text-2xl text-white" />
          </div>
          <h1 className="text-3xl font-extrabold gradient-text">Connexion</h1>
          <p className="text-gray-500 mt-2">Accédez à votre banque d'épreuves</p>
        </div>

        <div className="card">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">Nom d'utilisateur</label>
              <div className="relative">
                <FaUser className="absolute left-3.5 top-3.5 text-gray-400 text-sm" />
                <input
                  type="text"
                  {...register('username', {
                    required: "Nom d'utilisateur requis",
                  })}
                  className="input-field pl-10"
                  placeholder="etudiant1"
                />
              </div>
              {errors.username && (
                <p className="text-red-500 text-xs mt-1">{errors.username.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">Mot de passe</label>
              <div className="relative">
                <FaLock className="absolute left-3.5 top-3.5 text-gray-400 text-sm" />
                <input
                  type="password"
                  {...register('password', {
                    required: 'Mot de passe requis',
                    minLength: {
                      value: 6,
                      message: 'Minimum 6 caractères',
                    },
                  })}
                  className="input-field pl-10"
                  placeholder="••••••••"
                />
              </div>
              {errors.password && (
                <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full btn-primary py-3 text-base disabled:opacity-50"
            >
              {isLoading ? (
                <span className="inline-flex items-center space-x-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  <span>Connexion...</span>
                </span>
              ) : 'Se connecter'}
            </button>
          </form>

          <div className="mt-6 text-center text-sm">
            <p className="text-gray-500">
              Pas encore de compte ?{' '}
              <Link to="/register" className="text-primary-600 hover:text-primary-700 font-semibold">
                S'inscrire
              </Link>
            </p>
          </div>
        </div>

      </div>
    </div>
  )
}

export default LoginPage
