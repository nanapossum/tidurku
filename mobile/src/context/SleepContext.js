import { createContext, useContext, useState } from 'react';
import { DEFAULT_SETTINGS, DEMO_ACCOUNT, DUMMY_SESSIONS } from '../data/dummy';

const SleepContext = createContext(null);

export function SleepProvider({ children }) {
  const [activeEmail, setActiveEmail] = useState(null);
  const [accounts, setAccounts] = useState({
    [DEMO_ACCOUNT.email]: { ...DEMO_ACCOUNT, settings: DEFAULT_SETTINGS, sessions: DUMMY_SESSIONS },
  });
  const account = accounts[activeEmail];

  function login({ email, password }) {
    const normalizedEmail = email.trim().toLowerCase();
    if (accounts[normalizedEmail]?.password !== password) return false;
    setActiveEmail(normalizedEmail);
    return true;
  }

  function register(values) {
    const email = values.email.trim().toLowerCase();
    if (accounts[email]) return false;
    setAccounts((current) => ({
      ...current,
      [email]: {
        name: values.name.trim(), age: values.age.trim(), email, password: values.password,
        settings: DEFAULT_SETTINGS, sessions: [],
      },
    }));
    setActiveEmail(email);
    return true;
  }

  function updateAccount(update) {
    setAccounts((current) => ({
      ...current,
      [activeEmail]: { ...current[activeEmail], ...update(current[activeEmail]) },
    }));
  }

  return (
    <SleepContext.Provider value={{
      account, login, register,
      logout: () => setActiveEmail(null),
      saveSession: (session) => updateAccount(({ sessions }) => ({
        sessions: [...sessions.filter(item => item.id !== session.id), session],
      })),
      deleteSession: (id) => updateAccount(({sessions}) => ({sessions: sessions.filter(item => item.id !== id)})),
      saveSettings: (settings) => updateAccount(() => ({ settings })),
      saveProfile: (profile) => updateAccount(() => ({ name: profile.name.trim(), age: profile.age.trim() })),
    }}>
      {children}
    </SleepContext.Provider>
  );
}

export function useSleep() {
  return useContext(SleepContext);
}
