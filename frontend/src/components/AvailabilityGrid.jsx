import { useState, useEffect } from 'react';
import { api } from '../api';

const DAYS = ['MON', 'TUE', 'WED', 'THU', 'FRI'];
const DAY_LABELS = { MON: 'Monday', TUE: 'Tuesday', WED: 'Wednesday', THU: 'Thursday', FRI: 'Friday' };
const TIME_SLOTS = [
  '07:30-08:30', '08:30-09:30', '10:00-11:00', '11:00-12:00',
  '12:00-13:00', '13:00-14:00', '14:00-15:00', '15:00-16:00',
];

export default function AvailabilityGrid({ teacherId }) {
  const [unavailabilities, setUnavailabilities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadUnavailability();
  }, [teacherId]);

  const loadUnavailability = async () => {
    try {
      const data = await api.getUnavailability(teacherId);
      setUnavailabilities(data);
    } catch (err) {
      console.error('Failed to load availability:', err);
    } finally {
      setLoading(false);
    }
  };

  const isUnavailable = (day, slotIndex) => {
    return unavailabilities.some(u => u.day === day && u.slot_index === slotIndex);
  };

  const getUnavailabilityId = (day, slotIndex) => {
    const found = unavailabilities.find(u => u.day === day && u.slot_index === slotIndex);
    return found ? found.id : null;
  };

  const toggleSlot = async (day, slotIndex) => {
    setSaving(true);
    try {
      if (isUnavailable(day, slotIndex)) {
        const id = getUnavailabilityId(day, slotIndex);
        if (id) {
          await api.deleteUnavailability(id);
        }
      } else {
        await api.createUnavailability({
          teacher: teacherId,
          day,
          slot_index: slotIndex,
        });
      }
      await loadUnavailability();
    } catch (err) {
      alert('Error: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <p>Loading availability...</p>;

  return (
    <div>
      <h3 style={styles.heading}>📋 My Availability</h3>
      <p style={styles.hint}>
        Click cells to toggle availability. <span style={{...styles.badge, background: '#dcfce7', color: '#166534'}}>Green = Available</span>{' '}
        <span style={{...styles.badge, background: '#fee2e2', color: '#991b1b'}}>Red = Unavailable</span>
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
                  const unavail = isUnavailable(day, slotIdx);
                  return (
                    <td
                      key={day}
                      style={{
                        ...styles.cell,
                        background: unavail ? '#fee2e2' : '#dcfce7',
                        cursor: saving ? 'wait' : 'pointer',
                      }}
                      onClick={() => !saving && toggleSlot(day, slotIdx)}
                      title={unavail ? 'Unavailable - click to make available' : 'Available - click to mark unavailable'}
                    >
                      {unavail ? '✕' : '✓'}
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
  hint: { fontSize: '13px', color: '#64748b', margin: '0 0 12px 0' },
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
    fontWeight: '700',
    fontSize: '16px',
    transition: 'background 0.15s',
  },
};
