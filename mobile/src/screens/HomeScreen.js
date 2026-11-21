import { useState } from 'react';
import { Text, View, Pressable } from 'react-native';
import { useSleep } from '../context/SleepContext';
import Screen from '../components/Screen';
import Button from '../components/Button';
import Card from '../components/Card';
import HeroCard from '../components/HeroCard';
import { COLORS } from '../theme/colors';
import { durationHours,formatDuration,sleepScore } from '../utils/sleep';
import { localDateValue } from '../utils/validators';

export const clock = t => new Date(t).toLocaleTimeString('id-ID',{hour:'2-digit',minute:'2-digit'}).replace('.',':');
export function WeekChart({ sessions, target, start, onHistory }) {
  const days=Array.from({length:7},(_,i)=>{
    const day=new Date(start);day.setDate(day.getDate()+i);
    const entries=sessions.filter(s=>localDateValue(new Date(s.end))===localDateValue(day));
    const score=entries.length?Math.round(entries.reduce((n,s)=>n+sleepScore(s,target),0)/entries.length):0;
    return {label:['Sen','Sel','Rab','Kam','Jum','Sab','Min'][i],score};
  });
  return <View style={{backgroundColor:'white',borderRadius:22,padding:16,gap:12}}>
    <View style={{flexDirection:'row',alignItems:'center',justifyContent:'space-between'}}>
      <Text style={{fontFamily:'Nunito',fontSize:17,color:COLORS.text}}>Skor mingguan</Text>
      {onHistory && <Text onPress={onHistory} accessibilityRole="button" style={{backgroundColor:COLORS.surface,borderRadius:14,padding:8,color:COLORS.primary,fontFamily:'Nunito',fontSize:12}}>Lihat riwayat ›</Text>}
    </View>
    <View style={{flexDirection:'row',justifyContent:'space-around'}}>{days.map(({label,score},i)=><View key={label} accessible accessibilityLabel={label+' '+score} style={{alignItems:'center',justifyContent:'flex-end',height:98,gap:6}}>
      <View style={{width:26,height:score*.76,borderRadius:7,backgroundColor:i===6?COLORS.primary:COLORS.secondary}}/>
      <Text style={{color:COLORS.muted,fontFamily:'Inter',fontSize:11}}>{label}</Text></View>)}</View>
  </View>;
}
export function monday(offset=0) {
  const day=new Date();day.setHours(0,0,0,0);day.setDate(day.getDate()-(day.getDay()+6)%7+offset*7);return day;
}
export default function HomeScreen({navigation}) {
  const {account}=useSleep();
  const [target,setTarget]=useState(false);
  const {targetHours,bedtime}=account.settings;
  const sessions=[...account.sessions].sort((a,b)=>b.end-a.end);
  const last=sessions[0];
  const dailyHours=new Map();
  for(const s of sessions){const day=localDateValue(new Date(s.end));dailyHours.set(day,(dailyHours.get(day)||0)+durationHours(s));}
  const debt=last && [0,1,2].every(offset=>{const d=new Date(last.end);d.setDate(d.getDate()-offset);const h=dailyHours.get(localDateValue(d));return h>0 && h<6;});
  return <Screen title="Dashboard" background={require('../../assets/design/night.png')} tabs>
    <View style={{flexDirection:'row',padding:4,borderRadius:24,backgroundColor:COLORS.surface}}>
      {['Ringkasan','Target & Rekomendasi'].map((label,i)=><Pressable key={label} accessibilityRole="tab" onPress={()=>setTarget(Boolean(i))}
        style={{flex:1,alignItems:'center',justifyContent:'center',minHeight:38,borderRadius:20,backgroundColor:target===Boolean(i)?COLORS.primary:COLORS.surface}}>
        <Text style={{fontFamily:'Nunito',fontSize:13,color:target===Boolean(i)?'white':COLORS.text}}>{label}</Text></Pressable>)}
    </View>
    {target ? <>
      <HeroCard label="TARGET DURASI TIDUR" value={targetHours+' jam'} detail={'Jam tidur ideal · '+bedtime}>
        <Button variant="outline" title="Ubah target" onPress={()=>navigation.navigate('EditTarget')}/>
      </HeroCard>
      <Card title="Untuk malam ini" subtitle={last && durationHours(last)<Number(targetHours)?'Coba bersiap tidur 30 menit lebih awal.':'Pertahankan jadwal tidur yang konsisten.'}/>
      <Button variant="outline" title="Lihat wawasan lingkungan" onPress={()=>navigation.navigate('Wawasan')}/>
    </> : last ? <>
      <Text style={{color:'white',fontFamily:'Inter'}}>{new Date(last.end).toLocaleDateString('id-ID',{weekday:'long',day:'numeric',month:'long'})}</Text>
      <HeroCard label="SKOR TIDUR TERAKHIR" value={sleepScore(last,targetHours)} suffix='/ 100' detail={formatDuration(durationHours(last))+' · '+clock(last.start)+' – '+clock(last.end)}/>
      <WeekChart sessions={sessions} target={targetHours} start={monday()} onHistory={()=>navigation.navigate('Riwayat')}/>
      {debt && <View style={{backgroundColor:'#FFE398',padding:18,borderRadius:18,gap:6}}><Text style={{fontFamily:'Nunito',color:'#613D08'}}>Utang tidur terdeteksi</Text><Text style={{color:'#613D08'}}>Tidur kurang dari 6 jam selama 3 malam berturut-turut.</Text></View>}
    </> : <>
      <HeroCard label="RINGKASAN" value="Belum ada sesi tidur" detail="Catat sesi pertamamu untuk melihat skor."/>
      <Button title="+ Catat tidur" onPress={()=>navigation.navigate('Catat')}/>
      <Card title="Kapan pola muncul?" subtitle="Skor tersedia setelah sesi pertama. TidurKu perlu minimal 3 sesi untuk melihat pola."/>
    </>}
  </Screen>;
}
