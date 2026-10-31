import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import { useAuth } from './auth'
import Home from './pages/Home'
import DocumentPage from './pages/DocumentPage'
import Login from './pages/Login'
import Register from './pages/Register'
import Profile from './pages/Profile'
import NotFound from './pages/NotFound'
import AdminLayout from './pages/admin/AdminLayout'
import AdminDocuments from './pages/admin/AdminDocuments'
import DocumentEditor from './pages/admin/DocumentEditor'
import Taxonomy from './pages/admin/Taxonomy'
import Moderation from './pages/admin/Moderation'
import Reports from './pages/admin/Reports'
import SEO from './pages/admin/SEO'
import Analytics from './pages/admin/Analytics'
import SearchLogs from './pages/admin/SearchLogs'
import Users from './pages/admin/Users'
import Roles from './pages/admin/Roles'
import Settings from './pages/admin/Settings'
import SystemLogs from './pages/admin/SystemLogs'
import AdminHome from './pages/admin/AdminHome'

function RequireAuth({ children }) {
  const { user, ready } = useAuth()
  if (!ready) return <p className="muted pad">Loading…</p>
  return user ? children : <Navigate to="/login" replace />
}

function RequirePerm({ perm, children }) {
  const { user, ready, can } = useAuth()
  if (!ready) return <p className="muted pad">Loading…</p>
  if (!user) return <Navigate to="/login" replace />
  const list = Array.isArray(perm) ? perm : [perm]
  return can(...list) ? children : (
    <div className="empty">
      <h2>You don't have access to this page</h2>
      <p>Ask a Super Admin to grant your role the <code>{list.join(' or ')}</code> permission.</p>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="documents/:ref" element={<DocumentPage />} />
        <Route path="login" element={<Login />} />
        <Route path="register" element={<Register />} />
        <Route path="profile" element={<RequireAuth><Profile /></RequireAuth>} />

        <Route path="admin" element={<RequireAuth><AdminLayout /></RequireAuth>}>
          <Route index element={<AdminHome />} />
          <Route path="documents" element={<RequirePerm perm="documents.read_all"><AdminDocuments /></RequirePerm>} />
          <Route path="documents/new" element={<RequirePerm perm="documents.create"><DocumentEditor /></RequirePerm>} />
          <Route path="documents/:id" element={<RequirePerm perm="documents.update"><DocumentEditor /></RequirePerm>} />
          <Route path="taxonomy" element={<RequirePerm perm="taxonomy.manage"><Taxonomy /></RequirePerm>} />
          <Route path="comments" element={<RequirePerm perm="comments.moderate"><Moderation /></RequirePerm>} />
          <Route path="reports" element={<RequirePerm perm={['reports.manage', 'spam.manage']}><Reports /></RequirePerm>} />
          <Route path="seo" element={<RequirePerm perm="seo.manage"><SEO /></RequirePerm>} />
          <Route path="analytics" element={<RequirePerm perm="analytics.view"><Analytics /></RequirePerm>} />
          <Route path="search-logs" element={<RequirePerm perm="analytics.view"><SearchLogs /></RequirePerm>} />
          <Route path="users" element={<RequirePerm perm="users.manage"><Users /></RequirePerm>} />
          <Route path="roles" element={<RequirePerm perm="roles.manage"><Roles /></RequirePerm>} />
          <Route path="settings" element={<RequirePerm perm="settings.manage"><Settings /></RequirePerm>} />
          <Route path="system-logs" element={<RequirePerm perm="logs.view"><SystemLogs /></RequirePerm>} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}
