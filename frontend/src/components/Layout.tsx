import { ReactNode, useState, useEffect } from 'react'
import Header from './Header'
import Footer from './Footer'
import ProfileCompletionModal from './ProfileCompletionModal'
import { useAuth } from '@/contexts/AuthContext'

interface LayoutProps {
  children: ReactNode
}

const Layout = ({ children }: LayoutProps) => {
  const { user, isAuthenticated, isLoading } = useAuth()
  const [showProfileModal, setShowProfileModal] = useState(false)

  useEffect(() => {
    if (isLoading || !isAuthenticated || !user) return

    // Afficher le modal si niveau ou filière manquant
    const profileIncomplete = !user.niveau || !user.filiere
    if (!profileIncomplete) return

    // Vérifier si l'utilisateur a déjà ignoré récemment (7 jours)
    const skippedAt = localStorage.getItem('profile_completion_skipped')
    if (skippedAt) {
      const daysSinceSkipped = (Date.now() - Number(skippedAt)) / (1000 * 60 * 60 * 24)
      if (daysSinceSkipped < 7) return
    }

    // Délai léger pour ne pas interrompre la navigation
    const timer = setTimeout(() => setShowProfileModal(true), 1500)
    return () => clearTimeout(timer)
  }, [isAuthenticated, isLoading, user])

  return (
    <div className="flex flex-col min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 transition-colors duration-200">
      <Header />
      <main className="flex-grow container mx-auto px-4 py-8">
        {children}
      </main>
      <Footer />
      {showProfileModal && (
        <ProfileCompletionModal onClose={() => setShowProfileModal(false)} />
      )}
    </div>
  )
}

export default Layout

