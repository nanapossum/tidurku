import { useEffect, useState } from 'react';
import Screen from '../components/Screen';
import Card from '../components/Card';
import HeroCard from '../components/HeroCard';
import { useSleep } from '../context/SleepContext';
import { api } from '../services/api';

const FACTOR_NAMES = { temperature: 'Suhu malam', caffeine: 'Kafein', screen: 'Waktu layar' };

export default function InsightScreen({ navigation }) {
  const { token } = useSleep();
  const [insight, setInsight] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    api('/api/insights/environment', { token })
      .then(value => { if (active) setInsight(value); })
      .catch(reason => { if (active) setError(reason.message); });
    return () => { active = false; };
  }, [token]);

  return <Screen title="Wawasan tidur" onBack={navigation.goBack}>
    {error ? <Card title="Wawasan belum dapat dimuat" subtitle={error}/> : !insight ? <Card title="Memuat wawasan…"/> : <>
      <HeroCard label="SESI YANG DIANALISIS" value={`${insight.sampleSize} sesi`} detail={`Minimal ${insight.minRequired} sesi untuk analisis`}/>
      {!insight.available && <Card title="Data belum cukup" subtitle={`Tambahkan catatan tidur sampai terkumpul ${insight.minRequired} sesi untuk melihat kecenderungan.`}/>}
      {insight.findings.map(finding => <Card key={finding.factor} title={FACTOR_NAMES[finding.factor] || finding.factor} subtitle={finding.message}/>)}
      <Card title="Tentang hasil ini" subtitle={insight.disclaimer}/>
    </>}
  </Screen>;
}
