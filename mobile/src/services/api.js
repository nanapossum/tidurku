import { Platform } from 'react-native';

// Set EXPO_PUBLIC_API_URL in mobile/.env when testing on a physical device.
const API_URL = (process.env.EXPO_PUBLIC_API_URL ||
  (Platform.OS === 'android' ? 'http://10.0.2.2:8080' : 'http://localhost:8080')).replace(/\/$/, '');

export async function api(path, { token, method = 'GET', body } = {}) {
  let response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      headers: {
        Accept: 'application/json',
        ...(body ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      ...(body ? { body: JSON.stringify(body) } : {}),
    });
  } catch {
    throw new Error(`Tidak dapat terhubung ke backend (${API_URL}). Periksa server dan alamat API.`);
  }

  if (response.status === 204) return null;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data?.detail;
    const message = typeof detail === 'string' ? detail
      : detail?.message || detail?.fields?.[0]?.message || data?.message;
    throw new Error(message || `Permintaan gagal (${response.status}).`);
  }
  return data;
}

export function sessionFromApi(item) {
  return {
    id: item.id,
    start: new Date(item.startAt).getTime(),
    end: new Date(item.endAt).getTime(),
    quality: item.quality,
    stress: item.stress || '',
    caffeine: item.caffeine ?? 0,
    screenMinutes: item.screenMinutes ?? 0,
    notes: item.notes || '',
    score: item.score,
  };
}
