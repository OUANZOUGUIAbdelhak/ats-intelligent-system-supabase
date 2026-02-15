import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Search, FileText } from 'lucide-react'
import { api } from '@/lib/api'

export function Matching() {
  const [jobDesc, setJobDesc] = useState('')
  const [results, setResults] = useState<Array<{ cv: Record<string, unknown>; similarity_score: number }>>([])

  const searchMut = useMutation({
    mutationFn: async (description: string) => {
      const r = await api.post('/api/matching/semantic', null, {
        params: { job_description: description, top_n: 10 },
      })
      return r.data
    },
    onSuccess: (data) => {
      setResults(data.results ?? [])
    },
  })

  const handleSearch = () => {
    if (jobDesc.trim()) searchMut.mutate(jobDesc.trim())
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Semantic Matching</h1>
        <p className="text-slate-600 dark:text-slate-400 mt-1">
          Find CVs most similar to a job description using vector search
        </p>
      </div>

      <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
          Job description
        </label>
        <textarea
          value={jobDesc}
          onChange={(e) => setJobDesc(e.target.value)}
          placeholder="e.g. Senior Python developer with FastAPI and React experience, 5+ years..."
          className="w-full h-32 px-4 py-3 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white placeholder-slate-400"
          rows={4}
        />
        <button
          onClick={handleSearch}
          disabled={searchMut.isPending || !jobDesc.trim()}
          className="mt-4 flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Search className="w-5 h-5" />
          {searchMut.isPending ? 'Searching...' : 'Search'}
        </button>
      </div>

      {results.length > 0 && (
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
          <h2 className="text-xl font-bold mb-4 text-slate-900 dark:text-white">Results</h2>
          <div className="space-y-4">
            {results.map(({ cv, similarity_score }, i) => {
              const ci = (cv.structured_data as Record<string, unknown>)?.candidate_info as Record<string, unknown> | undefined
                ?? cv.candidate_info as Record<string, unknown> | undefined
              const name = ci?.full_name as string ?? 'Unknown'
              return (
                <div
                  key={String(cv.id)}
                  className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-full bg-gradient-to-r from-primary-500 to-primary-700 flex items-center justify-center text-white font-bold">
                      {String(name).charAt(0) || '?'}
                    </div>
                    <div>
                      <h3 className="font-semibold">{name}</h3>
                      <p className="text-sm text-slate-500">
                        Similarity: {(similarity_score * 100).toFixed(1)}%
                      </p>
                    </div>
                  </div>
                  <a
                    href={`/cvs/${cv.id}`}
                    className="flex items-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-700 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600"
                  >
                    <FileText className="w-4 h-4" />
                    View
                  </a>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {searchMut.isError && (
        <div className="p-4 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400">
          {String((searchMut.error as Error).message)}
        </div>
      )}
    </div>
  )
}
