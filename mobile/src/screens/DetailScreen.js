import { useState } from 'react';
import { Alert, Modal, StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import Button from '../components/Button';
import Screen from '../components/Screen';
import { useSleep } from '../context/SleepContext';
import { formatDuration, durationHours, sleepScore } from '../utils/sleep';
import { clock } from './HomeScreen';
import { COLORS } from '../theme/colors';

const fullDate = new Intl.DateTimeFormat('id-ID', { dateStyle: 'full' });
const shortDate = new Intl.DateTimeFormat('id-ID', { weekday: 'short', day: 'numeric', month: 'short' });
const sessionDate = new Intl.DateTimeFormat('id-ID', { day: 'numeric', month: 'long', year: 'numeric' });
const qualityLabels = ['', 'Sangat buruk', 'Buruk', 'Cukup', 'Baik', 'Sangat baik'];

function TimeCard({ label, time }) {
  return <View style={s.timeCard}>
    <Text style={s.caption}>{label}</Text>
    <Text style={s.time}>{clock(time)}</Text>
    <Text style={s.date}>{shortDate.format(time)}</Text>
  </View>;
}

export default function DetailScreen({ navigation, route }) {
  const { account, deleteSession } = useSleep();
  const [confirm, setConfirm] = useState(false);
  const session = account.sessions.find(item => item.id === route.params.sessionId);
  if (!session) return <Screen title="Detail sesi" onBack={navigation.goBack} />;

  const { start, end, quality, caffeine, screenMinutes, stress, notes } = session;
  const duration = formatDuration(durationHours(session));
  const factors = [
    ['Kafein', (caffeine ?? 0) + ' shot'],
    ['Waktu layar', (screenMinutes ?? 0) + ' menit'],
    ['Tingkat stres', stress || '—'],
  ];

  async function removeSession() {
    try {
      await deleteSession(session.id);
      setConfirm(false);
      navigation.goBack();
    } catch (error) {
      setConfirm(false);
      Alert.alert('Sesi belum terhapus', error.message);
    }
  }

  return <Screen title="Detail sesi" subtitle={fullDate.format(end)} onBack={navigation.goBack}>
    <View style={s.hero}>
      <View style={{ flex: 1, gap: 6 }}>
        <Text style={s.eyebrow}>DURASI TIDUR</Text>
        <Text style={s.duration}>{duration}</Text>
      </View>
      <View style={s.scoreBadge}>
        <Text style={s.caption}>Skor tidur</Text>
        <Text style={s.score}>{sleepScore(session, account.settings.targetHours)} / 100</Text>
      </View>
    </View>
    <View style={{ flexDirection: 'row', gap: 12 }}>
      <TimeCard label="Mulai tidur" time={start} />
      <TimeCard label="Bangun" time={end} />
    </View>
    <View style={[s.row, s.quality]}>
      <Text style={s.label}>Kualitas tidur</Text>
      <View style={s.rating}>
        {quality > 0 && <Feather name={quality >= 4 ? 'smile' : quality <= 2 ? 'frown' : 'meh'} size={20} color={COLORS.primary} />}
        <Text style={s.ratingText}>{quality ? quality + ' / 5 · ' + qualityLabels[quality] : 'Belum diisi'}</Text>
      </View>
    </View>
    <View style={{ gap: 8 }}>
      <Text style={s.heading}>Faktor sebelum tidur</Text>
      <View style={s.factors}>
        {factors.map(([label, value]) => <View key={label} style={s.row}>
          <Text style={s.body}>{label}</Text><Text style={s.value}>{value}</Text>
        </View>)}
        <View style={s.notes}>
          <Text style={s.caption}>Catatan</Text>
          <Text style={[s.body, { color: COLORS.text }]}>{notes || '—'}</Text>
        </View>
      </View>
    </View>
    <View style={{ gap: 11 }}>
      <Button title="Ubah sesi" onPress={() => navigation.navigate('SessionForm', { sessionId: session.id })} />
      <Button title="Hapus sesi" variant="danger" onPress={() => setConfirm(true)} />
    </View>
    <Modal visible={confirm} transparent animationType="fade" onRequestClose={() => setConfirm(false)}>
      <View style={s.overlay}><View style={s.sheet}>
        <View style={s.handle} />
        <Text style={[s.heading, { fontSize: 23 }]}>Hapus sesi tidur?</Text>
        <Text style={s.body}>Ringkasan tidur akan diperbarui.</Text>
        <View style={s.summary}>
          <Text style={s.value}>{sessionDate.formatRange?.(start, end) ?? sessionDate.format(end)}</Text>
          <Text style={s.date}>{clock(start)} – {clock(end)} · {duration}</Text>
        </View>
        <Button title="Hapus sesi" variant="destructive" onPress={removeSession} />
        <Button title="Batal" variant="outline" onPress={() => setConfirm(false)} />
      </View></View>
    </Modal>
  </Screen>;
}

const s = StyleSheet.create({
  hero: { flexDirection: 'row', alignItems: 'center', gap: 8, padding: 18, minHeight: 114, borderRadius: 21, overflow: 'hidden', backgroundColor: COLORS.hero,
    experimental_backgroundImage: 'linear-gradient(135deg, #1C103D 0%, #542184 68%, #6632BC 100%)' },
  eyebrow: { fontFamily: 'Nunito', color: COLORS.secondary, fontSize: 11 },
  duration: { color: 'white', fontFamily: 'Nunito', fontSize: 34 },
  scoreBadge: { minWidth: 107, minHeight: 57, padding: 6, alignItems: 'center', justifyContent: 'center', backgroundColor: 'white', borderRadius: 15, borderColor: COLORS.primary, borderWidth: 1.5 },
  score: { color: COLORS.primary, fontFamily: 'Nunito', fontSize: 17 },
  caption: { color: COLORS.muted, fontFamily: 'Nunito', fontSize: 12 },
  date: { color: COLORS.muted, fontFamily: 'Inter', fontSize: 12 },
  timeCard: { flex: 1, minHeight: 92, padding: 13, justifyContent: 'space-between', backgroundColor: 'white', borderRadius: 18, borderWidth: 1, borderColor: COLORS.border },
  time: { color: COLORS.text, fontFamily: 'Nunito', fontSize: 25 },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 8, flexWrap: 'wrap' },
  quality: { minHeight: 57, padding: 16, backgroundColor: COLORS.surface, borderRadius: 17 },
  label: { fontFamily: 'Nunito', fontSize: 15, color: COLORS.text },
  rating: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  ratingText: { fontFamily: 'Nunito', fontSize: 13, color: COLORS.primary },
  heading: { fontFamily: 'Nunito', fontSize: 17, color: COLORS.text },
  factors: { borderWidth: 1, borderColor: '#E7DDF1', backgroundColor: 'white', borderRadius: 19, padding: 15, gap: 10 },
  value: { fontFamily: 'Nunito', fontSize: 13, color: COLORS.text },
  body: { fontFamily: 'Inter', fontSize: 13, color: COLORS.muted },
  notes: { borderTopWidth: 1, borderColor: '#E7DDF1', paddingTop: 10, gap: 5 },
  overlay: { flex: 1, backgroundColor: '#21153599', justifyContent: 'flex-end', padding: 12 },
  sheet: { backgroundColor: 'white', borderRadius: 28, padding: 18, gap: 11 },
  handle: { width: 42, height: 4, borderRadius: 2, backgroundColor: COLORS.border, alignSelf: 'center', marginBottom: 6 },
  summary: { borderRadius: 15, backgroundColor: COLORS.surface, padding: 14, gap: 4 },
});
