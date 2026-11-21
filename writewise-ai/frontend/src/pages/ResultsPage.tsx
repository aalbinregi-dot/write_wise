import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { essays as essayApi } from '../api/services';

const ResultsPage: React.FC = () => {
  const { id }     = useParams<{ id: string }>();
  const navigate   = useNavigate();
  const [result, setResult]   = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState('');
  const [activeTab, setActiveTab] = useState<'overview'|'errors'|'advice'|'lessons'>('overview');

  useEffect(() => {
    if (!id) return;
    essayApi.results(id)
      .then(r => setResult(r.data))
      .catch(err => {
        if (err?.response?.status === 404) {
          essayApi.analyze(id)
            .then(() => essayApi.results(id).then(r => setResult(r.data)).catch(() => setError('Results not found.')))
            .catch(() => setError('Analysis failed or results not found.'));
        } else {
          setError('Failed to load results.');
        }
      })
      .finally(() => setLoading(false));
  }, [id]);

  const downloadPDF = async () => {
    try {
      const res = await essayApi.report(id!);
      const url = URL.createObjectURL(new Blob([res.data]));
      const a   = document.createElement('a');
      a.href = url; a.download = `writewise_report_${id}.pdf`; a.click();
    } catch { alert('PDF generation failed.'); }
  };

  if (loading) return (
    <div className="flex items-center justify-center" style={{ height: '60vh' }}>
      <div className="spinner" style={{ width: 48, height: 48 }} />
    </div>
  );
  if (error) return <div className="alert alert-error">{error}</div>;
  if (!result) return null;

  const score      = result.final_score || result.predicted_score || 0;
  const scoreColor = score >= 5 ? '#10B981' : score >= 4 ? '#3B82F6' : score >= 3 ? '#F59E0B' : '#F43F5E';

  const grammarErrors  = result.grammar_errors || [];
  const spellingErrors = result.spelling_errors || [];
  const totalErrors    = (result.grammar_error_count || 0) + (result.spelling_error_count || 0);

  return (
    <div className="fade-in" style={{ maxWidth: 960, margin: '0 auto' }}>
      {/* Top action header */}
      <div className="flex items-center justify-between mb-6">
        <button className="btn btn-ghost btn-sm" onClick={() => navigate('/essays')}>
          ← Back to Essays
        </button>
        <div className="flex gap-2">
          <button id="download-pdf-btn" className="btn btn-secondary" onClick={downloadPDF}>📄 Download PDF Report</button>
          <button className="btn btn-primary" onClick={() => navigate('/analyze')}>✍ Grade Another Essay</button>
        </div>
      </div>

      {/* Hero Score Banner */}
      <div className="card mb-6" style={{
        background: 'linear-gradient(135deg, rgba(22, 29, 47, 0.9), rgba(17, 24, 39, 0.9))',
        border: `1px solid ${scoreColor}40`,
        padding: '2rem',
      }}>
        <div className="flex items-center gap-6" style={{ flexWrap: 'wrap' }}>
          {/* Score Badge */}
          <div style={{
            width: 120, height: 120, borderRadius: '50%',
            background: `conic-gradient(${scoreColor} ${((score - 1) / 5) * 100}%, var(--bg-secondary) 0%)`,
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
          }}>
            <div style={{
              width: 100, height: 100, borderRadius: '50%', background: 'var(--bg-card)',
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
            }}>
              <span style={{ fontSize: '2.2rem', fontWeight: 900, color: 'var(--text-primary)', lineHeight: 1 }}>{score.toFixed(1)}</span>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>out of 6.0</span>
            </div>
          </div>

          <div style={{ flex: 1 }}>
            <span className="badge badge-low" style={{ background: `${scoreColor}20`, color: scoreColor, borderColor: `${scoreColor}40`, marginBottom: '0.5rem' }}>
              Grade: {score >= 5 ? 'Excellent' : score >= 4 ? 'Good' : score >= 3 ? 'Satisfactory' : 'Developing'}
            </span>
            <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-primary)', marginTop: '0.25rem' }}>
              Essay Evaluation Complete
            </h1>
            <p className="text-secondary text-sm mt-1">
              Word Count: <strong>{result.word_count || 0}</strong> • Total Errors Found: <strong style={{ color: totalErrors > 0 ? 'var(--brand-amber)' : 'var(--brand-green)' }}>{totalErrors}</strong>
            </p>
          </div>
        </div>
      </div>

      {/* 4 Clean Navigation Tabs */}
      <div className="flex gap-2 mb-6" style={{ borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
        {[
          { id: 'overview', label: '📊 Summary' },
          { id: 'errors',   label: `✏️ Grammar & Spelling (${totalErrors})` },
          { id: 'advice',   label: '💡 How to Improve' },
          { id: 'lessons',  label: '📚 Recommended Lessons' },
        ].map(tab => (
          <button key={tab.id} id={`tab-${tab.id}`}
            className={`btn btn-sm ${activeTab === tab.id ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setActiveTab(tab.id as any)}>
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB 1: OVERVIEW */}
      {activeTab === 'overview' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Key Problems Box */}
          <div className="card">
            <h3 className="font-bold text-lg mb-4" style={{ color: 'var(--text-primary)' }}>Key Writing Feedback</h3>
            {(result.problems || []).length === 0 ? (
              <div className="alert alert-success">✓ Great job! No critical issues were detected in your essay.</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {(result.problems as any[]).map((p, i) => (
                  <div key={i} style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: 10, borderLeft: `4px solid ${p.priority === 'HIGH' ? 'var(--brand-rose)' : 'var(--brand-amber)'}` }}>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`badge ${p.priority === 'HIGH' ? 'badge-high' : 'badge-medium'}`}>{p.priority}</span>
                      <span className="font-bold text-sm" style={{ color: 'var(--text-primary)' }}>{p.title}</span>
                    </div>
                    <p className="text-sm text-secondary">{p.description}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Quick Metrics */}
          <div className="grid-3">
            <div className="card" style={{ textAlign: 'center' }}>
              <span className="text-xs text-muted" style={{ textTransform: 'uppercase' }}>Readability</span>
              <div className="font-bold text-xl mt-1" style={{ color: 'var(--brand-blue)' }}>{result.readability_grade || 'Standard'}</div>
              <span className="text-xs text-muted">Ease Score: {result.readability_score || 0}</span>
            </div>
            <div className="card" style={{ textAlign: 'center' }}>
              <span className="text-xs text-muted" style={{ textTransform: 'uppercase' }}>Vocabulary Diversity</span>
              <div className="font-bold text-xl mt-1" style={{ color: 'var(--brand-green)' }}>{((result.vocab_diversity || 0) * 100).toFixed(0)}%</div>
              <span className="text-xs text-muted">Unique word ratio</span>
            </div>
            <div className="card" style={{ textAlign: 'center' }}>
              <span className="text-xs text-muted" style={{ textTransform: 'uppercase' }}>Structure Quality</span>
              <div className="font-bold text-xl mt-1" style={{ color: 'var(--brand-indigo)' }}>{result.writing_analysis?.structure_quality || 'Good'}</div>
              <span className="text-xs text-muted">Paragraph organization</span>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: ERRORS & CORRECTIONS */}
      {activeTab === 'errors' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Grammar Errors */}
          <div className="card">
            <h3 className="font-bold text-lg mb-3" style={{ color: 'var(--text-primary)' }}>Grammar Errors</h3>
            {grammarErrors.length === 0 ? (
              <p className="text-sm text-muted">✓ No grammar errors detected.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
                {grammarErrors.map((err: any, idx: number) => (
                  <div key={idx} style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: 10 }}>
                    <span className="badge badge-high mb-2">{err.error_type}</span>
                    <p className="text-sm"><strong>Original:</strong> <span style={{ color: 'var(--brand-rose)' }}>{err.original}</span></p>
                    {err.correction && <p className="text-sm mt-1"><strong>Correction:</strong> <span style={{ color: 'var(--brand-green)' }}>{err.correction}</span></p>}
                    <p className="text-xs text-muted mt-1">{err.explanation}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Spelling Errors */}
          <div className="card">
            <h3 className="font-bold text-lg mb-3" style={{ color: 'var(--text-primary)' }}>Spelling Mistakes</h3>
            {spellingErrors.length === 0 ? (
              <p className="text-sm text-muted">✓ No spelling mistakes detected.</p>
            ) : (
              <div className="grid-2">
                {spellingErrors.map((err: any, idx: number) => (
                  <div key={idx} style={{ padding: '0.75rem 1rem', background: 'var(--bg-secondary)', borderRadius: 8 }} className="flex items-center justify-between">
                    <span className="font-mono text-rose text-sm">{err.misspelling}</span>
                    <span className="text-sm">→</span>
                    <span className="font-mono text-green text-sm font-bold">{err.correction}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 3: ADVICE */}
      {activeTab === 'advice' && (
        <div className="card">
          <h3 className="font-bold text-lg mb-4" style={{ color: 'var(--text-primary)' }}>Writing Improvement Plan</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {(result.feedback?.advice || []).map((item: any, idx: number) => (
              <div key={idx} style={{ padding: '1.25rem', background: 'rgba(59,130,246,0.06)', borderRadius: 10, borderLeft: '4px solid var(--brand-blue)' }}>
                <h4 className="font-bold text-sm mb-1" style={{ color: 'var(--brand-blue)' }}>{item.area}</h4>
                <p className="text-sm text-secondary" style={{ lineHeight: 1.6 }}>{item.advice}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 4: LESSONS */}
      {activeTab === 'lessons' && (
        <div className="card">
          <h3 className="font-bold text-lg mb-4" style={{ color: 'var(--text-primary)' }}>Recommended CEFR Lessons</h3>
          {(result.recommendations || []).length === 0 ? (
            <p className="text-sm text-muted">No specific lessons needed based on this essay.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
              {(result.recommendations as any[]).map((rec: any, idx: number) => (
                <div key={idx} className="card-glass" style={{ padding: '1rem' }}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="badge badge-medium">{rec.category}</span>
                    <span className="text-xs text-muted">⏱ {rec.time_to_learn || 1} hr</span>
                  </div>
                  <h4 className="font-bold text-sm" style={{ color: 'var(--text-primary)' }}>{rec.lesson}</h4>
                  <p className="text-xs text-muted mt-1">{rec.reason}</p>
                  <button className="btn btn-secondary btn-sm mt-3" onClick={() => navigate('/learning')}>
                    Start Lesson →
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ResultsPage;
