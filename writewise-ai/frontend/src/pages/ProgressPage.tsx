import React, { useEffect, useState } from 'react';
import { useAuth } from '../store/AuthContext';
import { students } from '../api/services';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

import { format } from 'date-fns';

const ProgressPage: React.FC = () => {
  const { user } = useAuth();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    students.myAnalytics()
      .then(r => setData(r.data))
      .finally(() => setLoading(false));
  }, [user]);

  if (loading) return <div className="flex items-center justify-center" style={{height:'40vh'}}><div className="spinner" style={{width:48,height:48}} /></div>;

  const history = data?.history || [];
  const comparison = data?.comparison;

  const chartData = history.map((h: any) => ({
    date:    h.essay__submitted_at ? format(new Date(h.essay__submitted_at), 'MMM d') : '',
    score:   parseFloat((h.final_score || 0).toFixed(2)),
    grammar: h.grammar_error_count || 0,
    spelling:h.spelling_error_count || 0,
    vocab:   parseFloat(((h.vocab_diversity || 0) * 100).toFixed(1)),
    words:   h.word_count || 0,
  }));

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">Writing Progress</h1>
        <p className="page-subtitle">Track your improvement across all submitted essays</p>
      </div>

      {history.length < 2 ? (
        <div className="alert alert-info mb-6">
          Submit at least 2 essays to see progress charts and before vs after comparisons.
        </div>
      ) : null}

      {/* Progress Charts */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        <div className="card">
          <h3 className="font-bold mb-4" style={{ color: 'var(--text-primary)' }}>Score Over Time</h3>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.1)" />
              <XAxis dataKey="date" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
              <YAxis domain={[1, 6]} tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
              <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8 }} />
              <Line type="monotone" dataKey="score" stroke="#3B82F6" strokeWidth={3}
                    dot={{ fill: '#3B82F6', r: 5 }} name="Score (1–6)" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="grid-2">
          <div className="card">
            <h3 className="font-bold mb-4" style={{ color: 'var(--text-primary)' }}>Error Reduction</h3>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.1)" />
                <XAxis dataKey="date" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8 }} />
                <Legend />
                <Line type="monotone" dataKey="grammar"  stroke="#F43F5E" strokeWidth={2} name="Grammar Errors" />
                <Line type="monotone" dataKey="spelling" stroke="#F59E0B" strokeWidth={2} name="Spelling Errors" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="card">
            <h3 className="font-bold mb-4" style={{ color: 'var(--text-primary)' }}>Vocabulary Diversity (%)</h3>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.1)" />
                <XAxis dataKey="date" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8 }} />
                <Line type="monotone" dataKey="vocab" stroke="#10B981" strokeWidth={2} name="Vocab Diversity %" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Before vs After */}
        {comparison && (
          <div className="card">
            <h3 className="font-bold mb-4" style={{ color: 'var(--text-primary)' }}>Before vs After Comparison</h3>
            <div className="grid-2">
              {['first_essay', 'latest_essay'].map((key, idx) => {
                const essay = comparison[key];
                return (
                  <div key={key} style={{ padding: '1.5rem', background: 'var(--bg-secondary)', borderRadius: 12, border: '1px solid var(--border)' }}>
                    <h4 className="font-bold mb-3" style={{ color: idx === 0 ? 'var(--text-muted)' : 'var(--brand-blue)' }}>
                      {idx === 0 ? '📝 First Essay' : '🎯 Latest Essay'}
                    </h4>
                    {[
                      { label: 'Score',           value: essay.score?.toFixed(1) || '—', unit: '/ 6' },
                      { label: 'Grammar Errors',  value: essay.grammar_errors ?? '—' },
                      { label: 'Spelling Errors', value: essay.spelling_errors ?? '—' },
                      { label: 'Word Count',      value: essay.word_count || '—' },
                      { label: 'Vocab Diversity', value: essay.vocab_diversity ? ((essay.vocab_diversity * 100).toFixed(0) + '%') : '—' },
                    ].map(row => (
                      <div key={row.label} className="flex items-center justify-between mb-2" style={{ borderBottom: '1px solid var(--border)', paddingBottom: '0.4rem' }}>
                        <span className="text-sm text-secondary">{row.label}</span>
                        <span className="font-bold text-sm">{row.value} {row.unit || ''}</span>
                      </div>
                    ))}
                  </div>
                );
              })}
            </div>
            <div className="grid-4 mt-4" style={{ gap: '0.75rem' }}>
              {Object.entries(comparison.improvements || {}).map(([key, val]: [string, any]) => (
                <div key={key} style={{ background: 'var(--bg-card)', borderRadius: 10, padding: '0.75rem', textAlign: 'center' }}>
                  <div className="text-xs text-muted mb-1" style={{ textTransform: 'capitalize' }}>{key}</div>
                  <div className={`font-bold ${val?.includes('+') || val?.includes('↑') ? 'text-green' : 'text-rose'}`}>{val}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProgressPage;
