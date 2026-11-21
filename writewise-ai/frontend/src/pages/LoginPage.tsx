import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../store/AuthContext';

const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate  = useNavigate();
  const [form, setForm]   = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (email: string, pass: string) => {
    setError(''); setLoading(true);
    try {
      await login(email, pass);
      navigate('/analyze');
    } catch {
      setError('Invalid email or password. Please try again.');
    } finally { setLoading(false); }
  };

  const handleDemoUser = () => handleLogin('student@writewise.ai', 'Test1234!');

  const handle = (e: React.FormEvent) => {
    e.preventDefault();
    handleLogin(form.email, form.password);
  };

  return (
    <div className="auth-layout">
      <div className="auth-card fade-in">
        <div className="auth-logo">
          <h1>WriteWise AI</h1>
          <p className="text-secondary text-sm mt-2">AI-Powered Writing Coach & Feedback</p>
        </div>

        {error && <div className="alert alert-error mb-4">{error}</div>}

        {/* Instant Demo Access Buttons */}
        <div style={{ background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.3)', borderRadius: 12, padding: '1.25rem', marginBottom: '1.5rem', textAlign: 'center' }}>
          <p className="font-bold text-sm mb-2" style={{ color: 'var(--brand-blue)' }}>🚀 One-Click Instant Access</p>
          <p className="text-xs text-muted mb-3">No login required — test the app immediately:</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <button id="instant-user-btn" className="btn btn-primary w-full" onClick={handleDemoUser} disabled={loading}>
              ⚡ Try it now — No account needed
            </button>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', margin: '1rem 0', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
          <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
          <span style={{ padding: '0 0.75rem' }}>OR SIGN IN WITH EMAIL</span>
          <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
        </div>

        <form onSubmit={handle} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="form-group">
            <label className="form-label">Email Address</label>
            <input id="email" type="email" className="form-input" required
              placeholder="you@example.com"
              value={form.email}
              onChange={e => setForm(f => ({ ...f, email: e.target.value }))} />
          </div>
          <div className="form-group">
            <label className="form-label">Password</label>
            <input id="password" type="password" className="form-input" required
              placeholder="••••••••"
              value={form.password}
              onChange={e => setForm(f => ({ ...f, password: e.target.value }))} />
          </div>
          <button id="login-btn" type="submit" className="btn btn-ghost btn-lg w-full" disabled={loading}>
            {loading ? <><span className="spinner" style={{width:18,height:18}} /> Signing in…</> : 'Sign In'}
          </button>
        </form>

        <p className="text-sm text-secondary text-center mt-4">
          Don't have an account? <Link to="/register" style={{ color: 'var(--brand-blue)' }}>Register</Link>
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
