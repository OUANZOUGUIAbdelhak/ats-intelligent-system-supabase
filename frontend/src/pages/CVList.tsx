import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { FileText, RefreshCw } from 'lucide-react'
import { api } from '@/lib/api'
import { CVUploader } from '@/components/cv/CVUploader'

export function CVList() {
  const [refreshKey, setRefreshKey] = useState(0)
  const navigate = useNavigate()

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['cvs', refreshKey],
    queryFn: async () => {
      const r = await api.get('/api/cv/search', { params: { page: 1, limit: 50 } })
      return r.data
    },
  })

  const handleUploadSuccess = () => {
    setRefreshKey((k) => k + 1)
    refetch()
  }

  const results = data?.results ?? []

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white">CVs</h1>
          <p className="text-slate-600 dark:text-slate-400">Upload and manage candidate CVs</p>
        </div>
        <button
          onClick={() => {
            setRefreshKey((k) => k + 1)
            refetch()
          }}
          className="px-4 py-2 bg-slate-200 dark:bg-slate-700 rounded-lg hover:bg-slate-300 dark:hover:bg-slate-600 flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      <CVUploader onUploadSuccess={handleUploadSuccess} />

      <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
        <h2 className="text-xl font-bold mb-4 text-slate-900 dark:text-white">CV List</h2>
        {isLoading ? (
          <div className="py-12 text-center">
            <div className="animate-spin w-10 h-10 border-4 border-primary-500 border-t-transparent rounded-full mx-auto" />
            <p className="mt-4 text-slate-500">Loading...</p>
          </div>
        ) : results.length > 0 ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {results.map((cv: Record<string, unknown>) => {
              const ci = (cv.structured_data as Record<string, unknown>)?.candidate_info as Record<string, unknown> | undefined
                ?? cv.candidate_info as Record<string, unknown> | undefined
              const name = ci?.full_name as string ?? 'Unknown'
              const filename = (cv.source as Record<string, unknown>)?.original_filename as string ?? cv.original_filename as string ?? 'CV'
              return (
                <div
                  key={String(cv.id)}
                  onClick={() => navigate(`/cvs/${cv.id}`)}
                  className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-900/50 cursor-pointer transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-full bg-gradient-to-r from-primary-500 to-primary-700 flex items-center justify-center text-white font-bold text-lg">
                      {String(name).charAt(0) || '?'}
                    </div>
                    <div className="min-w-0 flex-1">
                      <h3 className="font-semibold text-slate-900 dark:text-white truncate">{name}</h3>
                      <p className="text-sm text-slate-500 truncate">{filename}</p>
                    </div>
                  </div>
                  <div className="mt-3 flex justify-end">
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        cv.status === 'active'
                          ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                          : cv.status === 'processing'
                          ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                          : 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300'
                      }`}
                    >
                      {String(cv.status ?? '—')}
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <div className="py-12 text-center">
            <FileText className="w-14 h-14 mx-auto text-slate-400 mb-4" />
            <p className="text-slate-600 dark:text-slate-400">No CVs yet</p>
            <p className="text-sm mt-2 text-slate-500">Upload a CV above or load demo data</p>
          </div>
        )}
      </div>
    </div>
  )
}
