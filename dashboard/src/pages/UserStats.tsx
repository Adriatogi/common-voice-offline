import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getUserStats, getUserSentences } from '../utils/supabase'
import { useLanguage } from '../utils/LanguageContext'
import { t } from '../utils/i18n'
import { LanguageSwitcher } from '../components/LanguageSwitcher'
import type { UserStats as UserStatsType, UserSentence } from '../utils/supabase'

export default function UserStats() {
  const { lang } = useLanguage()
  const { cvUserId } = useParams<{ cvUserId: string }>()
  const [stats, setStats] = useState<UserStatsType | null>(null)
  const [sentences, setSentences] = useState<UserSentence[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    async function fetchUserData() {
      if (!cvUserId) return

      try {
        const [statsData, sentencesData] = await Promise.all([
          getUserStats(cvUserId),
          getUserSentences(cvUserId)
        ])
        
        if (statsData) {
          setStats(statsData)
          setSentences(sentencesData)
        } else {
          setNotFound(true)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load stats')
      } finally {
        setLoading(false)
      }
    }

    fetchUserData()
  }, [cvUserId])

  if (loading) {
    return <div className="container"><div className="loading">{t(lang, 'loading')}</div></div>
  }

  if (error) {
    return (
      <div className="container">
        <LanguageSwitcher />
        <Link to="/" className="back-link">{t(lang, 'back')}</Link>
        <div className="error">{t(lang, 'error')}: {error}</div>
      </div>
    )
  }

  if (notFound) {
    return (
      <div className="container">
        <LanguageSwitcher />
        <Link to="/" className="back-link">{t(lang, 'back')}</Link>
        <div className="not-found">
          <h2>{t(lang, 'userNotFound')}</h2>
          <p>{t(lang, 'userNotFoundDesc')} <code>{cvUserId}</code></p>
          <p style={{ marginTop: '0.5rem', fontSize: '0.9rem', color: '#666' }}>
            {t(lang, 'userNotFoundHint')}
          </p>
        </div>
      </div>
    )
  }

  if (!stats) return null

  const joinedDate = new Date(stats.joined_at).toLocaleDateString(lang === 'es' ? 'es-ES' : 'en-US')

  return (
    <div className="container">
      <LanguageSwitcher />
      <Link to="/" className="back-link">{t(lang, 'back')}</Link>

      <div className="user-info">
        <h1>{stats.username}</h1>
        <p className="joined">{t(lang, 'joinedOn')} {joinedDate}</p>
      </div>

      <div className="user-stats-grid">
        <div className="stat-box">
          <div className="stat-value">{stats.total_contributions}</div>
          <div className="stat-label">{t(lang, 'totalContributions')}</div>
        </div>
        <div className="stat-box">
          <div className="stat-value">{stats.recordings_uploaded}</div>
          <div className="stat-label">{t(lang, 'recordings')}</div>
        </div>
        {stats.current_language && (
          <div className="stat-box">
            <div className="stat-value" style={{ fontSize: '1.25rem' }}>{stats.current_language}</div>
            <div className="stat-label">{t(lang, 'currentLanguage')}</div>
          </div>
        )}
      </div>

      {sentences.length > 0 && (
        <div className="sentences-section">
          <h3>{t(lang, 'uploadedSentences')}</h3>
          <div className="sentences-list">
            {sentences.map((sentence, index) => (
              <div key={index} className="sentence-item">
                <span className="sentence-text">{sentence.text}</span>
                <div className="sentence-meta">
                  <span className="sentence-lang">{sentence.language}</span>
                  <span className="sentence-date">
                    {new Date(sentence.uploaded_at).toLocaleDateString(lang === 'es' ? 'es-ES' : 'en-US')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="share-section">
        <h3>{t(lang, 'shareTitle')}</h3>
        <div className="share-url">
          <input
            type="text"
            value={window.location.href}
            readOnly
            className="share-input"
          />
          <button
            className="copy-button"
            onClick={() => navigator.clipboard.writeText(window.location.href)}
          >
            {t(lang, 'copyButton')}
          </button>
        </div>
      </div>

      <footer className="footer">
        <p><a href="https://t.me/cv_offline_bot" target="_blank" rel="noopener noreferrer">@cv_offline_bot</a></p>
        <p style={{ marginTop: '0.75rem' }}>
          <a 
            href="https://github.com/Adriatogi/common-voice-offline" 
            target="_blank" 
            rel="noopener noreferrer"
            style={{ 
              display: 'inline-flex', 
              alignItems: 'center', 
              gap: '0.4rem',
              background: '#24292e',
              color: 'white',
              padding: '0.5rem 1rem',
              borderRadius: '6px',
              textDecoration: 'none',
              fontSize: '0.9rem'
            }}
          >
            <svg height="18" width="18" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
            </svg>
            {t(lang, 'footerGithub')}
          </a>
        </p>
      </footer>
    </div>
  )
}
