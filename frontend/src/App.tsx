import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Layout } from '@/components/layout/Layout'
import { Dashboard } from '@/pages/Dashboard'
import { CVList } from '@/pages/CVList'
import { CVViewer } from '@/pages/CVViewer'
import { Matching } from '@/pages/Matching'
import { Demo } from '@/pages/Demo'

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/cvs" element={<CVList />} />
          <Route path="/cvs/:cvId" element={<CVViewer />} />
          <Route path="/matching" element={<Matching />} />
          <Route path="/demo" element={<Demo />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}
