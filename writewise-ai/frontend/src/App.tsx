import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, NavLink } from 'react-router-dom';
import { useAuth, AuthProvider } from './store/AuthContext';

import LoginPage      from './pages/LoginPage';
import RegisterPage   from './pages/RegisterPage';
import DashboardPage  from './pages/DashboardPage';
import AnalyzePage    from './pages/AnalyzePage';
import EssaysPage     from './pages/EssaysPage';
import ResultsPage    from './pages/ResultsPage';
import ProgressPage   from './pages/ProgressPage';
import LearningPage   from './pages/LearningPage';
import PlagiarismPage from './pages/PlagiarismPage';
import HumanizerPage  from './pages/HumanizerPage';

// ── Icons (inline SVG to avoid extra deps) ─────────────────────────────────
const icons: Record<string, React.ReactNode> = {

  dashboard: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>,
  write:     <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>,
  essays:    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>,
  progress:  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>,
  learning:  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>,
  teacher:   <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>,
  logout:    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>,
  plagiarism:<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg>,
  humanizer: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>,
};

const Sidebar: React.FC = () => {
  const { user, logout } = useAuth();
  const initials = `${user?.first_name?.[0] || ''}${user?.last_name?.[0] || user?.username?.[0] || '?'}`.toUpperCase();

  const nav = [
    { to: '/dashboard',  icon: 'dashboard',  label: 'Dashboard' },
    { to: '/analyze',    icon: 'write',      label: 'Analyze Writing' },
    { to: '/essays',     icon: 'essays',     label: 'My Writing' },
    { to: '/progress',   icon: 'progress',   label: 'Progress' },
    { to: '/learning',   icon: 'learning',   label: 'Learning Plan' },
    { to: '/plagiarism', icon: 'plagiarism', label: 'Plagiarism Check' },
    { to: '/humanize',   icon: 'humanizer',  label: 'AI Humanizer' },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <h1>WriteWise AI</h1>
        <span>Write. Understand. Grow.</span>
      </div>

      <nav className="sidebar-nav">
        <span className="nav-section-label">Navigation</span>
        {nav.map(item => (
          <NavLink key={item.to} to={item.to}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            id={`nav-${item.label.toLowerCase().replace(/ /g, '-')}`}>
            {icons[item.icon]}
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-user">
        <div className="user-avatar">{initials}</div>
        <div className="user-info">
          <div className="user-name">{user?.first_name} {user?.last_name}</div>
          <div className="user-role">Member</div>
        </div>
      </div>
      
      <button 
        id="logout-btn" 
        onClick={logout} 
        className="nav-item" 
        style={{ marginTop: 'auto', background: 'none', border: 'none', width: '100%', textAlign: 'left', cursor: 'pointer', color: 'var(--danger-color, #ff4d4f)' }}
      >
        {icons.logout}
        Logout
      </button>
    </aside>
  );
};

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <div className="flex items-center justify-center" style={{height:'100vh'}}><div className="spinner" style={{width:48,height:48}}/></div>;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
};

const AppShell: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="app-shell">
    <Sidebar />
    <main className="main-content">{children}</main>
  </div>
);

const App: React.FC = () => (
  <AuthProvider>
    <BrowserRouter>
      <Routes>
        <Route path="/login"    element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/" element={<Navigate to="/analyze" replace />} />


        <Route path="/dashboard" element={
          <ProtectedRoute>
            <AppShell>
              <DashboardPage />
            </AppShell>
          </ProtectedRoute>
        } />
        <Route path="/analyze" element={
          <ProtectedRoute>
            <AppShell><AnalyzePage /></AppShell>
          </ProtectedRoute>
        } />
        <Route path="/essays" element={
          <ProtectedRoute>
            <AppShell><EssaysPage /></AppShell>
          </ProtectedRoute>
        } />
        <Route path="/essays/:id/results" element={
          <ProtectedRoute>
            <AppShell><ResultsPage /></AppShell>
          </ProtectedRoute>
        } />
        <Route path="/progress" element={
          <ProtectedRoute>
            <AppShell><ProgressPage /></AppShell>
          </ProtectedRoute>
        } />
        <Route path="/learning" element={
          <ProtectedRoute>
            <AppShell><LearningPage /></AppShell>
          </ProtectedRoute>
        } />
        <Route path="/plagiarism" element={
          <ProtectedRoute>
            <AppShell><PlagiarismPage /></AppShell>
          </ProtectedRoute>
        } />
        <Route path="/humanize" element={
          <ProtectedRoute>
            <AppShell><HumanizerPage /></AppShell>
          </ProtectedRoute>
        } />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  </AuthProvider>
);

export default App;
