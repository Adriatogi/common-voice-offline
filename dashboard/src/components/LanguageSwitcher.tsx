import { useLanguage } from '../utils/LanguageContext'

export function LanguageSwitcher() {
  const { lang, setLang } = useLanguage()

  return (
    <div className="language-switcher">
      <button
        className={lang === 'en' ? 'active' : ''}
        onClick={() => setLang('en')}
      >
        EN
      </button>
      <button
        className={lang === 'es' ? 'active' : ''}
        onClick={() => setLang('es')}
      >
        ES
      </button>
    </div>
  )
}
