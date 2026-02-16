import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Search, FileText, Briefcase } from 'lucide-react'
import { api } from '@/lib/api'

interface JobOffer {
  id: string
  title: string
  description: string
  required_skills?: string[]
  location?: string
  department?: string
}

export function Matching() {
  const [jobDesc, setJobDesc] = useState('')
  const [results, setResults] = useState<Array<{ cv: Record<string, unknown>; similarity_score: number }>>([])

  const { data: jobOffersData } = useQuery({
    queryKey: ['job-offers'],
    queryFn: async () => {
      const r = await api.get('/api/demo/job-offers')
      return r.data
    },
  })

  const jobOffers: JobOffer[] = jobOffersData?.job_offers ?? []

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

  const handleUseJobOffer = (job: JobOffer) => {
    const text = [job.title, job.description, ...(job.required_skills ?? [])].join(' ')
    setJobDesc(text)
    searchMut.mutate(text)
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Semantic Matching</h1>
        <p className="text-slate-600 dark:text-slate-400 mt-1">
          Find resumes that match job descriptions. Use example job offers or type your own.
        </p>
      </div>

      {jobOffers.length > 0 && (
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
          <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
            <Briefcase className="w-5 h-5" />
            Example job offers
          </h2>
          <p className="text-sm text-slate-500 mb-4">Click to search for matching resumes</p>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {jobOffers.map((job) => (
              <button
                key={job.id}
                onClick={() => handleUseJobOffer(job)}
                disabled={searchMut.isPending}
                className="text-left p-4 rounded-lg border border-slate-200 dark:border-slate-700 hover:border-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors"
              >
                <h3 className="font-semibold text-slate-900 dark:text-white">{job.title}</h3>
                {job.location && (
                  <p className="text-xs text-slate-500 mt-1">{job.location}</p>
                )}
                {job.required_skills?.length ? (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {job.required_skills.slice(0, 4).map((s) => (
                      <span
                        key={s}
                        className="px-2 py-0.5 text-xs bg-slate-100 dark:bg-slate-700 rounded"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                ) : null}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
          Job description (or use an example above)
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
          <h2 className="text-xl font-bold mb-4 text-slate-900 dark:text-white">Matching resumes</h2>
          <div className="space-y-4">
            {results.map(({ cv, similarity_score }, i) => {
              const ci = (cv.structured_data as Record<string, unknown>)?.candidate_info as Record<string, unknown> | undefined
                ?? cv.candidate_info as Record<string, unknown> | undefined
              const name = ci?.full_name as string ?? 'Unknown'
              const skills = (cv.structured_data as Record<string, unknown>)?.skills as Array<Record<string, unknown>> | undefined
                ?? cv.skills as Array<Record<string, unknown>> | undefined
              const skillList = skills?.slice(0, 5).map((s) => typeof s === 'string' ? s : (s.skill as string)) ?? []
              return (
                <div
                  key={String(cv.id)}
                  className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3"
                >
                  <div className="flex items-center gap-3 flex-1">
                    <div className="w-12 h-12 rounded-full bg-gradient-to-r from-primary-500 to-primary-700 flex items-center justify-center text-white font-bold flex-shrink-0">
                      {String(name).charAt(0) || '?'}
                    </div>
                    <div className="min-w-0">
                      <h3 className="font-semibold text-slate-900 dark:text-white">{name}</h3>
                      <p className="text-sm text-slate-500">
                        Similarity: {(similarity_score * 100).toFixed(1)}%
                      </p>
                      {skillList.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {skillList.map((sk, j) => (
                            <span key={j} className="text-xs px-2 py-0.5 bg-slate-100 dark:bg-slate-700 rounded">
                              {sk}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                  <a
                    href={`/cvs/${cv.id}`}
                    className="flex items-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-700 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 self-start sm:self-center"
                  >
                    <FileText className="w-4 h-4" />
                    View resume
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

      {results.length === 0 && searchMut.isSuccess && (
        <div className="p-6 rounded-xl border border-slate-200 dark:border-slate-700 text-center text-slate-500">
          No matching resumes found. Load sample resumes from the Demo page first.
        </div>
      )}
    </div>
  )
}
