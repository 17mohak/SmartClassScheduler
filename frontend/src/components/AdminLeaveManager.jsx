import { useState, useEffect } from 'react';
import { api } from '../api';

const DAY_LABELS = { MON: 'Monday', TUE: 'Tuesday', WED: 'Wednesday', THU: 'Thursday', FRI: 'Friday' };
const TIME_SLOTS = [
  '07:30-08:30', '08:30-09:30', '10:00-11:00', '11:00-12:00',
  '12:00-13:00', '13:00-14:00', '14:00-15:00', '15:00-16:00',
];

export default function AdminLeaveManager() {
  const [leaves, setLeaves] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('PENDING');
  const [remarks, setRemarks] = useState({});
  const [processing, setProcessing] = useState(null);

  useEffect(() => {
    loadLeaves();
  }, [filter]);

  const loadLeaves = async () => {
    setLoading(true);
    try {
      const params = filter ? `?status=${filter}` : '';
      const data = await api.getLeaveApplications(params);
      setLeaves(data);
    } catch (err) {
      console.error('Failed to load leaves:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (id) => {
    setProcessing(id);
    try {
      await api.approveLeave(id, remarks[id] || '');
      await loadLeaves();
    } catch (err) {
      alert('Error: ' + err.message);
    } finally {
      setProcessing(null);
    }
  };

  const handleDecline = async (id) => {
    setProcessing(id);
    try {
      await api.declineLeave(id, remarks[id] || '');
      await loadLeaves();
    } catch (err) {
      alert('Error: ' + err.message);
    } finally {
      setProcessing(null);
    }
  };

  const statusColor = {
    PENDING: { bg: '#fef3c7', color: '#92400e' },
    APPROVED: { bg: '#dcfce7', color: '#166534' },
    DECLINED: { bg: '#fee2e2', color: '#991b1b' },
  };

  return (
    <div>
      <h3 style={styles.heading}>📋 Leave Applications Management</h3>

      <div style={styles.filters}>
        {['PENDING', 'APPROVED', 'DECLINED', ''].map(f => (
          <button
            key={f}
            style={{
              ...styles.filterBtn,
              ...(filter === f ? styles.filterActive : {}),
            }}
            onClick={() => setFilter(f)}
          >
            {f || 'All'}
          </button>
        ))}
      </div>

      {loading ? (
        <p>Loading leave applications...</p>
      ) : leaves.length === 0 ? (
        <p style={styles.empty}>No leave applications found.</p>
      ) : (
        <div style={styles.list}>
          {leaves.map(leave => (
            <div key={leave.id} style={styles.card}>
              <div style={styles.cardHeader}>
                <div>
                  <span style={styles.teacherName}>{leave.teacher_name}</span>
                  <span style={styles.leaveInfo}>
                    {DAY_LABELS[leave.day]} — {leave.slot_index === -1 ? 'Full Day' : TIME_SLOTS[leave.slot_index]}
                  </span>
                </div>
                <span style={{
                  ...styles.statusBadge,
                  background: statusColor[leave.status].bg,
                  color: statusColor[leave.status].color,
                }}>
                  {leave.status}
                </span>
              </div>

              {leave.reason && <p style={styles.reason}>{leave.reason}</p>}

              <div style={styles.meta}>
                Applied: {new Date(leave.created_at).toLocaleDateString()}
              </div>

              {leave.admin_remarks && (
                <p style={styles.existingRemarks}>
                  <strong>Your remarks:</strong> {leave.admin_remarks}
                </p>
              )}

              {leave.status === 'PENDING' && (
                <div style={styles.actions}>
                  <input
                    style={styles.remarkInput}
                    type="text"
                    placeholder="Add remarks (optional)..."
                    value={remarks[leave.id] || ''}
                    onChange={e => setRemarks({ ...remarks, [leave.id]: e.target.value })}
                  />
                  <button
                    style={styles.approveBtn}
                    onClick={() => handleApprove(leave.id)}
                    disabled={processing === leave.id}
                  >
                    ✓ Approve
                  </button>
                  <button
                    style={styles.declineBtn}
                    onClick={() => handleDecline(leave.id)}
                    disabled={processing === leave.id}
                  >
                    ✕ Decline
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const styles = {
  heading: { margin: '0 0 12px 0', color: '#0f172a' },
  filters: { display: 'flex', gap: '6px', marginBottom: '16px' },
  filterBtn: {
    padding: '6px 14px',
    border: '1px solid #cbd5e1',
    borderRadius: '6px',
    background: 'white',
    fontSize: '13px',
    cursor: 'pointer',
    color: '#475569',
  },
  filterActive: {
    background: '#0d9488',
    color: 'white',
    borderColor: '#0d9488',
  },
  empty: { color: '#94a3b8', fontSize: '14px', fontStyle: 'italic' },
  list: { display: 'flex', flexDirection: 'column', gap: '10px' },
  card: {
    background: 'white',
    border: '1px solid #e2e8f0',
    borderRadius: '8px',
    padding: '14px 18px',
  },
  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '6px',
  },
  teacherName: {
    fontWeight: '700',
    color: '#0f172a',
    fontSize: '15px',
    display: 'block',
  },
  leaveInfo: {
    color: '#475569',
    fontSize: '13px',
  },
  statusBadge: {
    padding: '3px 10px',
    borderRadius: '12px',
    fontSize: '11px',
    fontWeight: '700',
    textTransform: 'uppercase',
    whiteSpace: 'nowrap',
  },
  reason: { color: '#475569', fontSize: '13px', margin: '4px 0' },
  meta: { fontSize: '12px', color: '#94a3b8', margin: '4px 0' },
  existingRemarks: {
    color: '#1e40af',
    fontSize: '13px',
    margin: '6px 0',
    background: '#eff6ff',
    padding: '6px 10px',
    borderRadius: '4px',
  },
  actions: {
    display: 'flex',
    gap: '8px',
    marginTop: '10px',
    alignItems: 'center',
  },
  remarkInput: {
    flex: 1,
    padding: '7px 10px',
    border: '1px solid #cbd5e1',
    borderRadius: '6px',
    fontSize: '13px',
  },
  approveBtn: {
    background: '#16a34a',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    padding: '8px 14px',
    fontSize: '13px',
    fontWeight: '600',
    cursor: 'pointer',
    whiteSpace: 'nowrap',
  },
  declineBtn: {
    background: '#dc2626',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    padding: '8px 14px',
    fontSize: '13px',
    fontWeight: '600',
    cursor: 'pointer',
    whiteSpace: 'nowrap',
  },
};
