import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Rocket, CheckCircle, Loader2, FileText } from 'lucide-react'
import { api } from '@/lib/api'

export function Demo() {
  const [steps, setSteps] = useState<Array<{
    filename?: string
    cv_index?: number
    cv_id: string
    steps: Array<{ name: string; status: string; note?: string; dim?: number }>
    error?: string
  }>>([])
  const queryClient = useQueryClient()

  const loadMut = useMutation({
    mutationFn: async () => {
      const r = await api.get('/api/demo/load', { params: { use_pdfs: true } })
      return r.data
    },
    onSuccess: (data) => {
      setSteps(data.steps ?? [])
      queryClient.invalidateQueries({ queryKey: ['cvs'] })
    },
  })

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Demo</h1>
        <p className="text-slate-600 dark:text-slate-400 mt-1">
          Load 10 sample resume PDFs and run the full pipeline (OCR → LLM → Embedding → Store)
        </p>
      </div>

      <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-8">
        <button
          onClick={() => loadMut.mutate()}
          disabled={loadMut.isPending}
          className="flex items-center gap-3 px-8 py-4 bg-primary-600 text-white rounded-xl hover:bg-primary-700 disabled:opacity-50 text-lg font-semibold"
        >
          {loadMut.isPending ? (
            <>
              <Loader2 className="w-6 h-6 animate-spin" />
              Processing 10 sample resumes...
            </>
          ) : (
            <>
              <Rocket className="w-6 h-6" />
              Load Sample Resumes
            </>
          )}
        </button>

        {loadMut.isSuccess && (
          <div className="mt-6 p-4 rounded-lg bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 flex items-center gap-3">
            <CheckCircle className="w-6 h-6" />
            <span>
              Loaded {loadMut.data?.total ?? 0} resumes. Go to <a href="/matching" className="underline font-medium">Matching</a> to find candidates for example job offers.
            </span>
          </div>
        )}

        {steps.length > 0 && (
          <div className="mt-8 space-y-6">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">Pipeline steps</h2>
            {steps.map((s, idx) => (
              <div
                key={s.cv_id}
                className={`p-4 rounded-xl border ${s.error ? 'border-red-300 dark:border-red-700' : 'border-slate-200 dark:border-slate-700'}`}
              >
                <p className="font-medium text-slate-900 dark:text-white mb-3 flex items-center gap-2">
                  <FileText className="w-4 h-4" />
                  {s.filename ?? `CV ${s.cv_index ?? idx + 1}`} — {s.cv_id.slice(0, 8)}...
                </p>
                {s.error && (
                  <p className="text-red-600 dark:text-red-400 text-sm mb-2">{s.error}</p>
                )}
                <div className="flex flex-wrap gap-3">
                  {s.steps.map((st, i) => (
                    <span
                      key={i}
                      className={`px-3 py-1 rounded-full text-sm ${
                        st.status === 'completed'
                          ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                          : st.status === 'failed'
                          ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                          : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300'
                      }`}
                    >
                      {st.name}
                      {st.note && ` (${st.note})`}
                      {st.dim && ` [${st.dim}d]`}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {loadMut.isError && (
          <div className="mt-6 p-4 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400">
            Error: {String((loadMut.error as Error).message)}
          </div>
        )}
      </div>

      <div className="bg-slate-100 dark:bg-slate-900 rounded-xl p-6 text-sm text-slate-600 dark:text-slate-400">
        <h3 className="font-semibold text-slate-900 dark:text-white mb-2">Sample resumes (10 PDFs)</h3>
        <ul className="list-disc list-inside space-y-1">
          <li>01. John Doe — Senior Full Stack Developer</li>
          <li>02. Marie Dupont — Java Engineer</li>
          <li>03. Sarah Chen — Data Scientist</li>
          <li>04. Michael Johnson — DevOps Engineer</li>
          <li>05. Emma Wilson — Frontend Developer</li>
          <li>06. David Park — Backend Engineer</li>
          <li>07. Lisa Martinez — UX Designer</li>
          <li>08. James Wright — Security Engineer</li>
          <li>09. Olivia Brown — Junior Developer</li>
          <li>10. Ahmed Hassan — Full Stack Developer</li>
        </ul>
        <p className="mt-4">
          Run the script <code className="bg-slate-200 dark:bg-slate-700 px-1 rounded">python scripts/generate_resume_pdfs.py</code> if PDFs are missing.
        </p>
      </div>
    </div>
  )
}
