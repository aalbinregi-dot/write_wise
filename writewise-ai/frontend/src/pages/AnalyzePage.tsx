import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { essays as essayApi } from '../api/services';

const SAMPLES = [
  {
    title: 'Technology in Education',
    text: `Technology has significantly changed the way students learn and teachers teach in modern education. The integration of digital tools in classrooms have opened up new possibilities for personalized learning. Students can now access vast resources online, collaborate with peers across the world, and receive immediate feedback on their work. However, there are also challenges associated with this transformation. Many students is distracted by social media and entertainment platforms. Furthermore technology access remain unequal across different socioeconomic groups. Despite these challenges, the benefits of technology in education outweigh the drawbacks when implemented thoughtfully. Schools should ensure that students develop critical thinking skills alongside their digital literacy. In conclusion, technology offers tremendous opportunities for improving educational outcomes but requires careful implementation and teacher guidance.`
  },
  {
    title: 'Environmental Protection',
    text: `Protecting the environment is one of the most urgent priorities of our time. Industrial activities and excessive consumption has lead to severe pollution, climate change, and habitat loss. Governments must enforce stricter regulations on carbon emissions and promote renewable energy sources like solar and wind power. Additionally individuals should adopt sustainable habits such as reducing waste, recycling, and conserving energy. Many people believes that economic growth is more important than environmental protection, but without a healthy planet, long-term prosperity is impossible. In summary, environmental conservation requires collective effort from governments, corporations, and individuals to secure a sustainable future for upcoming generations.`
  }
];

const AnalyzePage: React.FC = () => {
  const navigate = useNavigate();
  const fileRef  = useRef<HTMLInputElement>(null);
  const [text, setText]   = useState('');
  const [title, setTitle] = useState('');
  const [file, setFile]   = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [step, setStep]   = useState<'edit'|'analyzing'>('edit');

  const wordCount   = text.trim() ? text.trim().split(/\s+/).length : 0;
  const readingTime = Math.max(1, Math.ceil(wordCount / 200));

  const loadSample = (sample: typeof SAMPLES[0]) => {
    setTitle(sample.title);
    setText(sample.text);
    setError('');
  };

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    if (f.name.endsWith('.txt')) {
      const reader = new FileReader();
      reader.onload = (ev) => setText(ev.target?.result as string || '');
      reader.readAsText(f);
    }
  };

  const handleAnalyze = async () => {
    if (!text.trim() && !file) { setError('Please paste your essay or select a sample essay below.'); return; }
    if (wordCount < 15 && text.trim()) { setError('Please enter an essay of at least 15 words.'); return; }

    setError(''); setLoading(true); setStep('analyzing');
    try {
      const formData = new FormData();
      formData.append('title', title || 'My Essay');
      formData.append('essay_text', text);
      if (file) formData.append('file_upload', file);

      const createRes = await essayApi.create(formData);
      const essayId   = createRes.data.id;

      await essayApi.analyze(essayId);
      navigate(`/essays/${essayId}/results`);
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Analysis failed. Please try again.');
      setStep('edit');
    } finally { setLoading(false); }
  };

  return (
    <div className="fade-in" style={{ maxWidth: 900, margin: '0 auto' }}>
      <div className="page-header text-center mb-6">
        <h1 className="page-title" style={{ fontSize: '2.2rem' }}>Grade & Analyze Essay</h1>
        <p className="page-subtitle" style={{ fontSize: '1rem' }}>
          Paste your essay text below, upload a document, or click a sample to test instantly.
        </p>
      </div>

      {error && <div className="alert alert-error mb-4">{error}</div>}

      {step === 'analyzing' ? (
        <div className="card" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
          <div className="spinner" style={{ width: 56, height: 56, margin: '0 auto 1.5rem' }} />
          <h2 style={{ color: 'var(--text-primary)', fontSize: '1.5rem', marginBottom: '0.5rem' }}>
            Analyzing Essay...
          </h2>
          <p className="text-secondary mb-6">
            Evaluating grammar, spelling, vocabulary, structure, and computing AI score...
          </p>
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            {['Linguistic Features', 'AI Scoring Model', 'Grammar Check', 'Spelling Check', 'CEFR Lesson Mapping'].map((stepName, i) => (
              <span key={i} className="badge badge-low" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}>
                ✓ {stepName}
              </span>
            ))}
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Quick sample loader banner */}
          <div className="card" style={{ background: 'rgba(99, 102, 241, 0.08)', border: '1px solid rgba(99, 102, 241, 0.2)', padding: '1rem 1.25rem' }}>
            <div className="flex items-center justify-between" style={{ flexWrap: 'wrap', gap: '0.75rem' }}>
              <div>
                <span className="font-bold text-sm" style={{ color: 'var(--brand-blue)' }}>💡 Want to test instantly?</span>
                <span className="text-sm text-secondary" style={{ marginLeft: 6 }}>Click a sample essay to auto-fill:</span>
              </div>
              <div className="flex gap-2">
                {SAMPLES.map((sample, idx) => (
                  <button key={idx} id={`sample-btn-${idx}`} className="btn btn-secondary btn-sm" onClick={() => loadSample(sample)}>
                    Sample {idx + 1}: {sample.title}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Main Editor Card */}
          <div className="card" style={{ padding: '2rem' }}>
            <div className="form-group mb-4">
              <label className="form-label" style={{ fontSize: '0.9rem' }}>Essay Title</label>
              <input id="essay-title" type="text" className="form-input"
                placeholder="e.g. Technology in Education"
                value={title} onChange={e => setTitle(e.target.value)} />
            </div>

            <div className="form-group mb-4">
              <div className="flex items-center justify-between mb-1">
                <label className="form-label" style={{ fontSize: '0.9rem' }}>Essay Content</label>
                <div className="text-xs text-muted">
                  <span className="font-bold" style={{ color: wordCount >= 15 ? 'var(--brand-green)' : 'var(--text-muted)' }}>{wordCount} words</span>
                  <span> • ~{readingTime} min read</span>
                </div>
              </div>
              <textarea id="essay-text" className="form-textarea"
                placeholder="Paste or write your essay here..."
                style={{ minHeight: 280, fontSize: '0.95rem', lineHeight: 1.7 }}
                value={text} onChange={e => setText(e.target.value)} />
            </div>

            {/* File Upload Option */}
            <div className="flex items-center justify-between mb-6" style={{ background: 'var(--bg-secondary)', padding: '0.75rem 1rem', borderRadius: 8 }}>
              <div className="flex items-center gap-2">
                <button id="upload-file-btn" className="btn btn-ghost btn-sm" onClick={() => fileRef.current?.click()}>
                  📎 Upload File (TXT, PDF, DOCX)
                </button>
                {file && <span className="text-sm font-bold text-blue">📄 {file.name}</span>}
                <input ref={fileRef} type="file" accept=".txt,.pdf,.docx" style={{ display: 'none' }} onChange={handleFile} />
              </div>
              <span className="text-xs text-muted">Max size: 5MB</span>
            </div>

            {/* Submit Button */}
            <button id="analyze-btn" className="btn btn-primary btn-lg w-full" onClick={handleAnalyze}
              disabled={loading || (!text.trim() && !file)}>
              {loading ? <><span className="spinner" style={{width:18,height:18}} /> Grading...</> : '🚀 Grade & Analyze My Essay'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalyzePage;
