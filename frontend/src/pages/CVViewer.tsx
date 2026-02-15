import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Download, FileText } from 'lucide-react'
import { api } from '@/lib/api'

export function CVViewer() {
  const { cvId } = useParams<{ cvId: string }>()
  const navigate = useNavigate()

  const { data: cv, isLoading } = useQuery({
    queryKey: ['cv', cvId],
    queryFn: async () => {
      const r = await api.get(`/api/cv/${cvId}`)
      return r.data
    },
    enabled: !!cvId,
  })

  if (isLoading || !cv) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full" />
      </div>
    )
  }

  const ci = cv.structured_data?.candidate_info ?? cv.candidate_info ?? {}
  const experiences = cv.structured_data?.experiences ?? cv.experiences ?? []
  const skills = cv.structured_data?.skills ?? cv.skills ?? []
  const signedUrl = cv.signed_url

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/cvs')}
          className="flex items-center gap-2 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
        >
          <ArrowLeft className="w-5 h-5" />
          Back
        </button>
        {signedUrl && (
          <a
            href={signedUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            <Download className="w-4 h-4" />
            View / Download original
          </a>
        )}
      </div>

      <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-20 h-20 rounded-full bg-gradient-to-r from-primary-500 to-primary-700 flex items-center justify-center text-white text-2xl font-bold">
            {(ci.full_name as string)?.charAt(0) ?? '?'}
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
              {(ci.full_name as string) ?? 'Unknown'}
            </h1>
            <p className="text-slate-500">{cv.original_filename ?? 'CV'}</p>
            <span className="inline-block mt-2 px-3 py-1 text-sm rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
              {cv.status ?? '—'}
            </span>
          </div>
        </div>

        {(ci.email || ci.phone || ci.location) && (
          <div className="grid gap-4 md:grid-cols-3 mb-6">
            {ci.email && (
              <div>
                <p className="text-sm text-slate-500">Email</p>
                <p className="font-medium">{String(ci.email)}</p>
              </div>
            )}
            {ci.phone && (
              <div>
                <p className="text-sm text-slate-500">Phone</p>
                <p className="font-medium">{String(ci.phone)}</p>
              </div>
            )}
            {ci.location && (
              <div>
                <p className="text-sm text-slate-500">Location</p>
                <p className="font-medium">{String(ci.location)}</p>
              </div>
            )}
          </div>
        )}
      </div>

      {skills.length > 0 && (
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
          <h2 className="text-xl font-bold mb-4 text-slate-900 dark:text-white">Skills</h2>
          <div className="flex flex-wrap gap-2">
            {skills.map((s: Record<string, unknown> | string, i: number) => (
              <span
                key={i}
                className="px-3 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-full text-sm"
              >
                {typeof s === 'string' ? s : (s.skill as string) ?? (s as string)}
              </span>
            ))}
          </div>
        </div>
      )}

      {experiences.length > 0 && (
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
          <h2 className="text-xl font-bold mb-4 text-slate-900 dark:text-white">Experience</h2>
          <div className="space-y-4">
            {experiences.map((exp: Record<string, unknown>, i: number) => (
              <div key={i} className="border-l-2 border-primary-500 pl-4">
                <h3 className="font-semibold">{(exp.job_title as string) ?? (exp.title as string) ?? '—'}</h3>
                <p className="text-sm text-slate-500">
                  {String(exp.company ?? '—')} • {String(exp.start_date ?? '')} – {String(exp.end_date ?? 'Present')}
                </p>
                {exp.description && (
                  <p className="mt-2 text-slate-600 dark:text-slate-400">{String(exp.description)}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {cv.raw_text && (
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
          <h2 className="text-xl font-bold mb-4 text-slate-900 dark:text-white flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Raw OCR text
          </h2>
          <pre className="whitespace-pre-wrap text-sm text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-900 p-4 rounded-lg overflow-x-auto max-h-64 overflow-y-auto">
            {cv.raw_text}
          </pre>
        </div>
      )}

      <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
        <h2 className="text-xl font-bold mb-4 text-slate-900 dark:text-white">Structured data (JSON)</h2>
        <pre className="text-xs text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-900 p-4 rounded-lg overflow-auto max-h-80">
          {JSON.stringify(cv.structured_data ?? {}, null, 2)}
        </pre>
      </div>

      {cv.embedding_preview && (
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
          <h2 className="text-xl font-bold mb-4 text-slate-900 dark:text-white">Embedding</h2>
          <p className="text-slate-600 dark:text-slate-400">
            Dimension: {cv.embedding_preview.dimension}
            {cv.embedding_preview.first_5?.length ? (
              <> • First 5: [{cv.embedding_preview.first_5.map((n) => n.toFixed(4)).join(', ')}]</>
            ) : null}
          </p>
        </div>
      )}
    </div>
  )
}
