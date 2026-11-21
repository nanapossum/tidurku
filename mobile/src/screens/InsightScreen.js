import Screen from '../components/Screen';
import Card from '../components/Card';
import HeroCard from '../components/HeroCard';
import {useSleep} from '../context/SleepContext';
export default function InsightScreen({navigation}){
  const {account}=useSleep();
  const rows=account.sessions.filter(s=>s.notes||s.caffeine||s.screenMinutes||s.stress).sort((a,b)=>b.end-a.end).slice(0,7);
  return <Screen title="Wawasan tidur" onBack={navigation.goBack}>
    {rows.length<7?<Card title="Perlu 7 sesi dengan catatan faktor."/>:<>
      <HeroCard label="FAKTOR YANG TERCATAT" value={rows.length+' sesi'} detail="Sesi terbaru dengan catatan faktor"/>
      <Card title="Kafein" subtitle={rows.filter(s=>Number(s.caffeine)>0).length+' sesi dengan kafein'}/>
      <Card title="Waktu layar" subtitle={rows.filter(s=>Number(s.screenMinutes)>0).length+' sesi dengan waktu layar'}/>
      <Card title="Suhu malam" subtitle="Data suhu belum tersedia."/>
    </>}
  </Screen>;
}
