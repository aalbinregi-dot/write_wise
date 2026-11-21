import React, { useEffect, useState } from 'react';
import { lessons as lessonsApi } from '../api/services';

const CATEGORIES = ['All', 'Grammar', 'Writing', 'Reading', 'Listening', 'Speaking', 'Vocabulary', 'Pronunciation'];

const LearningPage: React.FC = () => {
  const [lessonList, setLessonList] = useState<any[]>([]);
  const [progress,   setProgress]   = useState<any[]>([]);
  const [category,   setCategory]   = useState('All');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      lessonsApi.all().then(r => setLessonList(r.data.lessons || [])),
      lessonsApi.progress().then(r => setProgress(r.data.results || r.data)),
    ]).finally(() => setLoading(false));
  }, []);

  const filtered = category === 'All'
    ? lessonList
    : lessonList.filter((l: any) => l.Category === category);

  const progressMap: Record<string, string> = {};
  (progress || []).forEach((p: any) => { progressMap[p.lesson_id] = p.status; });

  const markComplete = async (lesson: any) => {
    await lessonsApi.complete(lesson.Lesson_ID, lesson.Lesson, lesson.Category);
    setProgress(prev => {
      const existing = prev.find((p: any) => p.lesson_id === lesson.Lesson_ID);
      if (existing) return prev.map((p: any) => p.lesson_id === lesson.Lesson_ID ? { ...p, status: 'completed' } : p);
      return [...prev, { lesson_id: lesson.Lesson_ID, lesson_title: lesson.Lesson, lesson_category: lesson.Category, status: 'completed' }];
    });
  };

  if (loading) return <div className="flex items-center justify-center" style={{height:'40vh'}}><div className="spinner" style={{width:48,height:48}} /></div>;

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">Learning Plan</h1>
        <p className="page-subtitle">{lessonList.length} lessons available across all skill areas</p>
      </div>

      {/* Category filter */}
      <div className="flex gap-2 mb-6" style={{ flexWrap: 'wrap' }}>
        {CATEGORIES.map(cat => (
          <button key={cat} id={`filter-${cat}`}
            className={`btn btn-sm ${category === cat ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setCategory(cat)}>
            {cat}
          </button>
        ))}
      </div>

      {/* Stats */}
      <div className="grid-3 mb-6">
        {[
          { label: 'Total Lessons',    value: lessonList.length, color: 'var(--brand-blue)' },
          { label: 'Completed',        value: Object.values(progressMap).filter(s => s === 'completed').length, color: 'var(--brand-green)' },
          { label: 'In Progress',      value: Object.values(progressMap).filter(s => s === 'started').length,   color: 'var(--brand-amber)' },
        ].map(s => (
          <div key={s.label} className="stat-card">
            <span className="stat-label">{s.label}</span>
            <span className="stat-value" style={{ color: s.color }}>{s.value}</span>
          </div>
        ))}
      </div>

      {/* Lesson cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1rem' }}>
        {filtered.map((lesson: any, i: number) => {
          const status = progressMap[lesson.Lesson_ID] || 'not_started';
          return (
            <div key={i} className="card" style={{ transition: 'all 0.2s', cursor: 'default' }}>
              <div className="flex items-center justify-between mb-3">
                <span className="badge badge-medium">{lesson.Category}</span>
                {status === 'completed' ? (
                  <span className="badge badge-low">✓ Completed</span>
                ) : status === 'started' ? (
                  <span className="badge badge-medium">In Progress</span>
                ) : null}
              </div>
              <h3 className="font-bold text-sm mb-2" style={{ color: 'var(--text-primary)', lineHeight: 1.4 }}>
                {lesson.Lesson || 'Unnamed Lesson'}
              </h3>
              <div className="flex items-center gap-3 mb-3">
                <span className="text-xs text-muted">⏱ {lesson.Time_to_learn || 1} hr</span>
                <span className="text-xs text-muted">📊 Level {parseFloat(lesson.Difficulty || 1).toFixed(1)}</span>
              </div>
              <div className="flex gap-2">
                {lesson.Theory_References && lesson.Theory_References !== 'Link' && (
                  <a href={lesson.Theory_References} target="_blank" rel="noreferrer" className="btn btn-ghost btn-sm">📖 Theory</a>
                )}
                {status !== 'completed' ? (
                  <button id={`complete-${lesson.Lesson_ID}`}
                    className="btn btn-secondary btn-sm"
                    onClick={() => markComplete(lesson)}>
                    Mark Complete
                  </button>
                ) : (
                  <span className="btn btn-ghost btn-sm" style={{ opacity: 0.5, cursor: 'default' }}>✓ Done</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default LearningPage;
