import { useState } from 'react'
import Login from './components/Login'
import AvailabilityGrid from './components/AvailabilityGrid'
import LeaveApplication from './components/LeaveApplication'
import AdminLeaveManager from './components/AdminLeaveManager'
import CalendarView from './components/CalendarView'
import './App.css'

function App() {
  const [user, setUser] = useState(() => {
    const token = localStorage.getItem('token');
    const saved = localStorage.getItem('user');
    if (token && saved) {
      try { return JSON.parse(saved); } catch { return null; }
    }
    return null;
  });
  const [activeTab, setActiveTab] = useState('calendar');

  const handleLogin = (data) => {
    localStorage.setItem('user', JSON.stringify(data));
    setUser(data);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  if (!user) {
    return <Login onLogin={handleLogin} />;
  }

  const isAdmin = user.is_admin;
  const teacherTabs = [
    { id: 'calendar', label: '📅 Calendar', icon: '📅' },
    { id: 'availability', label: '📋 Availability', icon: '📋' },
    { id: 'leave', label: '📝 Leave', icon: '📝' },
  ];
  const adminTabs = [
    { id: 'leave-manage', label: '📋 Leave Management', icon: '📋' },
  ];
  const tabs = isAdmin ? adminTabs : teacherTabs;

  return (
    <div style={styles.app}>
      <header style={styles.header}>
        <div style={styles.headerLeft}>
          <h1 style={styles.logo}>📅 Smart Class Scheduler</h1>
        </div>
        <div style={styles.headerRight}>
          <span style={styles.userName}>
            {isAdmin ? '👤 Admin' : `👤 ${user.teacher_name}`}
          </span>
          <button style={styles.logoutBtn} onClick={handleLogout}>Logout</button>
        </div>
      </header>

      <nav style={styles.nav}>
        {tabs.map(tab => (
          <button
            key={tab.id}
            style={{
              ...styles.tab,
              ...(activeTab === tab.id ? styles.tabActive : {}),
            }}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <main style={styles.main}>
        {!isAdmin && activeTab === 'calendar' && (
          <CalendarView teacherId={user.teacher_id} isAdmin={false} />
        )}
        {!isAdmin && activeTab === 'availability' && (
          <AvailabilityGrid teacherId={user.teacher_id} />
        )}
        {!isAdmin && activeTab === 'leave' && (
          <LeaveApplication teacherId={user.teacher_id} />
        )}
        {isAdmin && activeTab === 'leave-manage' && (
          <AdminLeaveManager />
        )}
      </main>
    </div>
  );
}

const styles = {
  app: {
    minHeight: '100vh',
    background: '#f1f5f9',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
  header: {
    background: 'linear-gradient(135deg, #0f766e 0%, #115e59 100%)',
    padding: '14px 24px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    color: 'white',
  },
  headerLeft: {},
  headerRight: { display: 'flex', alignItems: 'center', gap: '12px' },
  logo: { margin: 0, fontSize: '18px', fontWeight: '700' },
  userName: { fontSize: '14px', opacity: 0.9 },
  logoutBtn: {
    background: 'rgba(255,255,255,0.15)',
    color: 'white',
    border: '1px solid rgba(255,255,255,0.3)',
    borderRadius: '6px',
    padding: '6px 14px',
    fontSize: '13px',
    cursor: 'pointer',
  },
  nav: {
    background: 'white',
    borderBottom: '1px solid #e2e8f0',
    padding: '0 24px',
    display: 'flex',
    gap: '2px',
  },
  tab: {
    padding: '12px 18px',
    border: 'none',
    background: 'none',
    fontSize: '14px',
    cursor: 'pointer',
    color: '#64748b',
    borderBottom: '2px solid transparent',
    fontWeight: '500',
  },
  tabActive: {
    color: '#0d9488',
    borderBottomColor: '#0d9488',
    fontWeight: '600',
  },
  main: {
    maxWidth: '1000px',
    margin: '24px auto',
    padding: '0 24px',
  },
};

export default App
