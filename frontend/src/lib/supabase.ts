/**
 * Supabase client (anon key) for frontend.
 * Used for auth and optional direct DB access.
 */

import { createClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL || ''
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || ''

export const supabase = url && anonKey ? createClient(url, anonKey) : null
