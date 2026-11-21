import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { essays as essayApi } from '../api/services';
import { format } from 'date-fns';

const EssaysPage: React.FC = () => {
  const navigate = useNavigate();
  const [essayList, setEssayList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    essayApi.list()
      .then(r => setEssayList(r.data.results || r.data))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center" style={{height:'40vh'}}><div className="spinner" style={{width:48,height:48}} /></div>;

  return (
    <div className="fade-in">
      <div className="page-header flex items-center justify-between">
        <div>
          <h1 className="page-title">My Essays</h1>
          <p className="page-subtitle">{essayList.length} submission{essayList.length !== 1 ? 's' : ''} total</p>
        </div>
        <button id="new-essay-btn" className="btn btn-primary" onClick={() => navigate('/analyze')}>✍ New Essay</button>
      </div>

      {essayList.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '4rem' }}>
          <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>📄</div>
          <h2 style={{ color: 'var(--text-primary)', marginBottom: '0.5rem' }}>No essays yet</h2>
          <p className="text-secondary mb-4">Submit your first essay to get started</p>
          <button className="btn btn-primary btn-lg" onClick={() => navigate('/analyze')}>Analyze My First Essay</button>
        </div>
      ) : (
        <div className="card">
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Submitted</th>
                  <th>Status</th>
                  <th>Words</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {essayList.map((essay: any) => (
                  <tr key={essay.id}>
                    <td>
                      <div className="font-bold text-sm">{essay.title || 'Untitled Essay'}</div>
                      <div className="text-xs text-muted font-mono">{essay.id?.slice(0, 8)}…</div>
                    </td>
                    <td className="text-sm">
                      {essay.submitted_at ? format(new Date(essay.submitted_at), 'MMM d, yyyy HH:mm') : '—'}
                    </td>
                    <td>
                      <span className={`badge ${essay.status === 'done' ? 'badge-low' : essay.status === 'failed' ? 'badge-high' : 'badge-medium'}`}>
                        {essay.status}
                      </span>
                    </td>
                    <td className="text-sm">{essay.essay_text?.split(' ').length || 0}</td>
                    <td>
                      <div className="flex gap-2">
                        {essay.status === 'done' && essay.has_result && (
                          <button id={`view-${essay.id?.slice(0,8)}`} className="btn btn-secondary btn-sm"
                            onClick={() => navigate(`/essays/${essay.id}/results`)}>
                            Results
                          </button>
                        )}
                        {essay.status === 'pending' && (
                          <button id={`analyze-${essay.id?.slice(0,8)}`} className="btn btn-primary btn-sm"
                            onClick={async () => {
                              await essayApi.analyze(essay.id);
                              navigate(`/essays/${essay.id}/results`);
                            }}>
                            Analyze
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default EssaysPage;
