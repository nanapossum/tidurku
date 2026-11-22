import {useState} from 'react';
import {View,Text,Pressable} from 'react-native';
import {Feather} from '@expo/vector-icons';
import {WeekChart,monday,clock} from './HomeScreen';
import Screen from '../components/Screen';
import Card from '../components/Card';
import {useSleep} from '../context/SleepContext';
import {formatDuration,durationHours,formatDate,sleepScore} from '../utils/sleep';
import {COLORS} from '../theme/colors';
import {localDateValue} from '../utils/validators';

const sessionDate = new Intl.DateTimeFormat('id-ID', {weekday:'long',day:'numeric',month:'short'});

function WeeklyStat({label, value, detail}) {
  return <View style={{flex:1,minHeight:88,paddingHorizontal:14,paddingVertical:10,justifyContent:'space-between',backgroundColor:COLORS.card,borderRadius:18}}>
    <Text style={{fontFamily:'Nunito',fontSize:12,color:COLORS.muted}}>{label}</Text>
    <Text style={{fontFamily:'Nunito',fontSize:20,color:COLORS.primary}}>{value}</Text>
    <Text style={{fontFamily:'Inter',fontSize:11,color:COLORS.muted}}>{detail}</Text>
  </View>;
}

export default function HistoryScreen({navigation}){
  const {account}=useSleep(),[offset,setOffset]=useState(0);
  const start=monday(offset),end=monday(offset+1);
  const rows=account.sessions.filter(s=>s.end>=start && s.end<end).sort((a,b)=>b.end-a.end);
  const avg=fn=>rows.length?rows.reduce((n,s)=>n+fn(s),0)/rows.length:0;
  const hoursByDay = new Map();
  for (const session of rows) {
    const day = localDateValue(new Date(session.end));
    hoursByDay.set(day, (hoursByDay.get(day) || 0) + durationHours(session));
  }
  const daysOnTarget = [...hoursByDay.values()].filter(hours => hours >= account.settings.targetHours).length;
  return <Screen title="Riwayat tidur" subtitle={formatDate(start)+' – '+formatDate(end.getTime()-1)} onBack={navigation.goBack}>
    <View style={{flexDirection:'row',alignItems:'center',justifyContent:'space-around',backgroundColor:COLORS.surface,borderRadius:24}}>
      <Pressable accessibilityLabel="Minggu sebelumnya" onPress={()=>setOffset(offset-1)} style={{padding:12}}><Text>‹</Text></Pressable>
      <Text style={{color:COLORS.primary,fontFamily:'Nunito'}}>{offset===0?'Minggu ini':Math.abs(offset)+' minggu lalu'}</Text>
      <Pressable accessibilityLabel="Minggu berikutnya" disabled={!offset} onPress={()=>setOffset(offset+1)} style={{padding:12}}><Text>›</Text></Pressable>
    </View>
    <WeekChart sessions={rows} start={start} target={account.settings.targetHours}/>
    <View style={{flexDirection:'row',gap:12}}>
      <WeeklyStat label="Rata-rata durasi" value={formatDuration(avg(durationHours), {showZeroMinutes:true})} detail={rows.length+' sesi'}/>
      <WeeklyStat label="Rata-rata skor" value={Math.round(avg(s=>sleepScore(s,account.settings.targetHours)))+'/100'} detail={'Target tercapai '+daysOnTarget+' hari'}/>
    </View>
    <Text style={{fontFamily:'Nunito',fontSize:18}}>Sesi terbaru</Text>
    {rows.length===0 && <Card title="Belum ada sesi pada minggu yang dipilih."/>}
    {rows.map(session => (
      <Pressable key={session.id} accessibilityRole="button" accessibilityHint="Buka detail sesi"
        onPress={()=>navigation.navigate('Detail',{sessionId:session.id})}
        style={{flexDirection:'row',alignItems:'center',gap:8,minHeight:58,paddingHorizontal:16,paddingVertical:8,borderRadius:17,backgroundColor:COLORS.card}}>
        <View style={{flex:1,gap:3}}>
          <Text style={{fontFamily:'Nunito',fontSize:15,color:COLORS.text}}>{sessionDate.format(session.end)}</Text>
          <Text style={{fontFamily:'Inter',fontSize:12,color:COLORS.muted}}>
            {clock(session.start)} – {clock(session.end)} · {formatDuration(durationHours(session), {showZeroMinutes:true})}
          </Text>
        </View>
        <Text style={{fontFamily:'Nunito',fontSize:17,color:COLORS.primary}}>{sleepScore(session,account.settings.targetHours)}</Text>
        <Feather name="chevron-right" size={18} color={COLORS.muted}/>
      </Pressable>
    ))}
  </Screen>;
}
