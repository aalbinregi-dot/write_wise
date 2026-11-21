import React, { useState } from 'react';
import { tools as toolsApi } from '../api/services';

const PlagiarismPage: React.FC = () => {
  const [text, setText] = useState('');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;

  const handleCheck = async () => {
    if (wordCount < 10) { setError('Please enter at least 10 words.'); return; }
    setError(''); setLoading(true); setResult(null);
    try {
      const res = await toolsApi.plagiarism(text);
      setResult(res.data);
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Check failed. Please try again.');
    } finally { setLoading(false); }
  };

  const scoreColor = result
    ? result.score >= 70 ? '#F43F5E'
      : result.score >= 40 ? '#F59E0B'
      : result.score >= 15 ? '#3B82F6'
      : '#10B981'
    : '#10B981';

  const circumference = 2 * Math.PI * 52;

  return (
    <div className="fade-in" style={{ maxWidth: 900, margin: '0 auto' }}>
      {/* Header */}
      <div className="page-header text-center mb-6">
        <h1 className="page-title" style={{ fontSize: '2.2rem' }}>🔍 Plagiarism Checker</h1>
        <p className="page-subtitle" style={{ fontSize: '1rem' }}>
          Detect similarity against common academic texts and reference sources.
        </p>
      </div>

      {error && <div className="alert alert-error mb-4">{error}</div>}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {/* Input Card */}
        <div className="card" style={{ padding: '2rem' }}>
          <div className="form-group mb-4">
            <div className="flex items-center justify-between mb-1">
              <label className="form-label" style={{ fontSize: '0.9rem' }}>Paste your text</label>
              <span className="text-xs text-muted">
                <span style={{ color: wordCount >= 10 ? 'var(--brand-green)' : 'var(--text-muted)', fontWeight: 700 }}>
                  {wordCount} words
                </span>
              </span>
            </div>
            <textarea
              id="plagiarism-text"
              className="form-textarea"
              placeholder="Paste the text you want to check for plagiarism..."
              style={{ minHeight: 220, fontSize: '0.95rem', lineHeight: 1.7 }}
              value={text}
              onChange={e => setText(e.target.value)}
            />
          </div>
          <button
            id="check-plagiarism-btn"
            className="btn btn-primary btn-lg w-full"
            onClick={handleCheck}
            disabled={loading || wordCount < 10}
          >
            {loading
              ? <><span className="spinner" style={{ width: 18, height: 18 }} /> Checking...</>
              : '🔍 Check for Plagiarism'}
          </button>
        </div>

        {/* Results */}
        {result && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }} className="fade-in">

            {/* Score Ring */}
            <div className="card" style={{
              background: 'linear-gradient(135deg, rgba(22,29,47,0.9), rgba(17,24,39,0.9))',
              border: `1px solid ${scoreColor}40`,
              padding: '2rem',
            }}>
              <div className="flex items-center gap-6" style={{ flexWrap: 'wrap' }}>
                {/* Ring */}
                <div style={{ flexShrink: 0 }}>
                  <svg width="130" height="130" viewBox="0 0 130 130">
                    <circle cx="65" cy="65" r="52" fill="none" stroke="var(--bg-secondary)" strokeWidth="10" />
                    <circle
                      cx="65" cy="65" r="52"
                      fill="none"
                      stroke={scoreColor}
                      strokeWidth="10"
                      strokeDasharray={circumference}
                      strokeDashoffset={circumference - (result.score / 100) * circumference}
                      strokeLinecap="round"
                      transform="rotate(-90 65 65)"
                      style={{ transition: 'stroke-dashoffset 1s ease' }}
                    />
                    <text x="65" y="60" textAnchor="middle" fill="var(--text-primary)" fontSize="26" fontWeight="900">
                      {result.score}%
                    </text>
                    <text x="65" y="78" textAnchor="middle" fill="var(--text-muted)" fontSize="11">
                      similarity
                    </text>
                  </svg>
                </div>

                <div style={{ flex: 1 }}>
                  <span className="badge" style={{
                    background: `${scoreColor}20`, color: scoreColor,
                    border: `1px solid ${scoreColor}40`, marginBottom: '0.5rem',
                    fontSize: '0.85rem', padding: '0.3rem 0.8rem',
                  }}>
                    {result.verdict}
                  </span>
                  <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)', marginTop: '0.5rem' }}>
                    Analysis Complete
                  </h2>
                  <p className="text-secondary text-sm mt-1">
                    <strong>{result.flagged_sentence_count}</strong> of <strong>{result.total_sentences}</strong> sentences flagged •{' '}
                    <strong>{result.matches?.length || 0}</strong> source{result.matches?.length !== 1 ? 's' : ''} matched
                  </p>
                </div>
              </div>
            </div>

            {/* Flagged Sentences */}
            {result.flagged_sentences?.length > 0 && (
              <div className="card">
                <h3 className="font-bold text-lg mb-4" style={{ color: 'var(--text-primary)' }}>
                  ⚠️ Flagged Sentences
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {result.flagged_sentences.map((s: any, i: number) => (
                    <div key={i} style={{
                      padding: '1rem',
                      background: 'rgba(244, 63, 94, 0.06)',
                      borderLeft: '4px solid var(--brand-rose)',
                      borderRadius: '0 10px 10px 0',
                    }}>
                      <div className="flex items-center gap-2 mb-2">
                        <span className="badge badge-high" style={{ fontSize: '0.75rem' }}>
                          {s.similarity}% match
                        </span>
                      </div>
                      <p className="text-sm" style={{ color: 'var(--brand-rose)', marginBottom: '0.5rem', lineHeight: 1.6 }}>
                        <strong>Your text:</strong> "{s.submitted_sentence}"
                      </p>
                      <p className="text-sm text-secondary" style={{ lineHeight: 1.6 }}>
                        <strong>Matched:</strong> "{s.matched_sentence}"
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Source Matches */}
            {result.matches?.length > 0 && (
              <div className="card">
                <h3 className="font-bold text-lg mb-4" style={{ color: 'var(--text-primary)' }}>
                  📚 Matched Sources
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
                  {result.matches.map((m: any, i: number) => (
                    <div key={i} style={{
                      padding: '1rem',
                      background: 'var(--bg-secondary)',
                      borderRadius: 10,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '1rem',
                    }}>
                      <div style={{
                        width: 52, height: 52, borderRadius: '50%', flexShrink: 0,
                        background: m.similarity >= 40 ? 'rgba(244,63,94,0.15)' : 'rgba(59,130,246,0.15)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: '1rem', fontWeight: 800,
                        color: m.similarity >= 40 ? 'var(--brand-rose)' : 'var(--brand-blue)',
                      }}>
                        {m.similarity}%
                      </div>
                      <div style={{ flex: 1 }}>
                        <div className="font-bold text-sm" style={{ color: 'var(--text-primary)' }}>{m.source}</div>
                        <div className="text-xs text-muted mt-1">
                          Cosine: {m.cosine_similarity}% · N-gram overlap: {m.ngram_similarity}%
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {result.score < 15 && (
              <div className="alert" style={{
                background: 'rgba(16,185,129,0.1)',
                border: '1px solid rgba(16,185,129,0.3)',
                color: 'var(--brand-green)',
                borderRadius: 10, padding: '1rem',
              }}>
                ✅ Great news! Your text appears to be original. No significant similarity was detected.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default PlagiarismPage;
