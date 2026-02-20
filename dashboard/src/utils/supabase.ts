import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY environment variables')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Types based on our schema
export interface LanguageStats {
  language: string
  contributors: number
  recordings_uploaded: number
}

export interface UserStats {
  cv_user_id: string
  username: string
  joined_at: string
  total_contributions: number
  languages_contributed: number
}

export interface UserSentence {
  cv_user_id: string
  language: string
  text: string
  uploaded_at: string
}

// API functions
export async function getStatsByLanguage(): Promise<LanguageStats[]> {
  const { data, error } = await supabase
    .from('stats_by_language')
    .select('*')
  
  if (error) throw error
  return data || []
}

// Check if string looks like a UUID
export function isUUID(str: string): boolean {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(str)
}

export async function getUserStats(searchValue: string, searchField: 'cv_user_id' | 'username' = 'cv_user_id'): Promise<UserStats | null> {
  // Get user info from public_users view (no sensitive data)
  const { data: user, error: userError } = await supabase
    .from('public_users')
    .select('cv_user_id, username, created_at')
    .eq(searchField, searchValue)
    .single()
  
  if (userError) {
    if (userError.code === 'PGRST116') return null // Not found
    throw userError
  }
  
  const cvUserId = user.cv_user_id
  
  // Get stats from user_stats view (may not exist if no uploads yet)
  const { data: statsData } = await supabase
    .from('user_stats')
    .select('total_contributions, languages_contributed')
    .eq('cv_user_id', cvUserId)
  
  const stats = statsData?.[0]
  
  return {
    cv_user_id: user.cv_user_id,
    username: user.username,
    joined_at: user.created_at,
    total_contributions: stats?.total_contributions ?? 0,
    languages_contributed: stats?.languages_contributed ?? 0,
  }
}

export async function getUserSentences(cvUserId: string): Promise<UserSentence[]> {
  const { data, error } = await supabase
    .from('user_sentences')
    .select('*')
    .eq('cv_user_id', cvUserId)
    .order('uploaded_at', { ascending: false })
  
  if (error) throw error
  return data || []
}

export async function getTotalStats() {
  // Get user count from public_users view
  const { count: userCount, error: usersError } = await supabase
    .from('public_users')
    .select('*', { count: 'exact', head: true })
  
  // Get recordings count from stats_by_language (no direct table access)
  const { data: langStats, error: statsError } = await supabase
    .from('stats_by_language')
    .select('recordings_uploaded')
  
  if (usersError) throw usersError
  if (statsError) throw statsError
  
  const totalRecordings = (langStats || []).reduce((sum, s) => sum + s.recordings_uploaded, 0)
  
  return {
    totalContributors: userCount ?? 0,
    totalRecordings,
  }
}
