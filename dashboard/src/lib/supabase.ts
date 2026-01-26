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
  recordings_pending: number
}

export interface UserStats {
  cv_user_id: string
  username: string
  joined_at: string
  current_language: string | null
  total_contributions: number
  recordings_uploaded: number
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

export async function getUserStats(cvUserId: string): Promise<UserStats | null> {
  const { data, error } = await supabase
    .from('user_stats')
    .select('*')
    .eq('cv_user_id', cvUserId)
    .single()
  
  if (error) {
    if (error.code === 'PGRST116') return null // Not found
    throw error
  }
  return data
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
  const { data: users, error: usersError } = await supabase
    .from('users')
    .select('id', { count: 'exact', head: true })
  
  const { data: recordings, error: recordingsError } = await supabase
    .from('recordings')
    .select('id', { count: 'exact', head: true })
    .eq('status', 'uploaded')
  
  if (usersError) throw usersError
  if (recordingsError) throw recordingsError
  
  return {
    totalContributors: users?.length ?? 0,
    totalRecordings: recordings?.length ?? 0,
  }
}
