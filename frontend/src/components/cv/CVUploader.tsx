import { useState, useRef, useCallback } from 'react'
import { Upload, X, FileText, Loader2, CheckCircle, AlertCircle } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { api } from '@/lib/api'

interface CVUploaderProps {
  onUploadSuccess?: () => void
}

export function CVUploader({ onUploadSuccess }: CVUploaderProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle')
  const [message, setMessage] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = useCallback(
    async (file: File) => {
      const maxSize = 10 * 1024 * 1024
      const allowed = [
        'application/pdf',
        'image/jpeg',
        'image/png',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      ]
      if (!allowed.includes(file.type)) {
        setStatus('error')
        setMessage(`Unsupported type: ${file.type}`)
        return
      }
      if (file.size > maxSize) {
        setStatus('error')
        setMessage('File too large (max 10 MB)')
        return
      }

      setSelectedFile(file)
      setStatus('idle')
      setMessage('')
      setIsUploading(true)

      try {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('source', 'upload')
        formData.append('gdpr_consent', 'true')

        const r = await api.post('/api/cv/ingest', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 120000,
        })
        const { cv_id } = r.data

        setStatus('success')
        setMessage(`Uploaded! CV ID: ${cv_id}`)
        setIsUploading(false)
        onUploadSuccess?.()
        setTimeout(() => {
          setSelectedFile(null)
          setStatus('idle')
          setMessage('')
        }, 3000)
      } catch (err: unknown) {
        const e = err as { response?: { data?: { detail?: string } }; message?: string }
        setIsUploading(false)
        setStatus('error')
        setMessage(e.response?.data?.detail ?? e.message ?? 'Upload failed')
      }
    },
    [onUploadSuccess]
  )

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const files = e.dataTransfer.files
    if (files.length) handleFile(files[0]!)
  }

  return (
    <div className="space-y-4">
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
        onDragLeave={(e) => { e.preventDefault(); setIsDragging(false) }}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`
          relative bg-white dark:bg-slate-800 rounded-xl p-12 border-2 border-dashed text-center cursor-pointer transition-all
          ${isDragging ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20' : 'border-slate-300 dark:border-slate-600 hover:border-primary-400'}
          ${isUploading ? 'pointer-events-none opacity-75' : ''}
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.jpg,.jpeg,.png"
          className="hidden"
          disabled={isUploading}
          onChange={(e) => {
            const f = e.target.files?.[0]
            if (f) handleFile(f)
          }}
        />

        <AnimatePresence mode="wait">
          {isUploading ? (
            <motion.div key="uploading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-4">
              <Loader2 className="w-16 h-16 mx-auto text-primary-500 animate-spin" />
              <h3 className="text-xl font-semibold">Processing CV...</h3>
            </motion.div>
          ) : selectedFile ? (
            <motion.div key="selected" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-4">
              <FileText className="w-16 h-16 mx-auto text-primary-500" />
              <h3 className="text-xl font-semibold">{selectedFile.name}</h3>
              <p className="text-sm text-slate-500">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
            </motion.div>
          ) : (
            <motion.div key="default" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-4">
              <Upload className="w-16 h-16 mx-auto text-slate-400" />
              <h3 className="text-xl font-semibold">Upload CV</h3>
              <p className="text-slate-500">Drag & drop PDF, DOCX, or image, or click to select</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <AnimatePresence>
        {status !== 'idle' && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className={`p-4 rounded-lg flex items-center gap-3 ${
              status === 'success'
                ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400'
                : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400'
            }`}
          >
            {status === 'success' ? <CheckCircle className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
            <p className="text-sm font-medium">{message}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
