import { Link } from 'react-router-dom'
import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { FaBars, FaTimes, FaBook, FaUser, FaSignInAlt, FaSignOutAlt, FaCloudUploadAlt } from 'react-icons/fa'

const Header = () => {
  const { user, isAuthenticated, logout } = useAuth()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <header className="bg-white shadow-md">
      <nav className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center space-x-2 text-2xl font-bold text-primary-600">
            <FaBook />
            <span>Banque d'Épreuves</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-6">
            <Link to="/epreuves" className="text-gray-700 hover:text-primary-600">
              Épreuves
            </Link>
            {isAuthenticated && (
              <Link 
                to="/upload" 
                className="flex items-center space-x-1 btn-primary text-sm"
              >
                <FaCloudUploadAlt />
                <span>Upload</span>
              </Link>
            )}
            {isAuthenticated ? (
              <>
                <Link to="/profile" className="flex items-center space-x-1 text-gray-700 hover:text-primary-600">
                  <FaUser />
                  <span>{user?.username}</span>
                </Link>
                <button onClick={logout} className="flex items-center space-x-1 text-gray-700 hover:text-primary-600">
                  <FaSignOutAlt />
                  <span>Déconnexion</span>
                </button>
              </>
            ) : (
              <Link to="/login" className="flex items-center space-x-1 btn-primary">
                <FaSignInAlt />
                <span>Connexion</span>
              </Link>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden text-2xl"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <FaTimes /> : <FaBars />}
          </button>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="md:hidden mt-4 space-y-2">
            <Link
              to="/epreuves"
              className="block py-2 text-gray-700 hover:text-primary-600"
              onClick={() => setMobileMenuOpen(false)}
            >
              Épreuves
            </Link>
            {isAuthenticated && (
              <Link
                to="/upload"
                className="block py-2 text-primary-600 font-medium hover:text-primary-700"
                onClick={() => setMobileMenuOpen(false)}
              >
                📤 Upload une épreuve
              </Link>
            )}
            {isAuthenticated ? (
              <>
                <Link
                  to="/profile"
                  className="block py-2 text-gray-700 hover:text-primary-600"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Profil ({user?.username})
                </Link>
                <button
                  onClick={() => {
                    logout()
                    setMobileMenuOpen(false)
                  }}
                  className="block w-full text-left py-2 text-gray-700 hover:text-primary-600"
                >
                  Déconnexion
                </button>
              </>
            ) : (
              <Link
                to="/login"
                className="block py-2 text-primary-600 font-semibold"
                onClick={() => setMobileMenuOpen(false)}
              >
                Connexion
              </Link>
            )}
          </div>
        )}
      </nav>
    </header>
  )
}

export default Header
