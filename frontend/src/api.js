const API_BASE = 'http://localhost:8000/api';

export async function apiRequest(endpoint, options = {}) {
  const token = localStorage.getItem('token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Token ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(error.error || error.detail || 'Request failed');
  }

  if (response.status === 204) return null;
  return response.json();
}

export const api = {
  login: (username, password) =>
    apiRequest('/login/', { method: 'POST', body: JSON.stringify({ username, password }) }),

  // Teacher Unavailability (Availability)
  getUnavailability: (teacherId) =>
    apiRequest(`/teacher-unavailability/?teacher=${teacherId}`),
  createUnavailability: (data) =>
    apiRequest('/teacher-unavailability/', { method: 'POST', body: JSON.stringify(data) }),
  deleteUnavailability: (id) =>
    apiRequest(`/teacher-unavailability/${id}/`, { method: 'DELETE' }),

  // Leave Applications
  getLeaveApplications: (params = '') =>
    apiRequest(`/leave-applications/${params}`),
  createLeaveApplication: (data) =>
    apiRequest('/leave-applications/', { method: 'POST', body: JSON.stringify(data) }),
  approveLeave: (id, remarks = '') =>
    apiRequest(`/leave-applications/${id}/approve/`, {
      method: 'POST',
      body: JSON.stringify({ admin_remarks: remarks }),
    }),
  declineLeave: (id, remarks = '') =>
    apiRequest(`/leave-applications/${id}/decline/`, {
      method: 'POST',
      body: JSON.stringify({ admin_remarks: remarks }),
    }),
  deleteLeaveApplication: (id) =>
    apiRequest(`/leave-applications/${id}/`, { method: 'DELETE' }),
};
