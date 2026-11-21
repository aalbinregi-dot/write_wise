import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { teacher as teacherApi } from '../api/services';
import { useNavigate } from 'react-router-dom';

const TeacherDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [analytics, setAnalytics] = useState<any>(null);
  const [students, setStudents]   = useState<any[]>([]);
  const [loading, setLoading]     = useState(true);


  useEffect(() => {
    Promise.all([
      teacherApi.classAnalytics().then(r => setAnalytics(r.data)),
      teacherApi.students().then(r => setStudents(r.data.results || r.data)),
    ]).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center" style={{height:'40vh'}}><div className="spinner" style={{width:48,height:48}} /></div>;

  const stats = analytics?.stats || {};
  const distribution = analytics?.score_distribution || [];

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">Teacher Dashboard</h1>
        <p className="page-subtitle">Class overview and student analytics</p>
      </div>

      {/* Class Stats */}
      <div className="grid-4 mb-6">
        {[
          { label: 'Students',     value: analytics?.student_count || 0,     color: 'var(--brand-blue)' },
          { label: 'Total Essays', value: stats.total_essays || 0,           color: 'var(--brand-indigo)' },
          { label: 'Class Avg',    value: stats.avg_score?.toFixed(2) || '—', color: 'var(--brand-green)' },
          { label: 'Score Range',  value: `${stats.min_score?.toFixed(1) || '—'}–${stats.max_score?.toFixed(1) || '—'}`, color: 'var(--brand-amber)' },
        ].map(s => (
          <div key={s.label} className="stat-card">
            <span className="stat-label">{s.label}</span>
            <span className="stat-value" style={{ color: s.color }}>{s.value}</span>
          </div>
        ))}
      </div>

      <div className="grid-2 mb-6">
        {/* Score Distribution */}
        <div className="card">
          <h3 className="font-bold mb-4" style={{ color: 'var(--text-primary)' }}>Score Distribution</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={distribution}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.1)" />
              <XAxis dataKey="range" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
              <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
              <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8 }} />
              <Bar dataKey="count" fill="#6366F1" radius={[4,4,0,0]} name="Essays" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Students needing attention */}
        <div className="card">
          <h3 className="font-bold mb-4" style={{ color: 'var(--text-primary)' }}>Students</h3>
          <div style={{ maxHeight: 250, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {students.length === 0 ? (
              <p className="text-sm text-muted">No students registered yet.</p>
            ) : (
              students.map((s: any) => (
                <div key={s.id} className="flex items-center justify-between" style={{ padding: '0.6rem 0.75rem', background: 'var(--bg-secondary)', borderRadius: 8 }}>
                  <div>
                    <p className="font-bold text-sm">{s.first_name} {s.last_name}</p>
                    <p className="text-xs text-muted">{s.email}</p>
                  </div>
                  <button id={`view-student-${s.id}`} className="btn btn-ghost btn-sm"
                    onClick={() => navigate(`/students/${s.id}`)}>
                    View →
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="alert alert-info">
        <div>
          <strong>Teacher Override</strong>
          <p className="text-sm mt-1">
            To override an AI score, navigate to a student's essay results page and use the Override Score button.
            Teacher scores always take precedence over AI predictions.
          </p>
        </div>
      </div>
    </div>
  );
};

export default TeacherDashboard;
