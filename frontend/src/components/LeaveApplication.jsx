import { useState, useEffect } from 'react';
import { api } from '../api';

const DAYS = ['MON', 'TUE', 'WED', 'THU', 'FRI'];
const DAY_LABELS = { MON: 'Monday', TUE: 'Tuesday', WED: 'Wednesday', THU: 'Thursday', FRI: 'Friday' };
const TIME_SLOTS = [
  '07:30-08:30', '08:30-09:30', '10:00-11:00', '11:00-12:00',
  '12:00-13:00', '13:00-14:00', '14:00-15:00', '15:00-16:00',
];

export default function LeaveApplication({ teacherId }) {
  const [leaves, setLeaves] = useState([]);
  const [loading, setLoading] = useState(true);
  const [day, setDay] = useState('MON');
  const [slotIndex, setSlotIndex] = useState(-1);
  const [reason, setReason] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadLeaves();
  }, [teacherId]);

  const loadLeaves = async () => {
    try {
      const data = await api.getLeaveApplications(`?teacher=${teacherId}`);
      setLeaves(data);
    } catch (err) {
      console.error('Failed to load leaves:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.createLeaveApplication({
        teacher: teacherId,
        day,
        slot_index: parseInt(slotIndex),
        reason,
      });
      setReason('');
      setSlotIndex(-1);
      await loadLeaves();
    } catch (err) {
      alert('Error: ' + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = async (id) => {
    if (!confirm('Cancel this leave application?')) return;
    try {
      await api.deleteLeaveApplication(id);
      await loadLeaves();
    } catch (err) {
      alert('Error: ' + err.message);
    }
  };

  const statusColor = {
    PENDING: { bg: '#fef3c7', color: '#92400e' },
    APPROVED: { bg: '#dcfce7', color: '#166534' },
    DECLINED: { bg: '#fee2e2', color: '#991b1b' },
  };

  return (
    <div>
      <h3 style={styles.heading}>📝 Leave Applications</h3>

      <form onSubmit={handleSubmit} style={styles.form}>
        <div style={styles.formRow}>
          <div style={styles.formGroup}>
            <label style={styles.label}>Day</label>
            <select style={styles.select} value={day} onChange={e => setDay(e.target.value)}>
              {DAYS.map(d => <option key={d} value={d}>{DAY_LABELS[d]}</option>)}
            </select>
          </div>
          <div style={styles.formGroup}>
            <label style={styles.label}>Time Slot</label>
            <select style={styles.select} value={slotIndex} onChange={e => setSlotIndex(e.target.value)}>
              <option value={-1}>Full Day</option>
              {TIME_SLOTS.map((t, i) => <option key={i} value={i}>{t}</option>)}
            </select>
          </div>
        </div>
        <div style={styles.formGroup}>
          <label style={styles.label}>Reason</label>
          <textarea
            style={styles.textarea}
            value={reason}
            onChange={e => setReason(e.target.value)}
            placeholder="Enter reason for leave..."
            rows={2}
          />
        </div>
        <button style={styles.submitBtn} type="submit" disabled={submitting}>
          {submitting ? 'Submitting...' : 'Submit Leave Application'}
        </button>
      </form>

      <h4 style={{ margin: '20px 0 10px', color: '#334155' }}>My Leave History</h4>
      {loading ? (
        <p>Loading...</p>
      ) : leaves.length === 0 ? (
        <p style={styles.empty}>No leave applications yet.</p>
      ) : (
        <div style={styles.leaveList}>
          {leaves.map(leave => (
            <div key={leave.id} style={styles.leaveCard}>
              <div style={styles.leaveHeader}>
                <span style={styles.leaveDay}>
                  {DAY_LABELS[leave.day]} — {leave.slot_index === -1 ? 'Full Day' : TIME_SLOTS[leave.slot_index]}
                </span>
                <span style={{
                  ...styles.statusBadge,
                  background: statusColor[leave.status].bg,
                  color: statusColor[leave.status].color,
                }}>
                  {leave.status}
                </span>
              </div>
              {leave.reason && <p style={styles.leaveReason}>{leave.reason}</p>}
              {leave.admin_remarks && (
                <p style={styles.adminRemarks}>
                  <strong>Admin:</strong> {leave.admin_remarks}
                </p>
              )}
              <div style={styles.leaveFooter}>
                <span style={styles.leaveDate}>
                  Applied: {new Date(leave.created_at).toLocaleDateString()}
                </span>
                {leave.status === 'PENDING' && (
                  <button
                    style={styles.cancelBtn}
                    onClick={() => handleCancel(leave.id)}
                  >
                    Cancel
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const styles = {
  heading: { margin: '0 0 12px 0', color: '#0f172a' },
  form: {
    background: '#f8fafc',
    border: '1px solid #e2e8f0',
    borderRadius: '8px',
    padding: '16px',
  },
  formRow: { display: 'flex', gap: '12px', marginBottom: '12px' },
  formGroup: { flex: 1 },
  label: { display: 'block', fontSize: '13px', fontWeight: '600', color: '#334155', marginBottom: '4px' },
  select: {
    width: '100%',
    padding: '8px 10px',
    border: '1px solid #cbd5e1',
    borderRadius: '6px',
    fontSize: '13px',
    boxSizing: 'border-box',
  },
  textarea: {
    width: '100%',
    padding: '8px 10px',
    border: '1px solid #cbd5e1',
    borderRadius: '6px',
    fontSize: '13px',
    resize: 'vertical',
    boxSizing: 'border-box',
  },
  submitBtn: {
    background: '#0d9488',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    padding: '10px 20px',
    fontSize: '13px',
    fontWeight: '600',
    cursor: 'pointer',
    marginTop: '8px',
  },
  empty: { color: '#94a3b8', fontSize: '14px', fontStyle: 'italic' },
  leaveList: { display: 'flex', flexDirection: 'column', gap: '8px' },
  leaveCard: {
    background: 'white',
    border: '1px solid #e2e8f0',
    borderRadius: '8px',
    padding: '12px 16px',
  },
  leaveHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '4px',
  },
  leaveDay: { fontWeight: '600', color: '#0f172a', fontSize: '14px' },
  statusBadge: {
    padding: '3px 10px',
    borderRadius: '12px',
    fontSize: '11px',
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  leaveReason: { color: '#475569', fontSize: '13px', margin: '4px 0' },
  adminRemarks: {
    color: '#1e40af',
    fontSize: '13px',
    margin: '4px 0',
    background: '#eff6ff',
    padding: '6px 10px',
    borderRadius: '4px',
  },
  leaveFooter: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: '8px',
  },
  leaveDate: { fontSize: '12px', color: '#94a3b8' },
  cancelBtn: {
    background: '#fee2e2',
    color: '#991b1b',
    border: 'none',
    borderRadius: '4px',
    padding: '4px 12px',
    fontSize: '12px',
    fontWeight: '600',
    cursor: 'pointer',
  },
};
