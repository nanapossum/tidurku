const DATE = /^(\d{4})-(\d{2})-(\d{2})$/;
const TIME = /^(?:[01]\d|2[0-3]):[0-5]\d$/;

export function localDateValue(date) {
  return [date.getFullYear(), String(date.getMonth() + 1).padStart(2, '0'),
    String(date.getDate()).padStart(2, '0')].join('-');
}

export function parseDateTime(date, time) {
  const match = DATE.exec(date);
  if (!match || !TIME.test(time)) return null;
  const [, year, month, day] = match.map(Number);
  const [hours, minutes] = time.split(':').map(Number);
  const value = new Date(year, month - 1, day, hours, minutes);
  return localDateValue(value) === date && value.getHours() === hours && value.getMinutes() === minutes
    ? value.getTime()
    : null;
}

export function validateProfile({ name, age }) {
  const errors = {};
  if (name.trim().length < 2) errors.name = 'Nama minimal 2 karakter.';
  if (!/^\d{1,3}$/.test(age.trim()) || Number(age) < 10 || Number(age) > 120) {
    errors.age = 'Masukkan usia 10–120 tahun.';
  }
  return errors;
}

export function validateAccount(values, registering) {
  const errors = registering ? validateProfile(values) : {};
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.email.trim())) errors.email = 'Format email tidak valid.';
  if (values.password.length < 8 || !values.password.trim()) errors.password = 'Kata sandi minimal 8 karakter.';
  return errors;
}

export function validateSession(values, sessions) {
  const errors = {};
  const start = parseDateTime(values.startDate, values.startTime);
  const end = parseDateTime(values.endDate, values.endTime);

  if (parseDateTime(values.startDate, '12:00') === null) errors.startDate = 'Gunakan tanggal yang valid (YYYY-MM-DD).';
  if (parseDateTime(values.endDate, '12:00') === null) errors.endDate = 'Gunakan tanggal yang valid (YYYY-MM-DD).';
  if (!TIME.test(values.startTime) || (start === null && !errors.startDate)) errors.startTime = 'Gunakan jam yang valid (HH:mm).';
  if (!TIME.test(values.endTime) || (end === null && !errors.endDate)) errors.endTime = 'Gunakan jam yang valid (HH:mm).';

  if (start !== null && end !== null) {
    if (end <= start) errors.endTime = 'Waktu bangun harus setelah waktu tidur.';
    else if (end > Date.now()) errors.endTime = 'Waktu bangun belum terjadi.';
    else if (sessions.some((session) => start < session.end && end > session.start)) {
      errors.endTime = 'Waktunya bertumpang tindih dengan sesi lain.';
    }
  }
  if (values.quality && !/^[1-5]$/.test(values.quality)) errors.quality = 'Pilih kualitas tidur.';
  return errors;
}

export function validateSettings({ targetHours, bedtime }) {
  const errors = {};
  const hours = Number(targetHours.replace(',', '.'));
  if (!/^\d+(?:[.,]\d+)?$/.test(targetHours) || hours < 4 || hours > 12) {
    errors.targetHours = 'Masukkan target antara 4 dan 12 jam.';
  }
  if (!TIME.test(bedtime)) errors.bedtime = 'Gunakan format HH:mm, misalnya 22:30.';
  return errors;
}
