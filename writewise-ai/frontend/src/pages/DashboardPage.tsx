import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../store/AuthContext';
import { students, essays as essayApi } from '../api/services';
import { format } from 'date-fns';

const DashboardPage: React.FC = () => {
  const { user }     = useAuth();
  const navigate     = useNavigate();
  const [progress, setProgress]   = useState<any>(null);
  const [essayList, setEssayList] = useState<any[]>([]);
  const [recs, setRecs]           = useState<any[]>([]);
  const [loading, setLoading]     = useState(true);

  useEffect(() => {
    if (!user) return;
    Promise.all([
      students.progress(user.id).then(r => setProgress(r.data)).catch(() => {}),
      essayApi.list().then(r => setEssayList(r.data.results || r.data)).catch(() => {}),
      students.recommendations(user.id).then(r => setRecs(r.data.recommendations || [])).catch(() => {}),
    ]).finally(() => setLoading(false));
  }, [user]);

  const summary     = progress?.summary || {};
  const displayName = user?.first_name || user?.username || 'Student';

  if (loading) return (
    <div className="flex items-center justify-center" style={{ height: '60vh' }}>
      <div className="spinner" style={{ width: 48, height: 48 }} />
    </div>
  );

  return (
    <div className="fade-in" style={{ maxWidth: 1000, margin: '0 auto' }}>
      {/* Welcome Banner */}
      <div className="card mb-6" style={{
        background: 'linear-gradient(135deg, rgba(59,130,246,0.15), rgba(99,102,241,0.15))',
        border: '1px solid rgba(99,102,241,0.3)',
        padding: '2rem',
      }}>
        <div className="flex items-center justify-between" style={{ flexWrap: 'wrap', gap: '1.5rem' }}>
          <div>
            <h1 className="page-title" style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>
              Welcome back, {displayName}! 👋
            </h1>
            <p className="text-secondary" style={{ fontSize: '1rem' }}>
              WriteWise AI analyzes your essays, explains errors, and helps you improve your writing grade.
            </p>
          </div>
          <button id="main-analyze-btn" className="btn btn-primary btn-lg" onClick={() => navigate('/analyze')} style={{ boxShadow: '0 8px 25px rgba(59,130,246,0.4)' }}>
            ✍ Grade an Essay Now →
          </button>
        </div>
      </div>

      {/* 3 Simple Stat Cards */}
      <div className="grid-3 mb-6">
        <div className="stat-card" style={{ padding: '1.5rem' }}>
          <span className="stat-label">Latest Writing Score</span>
          <span className="stat-value" style={{ color: 'var(--brand-blue)', fontSize: '2.5rem' }}>
            {summary.latest_score ? `${summary.latest_score.toFixed(1)} / 6` : '—'}
          </span>
          <span className="text-xs text-muted">
            {summary.score_change != null ? `${summary.score_change >= 0 ? '▲ +' : '▼ '}${summary.score_change.toFixed(2)} overall change` : 'No essays evaluated yet'}
          </span>
        </div>

        <div className="stat-card" style={{ padding: '1.5rem' }}>
          <span className="stat-label">Total Essays Graded</span>
          <span className="stat-value" style={{ fontSize: '2.5rem' }}>
            {summary.total_essays ?? essayList.length}
          </span>
          <span className="text-xs text-muted">Submissions tracked</span>
        </div>

        <div className="stat-card" style={{ padding: '1.5rem' }}>
          <span className="stat-label">Personal Best</span>
          <span className="stat-value" style={{ color: 'var(--brand-green)', fontSize: '2.5rem' }}>
            {summary.best_score ? `${summary.best_score.toFixed(1)} / 6` : '—'}
          </span>
          <span className="text-xs text-muted">Highest score achieved</span>
        </div>
      </div>

      {/* 2 Main Columns */}
      <div className="grid-2 mb-6" style={{ gridTemplateColumns: '1.2fr 0.8fr' }}>
        {/* Recent Essays */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-lg" style={{ color: 'var(--text-primary)' }}>Recent Essays</h3>
            {essayList.length > 0 && (
              <button className="btn btn-ghost btn-sm" onClick={() => navigate('/essays')}>View All</button>
            )}
          </div>

          {essayList.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {essayList.slice(0, 4).map((essay: any) => (
                <div key={essay.id} className="card-glass flex items-center justify-between" style={{ padding: '1rem' }}>
                  <div>
                    <h4 className="font-bold text-sm" style={{ color: 'var(--text-primary)' }}>
                      {essay.title || 'Untitled Essay'}
                    </h4>
                    <span className="text-xs text-muted">
                      {essay.submitted_at ? format(new Date(essay.submitted_at), 'MMM d, yyyy') : ''}
                    </span>
                  </div>
                  <button className="btn btn-secondary btn-sm" onClick={() => navigate(`/essays/${essay.id}/results`)}>
                    View Assessment →
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '2rem 1rem' }}>
              <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>📝</div>
              <p className="text-secondary text-sm mb-4">You haven't submitted any essays yet.</p>
              <button className="btn btn-primary" onClick={() => navigate('/analyze')}>Analyze Your First Essay</button>
            </div>
          )}
        </div>

        {/* Recommended Lessons */}
        <div className="card">
          <h3 className="font-bold text-lg mb-4" style={{ color: 'var(--text-primary)' }}>Recommended Lessons</h3>
          {recs.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {recs.slice(0, 3).map((rec: any, idx: number) => (
                <div key={idx} style={{ padding: '0.875rem', background: 'var(--bg-secondary)', borderRadius: 10, borderLeft: '3px solid var(--brand-indigo)' }}>
                  <span className="badge badge-medium mb-1">{rec.category}</span>
                  <p className="font-bold text-sm" style={{ color: 'var(--text-primary)' }}>{rec.lesson}</p>
                  <button className="btn btn-ghost btn-sm mt-2" onClick={() => navigate('/learning')}>
                    Start Lesson →
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ padding: '1.5rem 1rem', textAlign: 'center' }}>
              <p className="text-secondary text-sm">
                Grade an essay to unlock personalized lesson recommendations.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
