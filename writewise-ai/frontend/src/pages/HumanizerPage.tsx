import React, { useState } from 'react';
import { tools as toolsApi } from '../api/services';

const HumanizerPage: React.FC = () => {
  const [text, setText] = useState('');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;

  const handleHumanize = async () => {
    if (wordCount < 5) { setError('Please enter at least 5 words.'); return; }
    setError(''); setLoading(true); setResult(null);
    try {
      const res = await toolsApi.humanize(text);
      setResult(res.data);
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Humanization failed. Please try again.');
    } finally { setLoading(false); }
  };

  const handleCopy = () => {
    if (result?.humanized_text) {
      navigator.clipboard.writeText(result.humanized_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const SAMPLE_AI_TEXT = `Furthermore, it is important to note that the utilization of cutting-edge technology has significantly enhanced the overall learning experience. In the modern era, students are able to leverage digital platforms to optimize their academic performance. It is undeniable that this paradigm shift has facilitated a more comprehensive approach to education. Moreover, the implementation of these robust solutions demonstrates the seamless integration of innovation in the contemporary educational landscape. In conclusion, one must acknowledge the pivotal role that technology plays in shaping the future of learning.`;

  return (
    <div className="fade-in" style={{ maxWidth: 1000, margin: '0 auto' }}>
      {/* Header */}
      <div className="page-header text-center mb-6">
        <h1 className="page-title" style={{ fontSize: '2.2rem' }}>✨ AI Text Humanizer</h1>
        <p className="page-subtitle" style={{ fontSize: '1rem' }}>
          Paste AI-generated text and get a natural, human-sounding rewrite instantly.
        </p>
      </div>

      {error && <div className="alert alert-error mb-4">{error}</div>}

      {/* Sample loader */}
      <div className="card mb-4" style={{
        background: 'rgba(99,102,241,0.08)',
        border: '1px solid rgba(99,102,241,0.2)',
        padding: '1rem 1.25rem',
      }}>
        <div className="flex items-center justify-between" style={{ flexWrap: 'wrap', gap: '0.75rem' }}>
          <div>
            <span className="font-bold text-sm" style={{ color: 'var(--brand-indigo)' }}>💡 Try a sample</span>
            <span className="text-sm text-secondary" style={{ marginLeft: 6 }}>
              Load an AI-sounding paragraph to see the humanizer in action:
            </span>
          </div>
          <button
            id="load-sample-humanizer-btn"
            className="btn btn-secondary btn-sm"
            onClick={() => { setText(SAMPLE_AI_TEXT); setResult(null); }}
          >
            Load AI Sample Text
          </button>
        </div>
      </div>

      {/* Input */}
      <div className="card mb-4" style={{ padding: '2rem' }}>
        <div className="form-group mb-4">
          <div className="flex items-center justify-between mb-1">
            <label className="form-label" style={{ fontSize: '0.9rem' }}>AI-Generated Text</label>
            <span className="text-xs text-muted">
              <span style={{ fontWeight: 700, color: wordCount >= 5 ? 'var(--brand-green)' : 'var(--text-muted)' }}>
                {wordCount} words
              </span>
            </span>
          </div>
          <textarea
            id="humanizer-input"
            className="form-textarea"
            placeholder="Paste your AI-generated text here..."
            style={{ minHeight: 180, fontSize: '0.95rem', lineHeight: 1.7 }}
            value={text}
            onChange={e => { setText(e.target.value); setResult(null); }}
          />
        </div>
        <button
          id="humanize-btn"
          className="btn btn-primary btn-lg w-full"
          onClick={handleHumanize}
          disabled={loading || wordCount < 5}
        >
          {loading
            ? <><span className="spinner" style={{ width: 18, height: 18 }} /> Humanizing...</>
            : '✨ Humanize Text'}
        </button>
      </div>

      {/* Results */}
      {result && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }} className="fade-in">

          {/* Stats bar */}
          <div className="grid-3">
            <div className="card" style={{ textAlign: 'center' }}>
              <span className="text-xs text-muted" style={{ textTransform: 'uppercase' }}>Changes Made</span>
              <div className="font-bold text-xl mt-1" style={{ color: 'var(--brand-indigo)' }}>
                {result.changes_made}
              </div>
              <span className="text-xs text-muted">phrase rewrites</span>
            </div>
            <div className="card" style={{ textAlign: 'center' }}>
              <span className="text-xs text-muted" style={{ textTransform: 'uppercase' }}>Original Words</span>
              <div className="font-bold text-xl mt-1" style={{ color: 'var(--brand-blue)' }}>
                {result.original_text.trim().split(/\s+/).length}
              </div>
              <span className="text-xs text-muted">word count</span>
            </div>
            <div className="card" style={{ textAlign: 'center' }}>
              <span className="text-xs text-muted" style={{ textTransform: 'uppercase' }}>Output Words</span>
              <div className="font-bold text-xl mt-1" style={{ color: 'var(--brand-green)' }}>
                {result.humanized_text.trim().split(/\s+/).length}
              </div>
              <span className="text-xs text-muted">word count</span>
            </div>
          </div>

          {/* Side-by-side comparison */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
            {/* Original */}
            <div className="card" style={{ padding: '1.5rem' }}>
              <div className="flex items-center gap-2 mb-3">
                <span style={{
                  background: 'rgba(244,63,94,0.15)', color: 'var(--brand-rose)',
                  borderRadius: 6, padding: '0.2rem 0.6rem', fontSize: '0.75rem', fontWeight: 700,
                }}>
                  🤖 AI-Generated
                </span>
              </div>
              <p style={{
                fontSize: '0.9rem', lineHeight: 1.8, color: 'var(--text-secondary)',
                whiteSpace: 'pre-wrap', wordBreak: 'break-word',
              }}>
                {result.original_text}
              </p>
            </div>

            {/* Humanized */}
            <div className="card" style={{
              padding: '1.5rem',
              border: '1px solid rgba(16,185,129,0.3)',
              background: 'rgba(16,185,129,0.04)',
            }}>
              <div className="flex items-center justify-between mb-3">
                <span style={{
                  background: 'rgba(16,185,129,0.15)', color: 'var(--brand-green)',
                  borderRadius: 6, padding: '0.2rem 0.6rem', fontSize: '0.75rem', fontWeight: 700,
                }}>
                  ✅ Humanized
                </span>
                <button
                  id="copy-humanized-btn"
                  className="btn btn-ghost btn-sm"
                  onClick={handleCopy}
                  style={{ fontSize: '0.75rem' }}
                >
                  {copied ? '✓ Copied!' : '📋 Copy'}
                </button>
              </div>
              <p style={{
                fontSize: '0.9rem', lineHeight: 1.8, color: 'var(--text-primary)',
                whiteSpace: 'pre-wrap', wordBreak: 'break-word',
              }}>
                {result.humanized_text}
              </p>
            </div>
          </div>

          {/* Changes log */}
          {result.changes?.length > 0 && (
            <div className="card">
              <h3 className="font-bold text-lg mb-4" style={{ color: 'var(--text-primary)' }}>
                📝 Changes Made
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
                {result.changes.map((c: any, i: number) => (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'flex-start', gap: '1rem',
                    padding: '0.75rem 1rem',
                    background: 'var(--bg-secondary)',
                    borderRadius: 8,
                  }}>
                    <span style={{
                      background: 'rgba(99,102,241,0.15)', color: 'var(--brand-indigo)',
                      borderRadius: 6, padding: '0.15rem 0.5rem',
                      fontSize: '0.7rem', fontWeight: 700, flexShrink: 0, marginTop: 2,
                    }}>
                      {c.type}
                    </span>
                    <div style={{ flex: 1, fontSize: '0.85rem' }}>
                      <span style={{ color: 'var(--brand-rose)' }}>"{c.original}"</span>
                      <span className="text-muted" style={{ margin: '0 0.4rem' }}>→</span>
                      <span style={{ color: 'var(--brand-green)' }}>"{c.replacement}"</span>
                    </div>
                  </div>
                ))}
              </div>
              <p className="text-xs text-muted mt-3" style={{ fontStyle: 'italic' }}>
                {result.readability_note}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default HumanizerPage;
