import { Link } from 'react-router-dom'
import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { FaBars, FaTimes, FaBook, FaUser, FaSignInAlt, FaSignOutAlt, FaCloudUploadAlt, FaUserPlus, FaCog } from 'react-icons/fa'

const Header = () => {
  const { user, isAuthenticated, logout } = useAuth()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <header className="bg-white/80 backdrop-blur-md shadow-sm sticky top-0 z-50 border-b border-gray-100">
      <nav className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center space-x-2 text-2xl font-bold">
            <span className="bg-primary-600 text-white p-2 rounded-xl">
              <FaBook className="text-lg" />
            </span>
            <span className="gradient-text hidden sm:inline">Banque d'Épreuves</span>
            <span className="gradient-text sm:hidden">IMSP</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-4">
            <Link to="/epreuves" className="text-gray-600 hover:text-primary-600 font-medium transition-colors px-3 py-2 rounded-lg hover:bg-primary-50">
              Épreuves
            </Link>
            {isAuthenticated && (
              <Link 
                to="/upload" 
                className="flex items-center space-x-1.5 btn-accent text-sm"
              >
                <FaCloudUploadAlt />
                <span>Upload</span>
              </Link>
            )}
            {isAuthenticated && user?.is_staff && (
              <Link
                to="/admin-panel"
                className="flex items-center space-x-1.5 text-gray-600 hover:text-primary-600 font-medium transition-colors px-3 py-2 rounded-lg hover:bg-primary-50"
              >
                <FaCog className="text-sm" />
                <span>Admin</span>
              </Link>
            )}
            {isAuthenticated ? (
              <>
                <Link to="/profile" className="flex items-center space-x-1.5 text-gray-600 hover:text-primary-600 font-medium transition-colors px-3 py-2 rounded-lg hover:bg-primary-50">
                  <FaUser className="text-sm" />
                  <span>{user?.username}</span>
                </Link>
                <button onClick={logout} className="flex items-center space-x-1.5 text-gray-500 hover:text-red-500 font-medium transition-colors px-3 py-2 rounded-lg hover:bg-red-50">
                  <FaSignOutAlt className="text-sm" />
                  <span>Déconnexion</span>
                </button>
              </>
            ) : (
              <div className="flex items-center space-x-2">
                <Link to="/login" className="flex items-center space-x-1.5 btn-secondary text-sm">
                  <FaSignInAlt />
                  <span>Connexion</span>
                </Link>
                <Link to="/register" className="flex items-center space-x-1.5 btn-primary text-sm">
                  <FaUserPlus />
                  <span>S'inscrire</span>
                </Link>
              </div>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden text-2xl text-gray-600 p-2"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <FaTimes /> : <FaBars />}
          </button>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="md:hidden mt-4 space-y-1 pb-3 border-t border-gray-100 pt-3">
            <Link
              to="/epreuves"
              className="block py-2.5 px-3 text-gray-700 hover:text-primary-600 hover:bg-primary-50 rounded-lg font-medium"
              onClick={() => setMobileMenuOpen(false)}
            >
              Épreuves
            </Link>
            {isAuthenticated && (
              <Link
                to="/upload"
                className="block py-2.5 px-3 text-accent-600 font-medium hover:bg-accent-50 rounded-lg"
                onClick={() => setMobileMenuOpen(false)}
              >
                📤 Upload une épreuve
              </Link>
            )}
            {isAuthenticated && (user as any)?.is_staff && (
              <Link
                to="/admin-panel"
                className="block py-2.5 px-3 text-gray-700 hover:text-primary-600 hover:bg-primary-50 rounded-lg font-medium"
                onClick={() => setMobileMenuOpen(false)}
              >
                ⚙️ Panneau Admin
              </Link>
            )}
            {isAuthenticated ? (
              <>
                <Link
                  to="/profile"
                  className="block py-2.5 px-3 text-gray-700 hover:text-primary-600 hover:bg-primary-50 rounded-lg"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Profil ({user?.username})
                </Link>
                <button
                  onClick={() => {
                    logout()
                    setMobileMenuOpen(false)
                  }}
                  className="block w-full text-left py-2.5 px-3 text-red-500 hover:bg-red-50 rounded-lg font-medium"
                >
                  Déconnexion
                </button>
              </>
            ) : (
              <div className="space-y-1 pt-2">
                <Link
                  to="/login"
                  className="block py-2.5 px-3 text-gray-700 hover:text-primary-600 hover:bg-primary-50 rounded-lg font-medium"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Connexion
                </Link>
                <Link
                  to="/register"
                  className="block py-2.5 px-3 text-primary-600 font-semibold hover:bg-primary-50 rounded-lg"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  S'inscrire
                </Link>
              </div>
            )}
          </div>
        )}
      </nav>
    </header>
  )
}

export default Header
