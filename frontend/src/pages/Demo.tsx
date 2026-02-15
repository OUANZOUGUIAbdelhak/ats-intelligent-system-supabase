import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Rocket, CheckCircle, Loader2 } from 'lucide-react'
import { api } from '@/lib/api'

export function Demo() {
  const [steps, setSteps] = useState<Array<{
    cv_index: number
    cv_id: string
    steps: Array<{ name: string; status: string; note?: string; dim?: number }>
  }>>([])
  const queryClient = useQueryClient()

  const loadMut = useMutation({
    mutationFn: async () => {
      const r = await api.get('/api/demo/load')
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
          Load 4 example CVs (clean, scanned-style, messy, multilingual) and run the full pipeline
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
              Loading demo data...
            </>
          ) : (
            <>
              <Rocket className="w-6 h-6" />
              Load Demo Data
            </>
          )}
        </button>

        {loadMut.isSuccess && (
          <div className="mt-6 p-4 rounded-lg bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 flex items-center gap-3">
            <CheckCircle className="w-6 h-6" />
            <span>
              Loaded {loadMut.data?.total ?? 0} CVs. Pipeline: OCR → LLM → Embedding → Store
            </span>
          </div>
        )}

        {steps.length > 0 && (
          <div className="mt-8 space-y-6">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">Pipeline steps</h2>
            {steps.map((s) => (
              <div
                key={s.cv_id}
                className="p-4 rounded-xl border border-slate-200 dark:border-slate-700"
              >
                <p className="font-medium text-slate-900 dark:text-white mb-3">
                  CV {s.cv_index} — {s.cv_id.slice(0, 8)}...
                </p>
                <div className="flex flex-wrap gap-3">
                  {s.steps.map((st, i) => (
                    <span
                      key={i}
                      className={`px-3 py-1 rounded-full text-sm ${
                        st.status === 'completed'
                          ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
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
        <h3 className="font-semibold text-slate-900 dark:text-white mb-2">Demo CVs</h3>
        <ul className="list-disc list-inside space-y-1">
          <li>1. Clean structured CV (English)</li>
          <li>2. Scanned-style CV (French)</li>
          <li>3. Messy layout (minimal)</li>
          <li>4. Multilingual (EN/ES/FR)</li>
        </ul>
        <p className="mt-4">
          Each CV is processed: OCR text → Groq LLM structuring → 384-dim embedding → stored in Supabase.
        </p>
      </div>
    </div>
  )
}
