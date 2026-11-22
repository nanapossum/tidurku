import { createContext, useContext, useState } from 'react';
import { api, sessionFromApi } from '../services/api';

const SleepContext = createContext(null);

function accountFromApi(user, goal, reminder, sessions) {
  return {
    id: user.id,
    name: user.name,
    age: String(user.age),
    city: user.city || '',
    email: user.email,
    settings: {
      targetHours: String(goal.targetHours),
      bedtime: goal.bedtime,
      reminder: reminder.enabled,
      customReminder: reminder.isCustom,
      reminderTime: reminder.time,
    },
    sessions: sessions.map(sessionFromApi),
  };
}

export function SleepProvider({ children }) {
  const [account, setAccount] = useState(null);
  const [token, setToken] = useState(null);

  async function loadAccount(accessToken) {
    const [user, goal, reminder, firstPage] = await Promise.all([
      api('/api/me', { token: accessToken }),
      api('/api/goal', { token: accessToken }),
      api('/api/reminders', { token: accessToken }),
      api('/api/sleep-sessions?limit=100', { token: accessToken }),
    ]);
    const remainingPages = await Promise.all(Array.from(
      { length: Math.ceil(Math.max(0, firstPage.total - firstPage.items.length) / 100) },
      (_, index) => api(`/api/sleep-sessions?limit=100&offset=${(index + 1) * 100}`, { token: accessToken }),
    ));
    const sessions = [...firstPage.items, ...remainingPages.flatMap(page => page.items)];
    setToken(accessToken);
    setAccount(accountFromApi(user, goal, reminder, sessions));
  }

  async function login({ email, password }) {
    const result = await api('/api/auth/login', { method: 'POST', body: { email: email.trim(), password } });
    await loadAccount(result.accessToken);
  }

  async function register(values) {
    const result = await api('/api/auth/register', {
      method: 'POST',
      body: { name: values.name.trim(), email: values.email.trim(), password: values.password, age: Number(values.age) },
    });
    await loadAccount(result.accessToken);
  }

  async function saveSession(session) {
    const body = {
      startAt: new Date(session.start).toISOString(),
      endAt: new Date(session.end).toISOString(),
      quality: session.quality,
      stress: session.stress || null,
      caffeine: Number(session.caffeine) || 0,
      screenMinutes: Number(session.screenMinutes) || 0,
      notes: session.notes?.trim() || null,
    };
    const saved = await api(session.id ? `/api/sleep-sessions/${session.id}` : '/api/sleep-sessions', {
      token, method: session.id ? 'PUT' : 'POST', body,
    });
    const mapped = sessionFromApi(saved);
    setAccount(current => ({ ...current, sessions: [mapped, ...current.sessions.filter(item => item.id !== mapped.id)].sort((a, b) => b.start - a.start) }));
    return mapped;
  }

  async function deleteSession(id) {
    await api(`/api/sleep-sessions/${id}`, { token, method: 'DELETE' });
    setAccount(current => ({ ...current, sessions: current.sessions.filter(item => item.id !== id) }));
  }

  async function saveSettings(settings) {
    const [goal, reminder] = await Promise.all([
      api('/api/goal', { token, method: 'PUT', body: {
        targetHours: Number(String(settings.targetHours).replace(',', '.')),
        bedtime: settings.bedtime,
        confirmOutOfRange: true,
      } }),
      api('/api/reminders', { token, method: 'PUT', body: {
        enabled: Boolean(settings.reminder),
        time: settings.customReminder ? settings.reminderTime : null,
      } }),
    ]);
    setAccount(current => ({ ...current, settings: {
      targetHours: String(goal.targetHours), bedtime: goal.bedtime,
      reminder: reminder.enabled, customReminder: reminder.isCustom, reminderTime: reminder.time,
    } }));
  }

  async function saveProfile(profile) {
    const user = await api('/api/me', { token, method: 'PATCH', body: { name: profile.name.trim(), age: Number(profile.age) } });
    setAccount(current => ({ ...current, name: user.name, age: String(user.age), city: user.city || '' }));
  }

  function logout() {
    setAccount(null);
    setToken(null);
  }

  return (
    <SleepContext.Provider value={{ account, token, login, register, logout, saveSession, deleteSession, saveSettings, saveProfile }}>
      {children}
    </SleepContext.Provider>
  );
}

export function useSleep() {
  return useContext(SleepContext);
}
