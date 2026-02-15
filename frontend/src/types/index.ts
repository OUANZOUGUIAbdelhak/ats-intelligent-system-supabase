export interface CVListItem {
  id: string
  structured_data?: { candidate_info?: { full_name?: string }; sections?: unknown[] }
  source?: { original_filename?: string }
  candidate_info?: { full_name?: string }
  status?: string
}
