import { createContext, useContext, useState, useEffect } from 'react'
import type { ReactNode } from 'react'
import type { Language } from './i18n'

interface LanguageContextType {
  lang: Language
  setLang: (lang: Language) => void
}

const LanguageContext = createContext<LanguageContextType | null>(null)

function getInitialLanguage(): Language {
  if (typeof window === 'undefined') return 'es'
  try {
    const stored = localStorage.getItem('dashboard_lang')
    if (stored === 'en' || stored === 'es') return stored
    const browserLang = navigator.language.slice(0, 2)
    return browserLang === 'en' ? 'en' : 'es'
  } catch {
    return 'es'
  }
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Language>('es')
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setLangState(getInitialLanguage())
    setMounted(true)
  }, [])

  const setLang = (newLang: Language) => {
    setLangState(newLang)
    try {
      localStorage.setItem('dashboard_lang', newLang)
    } catch {
      // localStorage might not be available
    }
  }

  // Prevent hydration mismatch by not rendering until mounted
  if (!mounted) {
    return <>{children}</>
  }

  return (
    <LanguageContext.Provider value={{ lang, setLang }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  const context = useContext(LanguageContext)
  if (!context) {
    // Return default during initial render
    return { lang: 'es' as Language, setLang: () => {} }
  }
  return context
}
