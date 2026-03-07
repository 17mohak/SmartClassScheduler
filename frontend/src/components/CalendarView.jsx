import { useState, useEffect } from 'react';
import { api } from '../api';

const DAYS = ['MON', 'TUE', 'WED', 'THU', 'FRI'];
const DAY_LABELS = { MON: 'Monday', TUE: 'Tuesday', WED: 'Wednesday', THU: 'Thursday', FRI: 'Friday' };
const TIME_SLOTS = [
  '07:30-08:30', '08:30-09:30', '10:00-11:00', '11:00-12:00',
  '12:00-13:00', '13:00-14:00', '14:00-15:00', '15:00-16:00',
];

export default function CalendarView({ teacherId, isAdmin }) {
  const [unavailabilities, setUnavailabilities] = useState([]);
  const [leaves, setLeaves] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [teacherId]);

  const loadData = async () => {
    setLoading(true);
    try {
      const params = teacherId ? `?teacher=${teacherId}` : '';
      const [unavailData, leaveData] = await Promise.all([
        api.getUnavailability(teacherId || ''),
        api.getLeaveApplications(params),
      ]);
      setUnavailabilities(unavailData);
      setLeaves(leaveData);
    } catch (err) {
      console.error('Failed to load calendar data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getCellStatus = (day, slotIndex) => {
    const isUnavail = unavailabilities.some(u => u.day === day && u.slot_index === slotIndex);

    const matchingLeaves = leaves.filter(l =>
      l.day === day && (l.slot_index === slotIndex || l.slot_index === -1)
    );

    const approvedLeave = matchingLeaves.find(l => l.status === 'APPROVED');
    const pendingLeave = matchingLeaves.find(l => l.status === 'PENDING');

    if (approvedLeave) return { type: 'leave-approved', label: '🏖️ Leave', tooltip: `Approved leave: ${approvedLeave.reason || 'No reason'}` };
    if (pendingLeave) return { type: 'leave-pending', label: '⏳ Pending', tooltip: `Pending leave: ${pendingLeave.reason || 'No reason'}` };
    if (isUnavail) return { type: 'unavailable', label: '✕', tooltip: 'Marked unavailable' };
    return { type: 'available', label: '✓', tooltip: 'Available' };
  };

  const cellStyles = {
    'leave-approved': { background: '#fef3c7', color: '#92400e', fontWeight: '600' },
    'leave-pending': { background: '#e0f2fe', color: '#075985', fontWeight: '600' },
    'unavailable': { background: '#fee2e2', color: '#991b1b', fontWeight: '700' },
    'available': { background: '#dcfce7', color: '#166534', fontWeight: '700' },
  };

  if (loading) return <p>Loading calendar...</p>;

  return (
    <div>
      <h3 style={styles.heading}>📅 Calendar Overview</h3>
      <p style={styles.hint}>
        <span style={{...styles.badge, background: '#dcfce7', color: '#166534'}}>✓ Available</span>{' '}
        <span style={{...styles.badge, background: '#fee2e2', color: '#991b1b'}}>✕ Unavailable</span>{' '}
        <span style={{...styles.badge, background: '#fef3c7', color: '#92400e'}}>🏖️ Leave Approved</span>{' '}
        <span style={{...styles.badge, background: '#e0f2fe', color: '#075985'}}>⏳ Leave Pending</span>
      </p>
      <div style={styles.tableWrapper}>
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>Time</th>
              {DAYS.map(d => (
                <th key={d} style={styles.th}>{DAY_LABELS[d]}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {TIME_SLOTS.map((time, slotIdx) => (
              <tr key={slotIdx}>
                <td style={styles.timeCell}>{time}</td>
                {DAYS.map(day => {
                  const status = getCellStatus(day, slotIdx);
                  return (
                    <td
                      key={day}
                      style={{ ...styles.cell, ...cellStyles[status.type] }}
                      title={status.tooltip}
                    >
                      {status.label}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const styles = {
  heading: { margin: '0 0 8px 0', color: '#0f172a' },
  hint: { fontSize: '13px', color: '#64748b', margin: '0 0 12px 0', lineHeight: '2' },
  badge: { padding: '2px 8px', borderRadius: '4px', fontSize: '12px', fontWeight: '600' },
  tableWrapper: { overflowX: 'auto' },
  table: { borderCollapse: 'collapse', width: '100%', fontSize: '13px' },
  th: {
    background: '#0d9488',
    color: 'white',
    padding: '10px 14px',
    textAlign: 'center',
    fontWeight: '600',
    fontSize: '13px',
  },
  timeCell: {
    padding: '8px 10px',
    fontWeight: '600',
    color: '#475569',
    background: '#f1f5f9',
    textAlign: 'center',
    borderBottom: '1px solid #e2e8f0',
    whiteSpace: 'nowrap',
  },
  cell: {
    padding: '10px',
    textAlign: 'center',
    borderBottom: '1px solid #e2e8f0',
    borderRight: '1px solid #e2e8f0',
    fontSize: '14px',
  },
};
