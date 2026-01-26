import { useEffect, useState } from 'react'
import { getStatsByLanguage, supabase } from '../lib/supabase'
import { useLanguage } from '../lib/LanguageContext'
import { t } from '../lib/i18n'
import { LanguageSwitcher } from '../components/LanguageSwitcher'
import type { LanguageStats } from '../lib/supabase'

export default function Home() {
  const { lang } = useLanguage()
  const [stats, setStats] = useState<LanguageStats[]>([])
  const [totals, setTotals] = useState({ contributors: 0, recordings: 0, languages: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lookupId, setLookupId] = useState('')

  useEffect(() => {
    async function fetchStats() {
      try {
        const languageStats = await getStatsByLanguage()
        const filteredStats = languageStats.filter(s => s.language)
        filteredStats.sort((a, b) => 
          (b.recordings_uploaded + b.recordings_pending) - (a.recordings_uploaded + a.recordings_pending)
        )
        setStats(filteredStats)

        const { count: userCount } = await supabase
          .from('users')
          .select('*', { count: 'exact', head: true })

        const { count: recordingCount } = await supabase
          .from('recordings')
          .select('*', { count: 'exact', head: true })
          .eq('status', 'uploaded')

        setTotals({
          contributors: userCount || 0,
          recordings: recordingCount || 0,
          languages: filteredStats.length,
        })
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load stats')
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
  }, [])

  const handleLookup = (e: React.FormEvent) => {
    e.preventDefault()
    if (lookupId.trim()) {
      window.location.href = `/stats/${lookupId.trim()}`
    }
  }

  if (loading) {
    return <div className="container"><div className="loading">{t(lang, 'loading')}</div></div>
  }

  if (error) {
    return <div className="container"><div className="error">{t(lang, 'error')}: {error}</div></div>
  }

  const totalUploaded = stats.reduce((sum, s) => sum + s.recordings_uploaded, 0)
  const totalPending = stats.reduce((sum, s) => sum + s.recordings_pending, 0)
  const totalContributors = stats.reduce((sum, s) => sum + s.contributors, 0)

  return (
    <div className="container">
      <LanguageSwitcher />
      
      <h1>{t(lang, 'title')}</h1>
      <p style={{ color: '#666', marginBottom: '2rem' }}>{t(lang, 'subtitle')}</p>

      <div className="totals">
        <div className="stat-box">
          <div className="stat-value">{totals.contributors}</div>
          <div className="stat-label">{t(lang, 'contributors')}</div>
        </div>
        <div className="stat-box">
          <div className="stat-value">{totals.recordings}</div>
          <div className="stat-label">{t(lang, 'recordings')}</div>
        </div>
        <div className="stat-box">
          <div className="stat-value">{totals.languages}</div>
          <div className="stat-label">{t(lang, 'languages')}</div>
        </div>
      </div>

      <div className="lookup-section">
        <h2>{t(lang, 'lookupTitle')}</h2>
        <form onSubmit={handleLookup} className="lookup-form">
          <input
            type="text"
            placeholder={t(lang, 'lookupPlaceholder')}
            value={lookupId}
            onChange={(e) => setLookupId(e.target.value)}
            className="lookup-input"
          />
          <button type="submit" className="lookup-button">{t(lang, 'lookupButton')}</button>
        </form>
        <p className="lookup-hint">{t(lang, 'lookupHint')}</p>
      </div>

      <div className="language-stats">
        <h2>{t(lang, 'leaderboardTitle')}</h2>
        {stats.length === 0 ? (
          <p style={{ color: '#888', padding: '1rem', background: 'white', border: '1px solid #e0e0e0', borderRadius: '8px' }}>
            {t(lang, 'noLanguageData')}
          </p>
        ) : (
          <table className="stats-table">
            <thead>
              <tr>
                <th>{t(lang, 'tableRank')}</th>
                <th>{t(lang, 'tableLanguage')}</th>
                <th>{t(lang, 'tableContributors')}</th>
                <th>{t(lang, 'tableUploaded')}</th>
                <th>{t(lang, 'tablePending')}</th>
                <th>{t(lang, 'tableTotal')}</th>
              </tr>
            </thead>
            <tbody>
              {stats.map((stat, index) => (
                <tr key={stat.language}>
                  <td style={{ color: index < 3 ? '#d97706' : '#888', fontWeight: index < 3 ? 600 : 400 }}>
                    {index + 1}
                  </td>
                  <td style={{ fontWeight: 500 }}>{stat.language}</td>
                  <td>{stat.contributors}</td>
                  <td>{stat.recordings_uploaded}</td>
                  <td>{stat.recordings_pending}</td>
                  <td style={{ fontWeight: 500 }}>{stat.recordings_uploaded + stat.recordings_pending}</td>
                </tr>
              ))}
              {stats.length > 1 && (
                <tr style={{ background: '#f5f5f5', fontWeight: 600 }}>
                  <td></td>
                  <td>{t(lang, 'tableTotal')}</td>
                  <td>{totalContributors}</td>
                  <td>{totalUploaded}</td>
                  <td>{totalPending}</td>
                  <td>{totalUploaded + totalPending}</td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      <footer className="footer">
        <p>{t(lang, 'footerContribute')} <a href="https://t.me/cv_offline_bot" target="_blank" rel="noopener noreferrer">@cv_offline_bot</a></p>
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
