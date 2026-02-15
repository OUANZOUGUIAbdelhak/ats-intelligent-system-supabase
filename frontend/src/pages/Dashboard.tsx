import { Link } from 'react-router-dom'
import { FileText, Search, Upload, Rocket } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export function Dashboard() {
  const { data } = useQuery({
    queryKey: ['cvs-summary'],
    queryFn: async () => {
      const r = await api.get('/api/cv/search', { params: { page: 1, limit: 5 } })
      return r.data
    },
    retry: false,
  })

  const total = data?.total ?? 0

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Dashboard</h1>
        <p className="text-slate-600 dark:text-slate-400 mt-1">
          Applicant Tracking System with OCR, LLM structuring, and semantic search
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Link
          to="/cvs"
          className="p-6 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-primary-400 transition-colors"
        >
          <FileText className="w-10 h-10 text-primary-500 mb-3" />
          <h3 className="font-semibold text-slate-900 dark:text-white">CVs</h3>
          <p className="text-2xl font-bold text-primary-600 mt-1">{total}</p>
          <p className="text-sm text-slate-500 mt-1">Total documents</p>
        </Link>
        <Link
          to="/cvs"
          className="p-6 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-primary-400 transition-colors"
        >
          <Upload className="w-10 h-10 text-primary-500 mb-3" />
          <h3 className="font-semibold text-slate-900 dark:text-white">Upload</h3>
          <p className="text-sm text-slate-500 mt-1">Add new CVs</p>
        </Link>
        <Link
          to="/matching"
          className="p-6 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-primary-400 transition-colors"
        >
          <Search className="w-10 h-10 text-primary-500 mb-3" />
          <h3 className="font-semibold text-slate-900 dark:text-white">Matching</h3>
          <p className="text-sm text-slate-500 mt-1">Semantic search</p>
        </Link>
        <Link
          to="/demo"
          className="p-6 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-primary-400 transition-colors"
        >
          <Rocket className="w-10 h-10 text-primary-500 mb-3" />
          <h3 className="font-semibold text-slate-900 dark:text-white">Demo</h3>
          <p className="text-sm text-slate-500 mt-1">Load demo data</p>
        </Link>
      </div>

      {data?.results?.length ? (
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
          <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">Recent CVs</h2>
          <div className="space-y-3">
            {data.results.map((cv: Record<string, unknown>) => (
              <Link
                key={String(cv.id)}
                to={`/cvs/${cv.id}`}
                className="block p-4 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-900/50"
              >
                <div className="flex justify-between items-center">
                  <div>
                    <span className="font-medium">
                      {(() => {
                        const sd = cv.structured_data as Record<string, unknown> | undefined
                        const ci = sd?.candidate_info as Record<string, unknown> | undefined
                        const name = ci?.full_name as string | undefined
                        return name ?? (cv.candidate_info as Record<string, unknown>)?.full_name ?? 'Unknown'
                      })()}
                    </span>
                    <p className="text-sm text-slate-500">{String(cv.original_filename ?? 'CV')}</p>
                  </div>
                  <span
                    className={`px-2 py-1 text-xs rounded-full ${
                      cv.status === 'active'
                        ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                        : 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300'
                    }`}
                  >
                    {String(cv.status ?? '—')}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      ) : (
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-12 text-center">
          <FileText className="w-16 h-16 mx-auto text-slate-400 mb-4" />
          <p className="text-slate-600 dark:text-slate-400">No CVs yet</p>
          <Link
            to="/demo"
            className="inline-flex items-center gap-2 mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            <Rocket className="w-4 h-4" />
            Load Demo Data
          </Link>
        </div>
      )}
    </div>
  )
}
