/**
 * Backend API client - all CV/matching/scoring/demo calls go through here.
 */

import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || ''

export const api = axios.create({
  baseURL: API_URL || '/',
  headers: { 'Content-Type': 'application/json' },
})

export interface CVDocument {
  id: string
  raw_text?: string
  structured_data?: {
    candidate_info?: Record<string, unknown>
    sections?: unknown[]
    experiences?: unknown[]
    education?: unknown[]
    skills?: unknown[]
  }
  signed_url?: string | null
  original_file_path?: string
  status?: string
  quality_score?: number
  embedding_preview?: { dimension: number; first_5?: number[] }
  original_filename?: string
  created_at?: string
  candidate_info?: Record<string, unknown>
  source?: Record<string, unknown>
  experiences?: unknown[]
  skills?: unknown[]
}
