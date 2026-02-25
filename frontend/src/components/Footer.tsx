import { Link } from 'react-router-dom'
import { FaGithub, FaEnvelope, FaPhone } from 'react-icons/fa'

const Footer = () => {
  return (
    <footer className="bg-gray-800 text-white mt-12">
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <h3 className="text-xl font-bold mb-4">Banque d'Épreuves</h3>
            <p className="text-gray-300">
              Plateforme collaborative de partage d'épreuves académiques avec système de recommandation intelligent.
            </p>
          </div>

          <div>
            <h3 className="text-xl font-bold mb-4">Liens rapides</h3>
            <ul className="space-y-2">
              <li>
                <Link to="/epreuves" className="text-gray-300 hover:text-white">
                  Parcourir les épreuves
                </Link>
              </li>
              <li>
                <Link to="/about" className="text-gray-300 hover:text-white">
                  À propos
                </Link>
              </li>
              <li>
                <Link to="/contact" className="text-gray-300 hover:text-white">
                  Contact
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="text-xl font-bold mb-4">Contact</h3>
            <ul className="space-y-2">
              <li className="flex items-center space-x-2">
                <FaEnvelope />
                <span className="text-gray-300">contact@banque-epreuves.com</span>
              </li>
              <li className="flex items-center space-x-2">
                <FaPhone />
                <span className="text-gray-300">+229 XX XX XX XX</span>
              </li>
              <li className="flex items-center space-x-2">
                <FaGithub />
                <a href="https://github.com" className="text-gray-300 hover:text-white">
                  GitHub
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-700 mt-8 pt-6 text-center text-gray-400">
          <p>&copy; {new Date().getFullYear()} Banque d'Épreuves. Tous droits réservés.</p>
        </div>
      </div>
    </footer>
  )
}

export default Footer
