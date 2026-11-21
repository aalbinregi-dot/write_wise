import api from './client';

export const auth = {
  register: (data: any) => api.post('/auth/register/', data),
  login:    (data: any) => api.post('/auth/login/', data),
  me:       ()          => api.get('/auth/me/'),
};

export const essays = {
  list:     ()          => api.get('/essays/'),
  create:   (data: any) => api.post('/essays/', data),
  detail:   (id: string)=> api.get(`/essays/${id}/`),
  analyze:  (id: string)=> api.post(`/essays/${id}/analyze/`),
  results:  (id: string)=> api.get(`/essays/${id}/results/`),
  report:   (id: string)=> api.get(`/essays/${id}/report/`, { responseType: 'blob' }),
  override: (id: string, score: number) => api.post(`/essays/${id}/override/`, { teacher_score: score }),
};

export const students = {
  progress:        (id: number) => api.get(`/students/${id}/progress/`),
  recommendations: (id: number) => api.get(`/students/${id}/recommendations/`),
  analytics:       (id: number) => api.get(`/students/${id}/analytics/`),
  myAnalytics:     ()            => api.get('/analytics/me/'),
};

export const teacher = {
  classAnalytics: () => api.get('/teacher/class-analytics/'),
  students:       () => api.get('/auth/teacher/students/'),
};

export const lessons = {
  all:      (category?: string) => api.get('/lessons/', { params: category ? { category } : {} }),
  complete: (id: string, title: string, category: string) =>
    api.post(`/learning/${id}/complete/`, { title, category }),
  progress: () => api.get('/learning/progress/'),
};

export const tools = {
  plagiarism: (text: string) => api.post('/tools/plagiarism/', { text }),
  humanize:   (text: string) => api.post('/tools/humanize/',   { text }),
};
