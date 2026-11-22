export const DEMO_ACCOUNT = {
  name: 'Nara', email: 'demo@tidurku.test', password: 'TidurKu58', age: '21',
};

export const DEFAULT_SETTINGS = { targetHours: '8', bedtime: '22:30', reminder: true };

const now = new Date();

export const DUMMY_SESSIONS = [7.5, 7, 8, 6.5, 7.75, 8.25, 7].map((hours, index) => {
  const wake = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 7 + index, 7);
  return {
    id: String(index + 1),
    start: wake.getTime() - hours * 3600000,
    end: wake.getTime(),
    quality: index % 3 + 3,
    notes: index === 3 ? 'Minum kopi sore hari.' : '',
  };
});
