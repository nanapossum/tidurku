export function durationHours({ start, end }) {
  return (end - start) / 3600000;
}

export function formatDuration(hours, { showZeroMinutes = false } = {}) {
  const minutes = Math.round(hours * 60);
  const remainder = minutes % 60;
  return remainder || showZeroMinutes ? `${Math.floor(minutes / 60)} j ${remainder} m` : `${minutes / 60} j`;
}

export function formatDate(timestamp) {
  return new Intl.DateTimeFormat('id-ID', { day: 'numeric', month: 'short' }).format(timestamp);
}

export function sleepScore(session, targetHours) {
  if (typeof session.score === 'number') return session.score;
  const durationScore = Math.min(durationHours(session) / Number(targetHours), 1);
  if (!session.quality) return Math.round(durationScore * 100);
  return Math.round(100 * (durationScore * 0.7 + session.quality / 5 * 0.3));
}
