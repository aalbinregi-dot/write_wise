import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../store/AuthContext';

const RegisterPage: React.FC = () => {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    username: '', email: '', password: '', password2: '',
    first_name: '', last_name: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handle = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.password !== form.password2) { setError('Passwords do not match.'); return; }
    setError(''); setLoading(true);
    try {
      await register(form);
      navigate('/dashboard');
    } catch (err: any) {
      const data = err?.response?.data;
      setError(data ? JSON.stringify(data).replace(/[{}"]/g, '') : 'Registration failed.');
    } finally { setLoading(false); }
  };

  const set = (field: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm(f => ({ ...f, [field]: e.target.value }));

  return (
    <div className="auth-layout">
      <div className="auth-card fade-in" style={{ maxWidth: 520 }}>
        <div className="auth-logo">
          <h1>WriteWise AI</h1>
          <p className="text-secondary text-sm mt-2">Create your account</p>
        </div>

        {error && <div className="alert alert-error mb-4">{error}</div>}

        <form onSubmit={handle} style={{ display: 'grid', gap: '0.875rem' }}>
          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">First Name</label>
              <input id="first_name" type="text" className="form-input" required
                placeholder="Albin" value={form.first_name} onChange={set('first_name')} />
            </div>
            <div className="form-group">
              <label className="form-label">Last Name</label>
              <input id="last_name" type="text" className="form-input" required
                placeholder="Regi" value={form.last_name} onChange={set('last_name')} />
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Username</label>
            <input id="username" type="text" className="form-input" required
              placeholder="albinregi" value={form.username} onChange={set('username')} />
          </div>
          <div className="form-group">
            <label className="form-label">Email Address</label>
            <input id="email" type="email" className="form-input" required
              placeholder="you@example.com" value={form.email} onChange={set('email')} />
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">Password</label>
              <input id="password" type="password" className="form-input" required
                placeholder="••••••••" value={form.password} onChange={set('password')} />
            </div>
            <div className="form-group">
              <label className="form-label">Confirm Password</label>
              <input id="password2" type="password" className="form-input" required
                placeholder="••••••••" value={form.password2} onChange={set('password2')} />
            </div>
          </div>
          <button id="register-btn" type="submit" className="btn btn-primary btn-lg w-full mt-2" disabled={loading}>
            {loading ? <><span className="spinner" style={{width:18,height:18}} /> Creating account…</> : 'Create Account'}
          </button>
        </form>
        <p className="text-sm text-secondary text-center mt-4">
          Already have an account? <Link to="/login" style={{ color: 'var(--brand-blue)' }}>Sign in</Link>
        </p>
      </div>
    </div>
  );
};

export default RegisterPage;
