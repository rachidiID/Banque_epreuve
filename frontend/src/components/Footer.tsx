import { Link } from 'react-router-dom'
import { FaGithub, FaEnvelope, FaBook, FaHeart } from 'react-icons/fa'

const Footer = () => {
  return (
    <footer className="bg-gray-900 text-white mt-16">
      <div className="container mx-auto px-4 py-10">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <div className="flex items-center space-x-2 text-xl font-bold mb-3">
              <FaBook className="text-primary-400" />
              <span>Banque d'Épreuves IMSP</span>
            </div>
            <p className="text-gray-400 text-sm leading-relaxed">
              Plateforme collaborative de partage d'épreuves académiques avec système de recommandation intelligent pour les étudiants de l'IMSP.
            </p>
          </div>

          <div>
            <h3 className="font-bold mb-3 text-gray-200">Navigation</h3>
            <ul className="space-y-2 text-sm">
              <li><Link to="/epreuves" className="text-gray-400 hover:text-primary-400 transition-colors">Épreuves</Link></li>
              <li><Link to="/register" className="text-gray-400 hover:text-primary-400 transition-colors">S'inscrire</Link></li>
              <li><Link to="/login" className="text-gray-400 hover:text-primary-400 transition-colors">Connexion</Link></li>
              <li><a href="/api/docs/" className="text-gray-400 hover:text-primary-400 transition-colors">API Documentation</a></li>
            </ul>
          </div>

          <div>
            <h3 className="font-bold mb-3 text-gray-200">Contact</h3>
            <ul className="space-y-2 text-sm">
              <li className="flex items-center space-x-2 text-gray-400">
                <FaEnvelope className="text-xs" />
                <span>contact@imsp.uac.bj</span>
              </li>
              <li className="flex items-center space-x-2 text-gray-400">
                <FaGithub className="text-xs" />
                <a href="https://github.com/rachidiID/Banque_epreuve" target="_blank" rel="noopener noreferrer" className="hover:text-primary-400 transition-colors">
                  GitHub
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-800 mt-8 pt-6 text-center text-gray-500 text-sm">
          <p>
            &copy; {new Date().getFullYear()} Banque d'Épreuves IMSP — Fait avec{' '}
            <FaHeart className="inline text-red-400 text-xs" /> pour l'IMSP
          </p>
        </div>
      </div>
    </footer>
  )
}

export default Footer
