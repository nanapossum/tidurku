import {useState} from 'react';
import {View,Text,Pressable} from 'react-native';
import {WeekChart,monday,clock} from './HomeScreen';
import Screen from '../components/Screen';
import Card from '../components/Card';
import {useSleep} from '../context/SleepContext';
import {formatDuration,durationHours,formatDate,sleepScore} from '../utils/sleep';
import {COLORS} from '../theme/colors';
export default function HistoryScreen({navigation}){
  const {account}=useSleep(),[offset,setOffset]=useState(0);
  const start=monday(offset),end=monday(offset+1);
  const rows=account.sessions.filter(s=>s.end>=start && s.end<end).sort((a,b)=>b.end-a.end);
  const avg=fn=>rows.length?rows.reduce((n,s)=>n+fn(s),0)/rows.length:0;
  return <Screen title="Riwayat tidur" subtitle={formatDate(start)+' – '+formatDate(end.getTime()-1)} onBack={navigation.goBack}>
    <View style={{flexDirection:'row',alignItems:'center',justifyContent:'space-around',backgroundColor:COLORS.surface,borderRadius:24}}>
      <Pressable accessibilityLabel="Minggu sebelumnya" onPress={()=>setOffset(offset-1)} style={{padding:12}}><Text>‹</Text></Pressable>
      <Text style={{color:COLORS.primary,fontFamily:'Nunito'}}>{offset===0?'Minggu ini':Math.abs(offset)+' minggu lalu'}</Text>
      <Pressable accessibilityLabel="Minggu berikutnya" disabled={!offset} onPress={()=>setOffset(offset+1)} style={{padding:12}}><Text>›</Text></Pressable>
    </View>
    <WeekChart sessions={rows} start={start} target={account.settings.targetHours}/>
    <View style={{flexDirection:'row',gap:8}}><View style={{flex:1}}><Card title="Rata-rata durasi" subtitle={formatDuration(avg(durationHours))}/></View><View style={{flex:1}}><Card title="Rata-rata skor" subtitle={Math.round(avg(s=>sleepScore(s,account.settings.targetHours)))+'/100'}/></View></View>
    <Text style={{fontFamily:'Nunito',fontSize:18}}>Sesi terbaru</Text>
    {rows.length===0 && <Card title="Belum ada sesi pada minggu yang dipilih."/>}
    {rows.map(s=><Card key={s.id} title={formatDate(s.end)} subtitle={clock(s.start)+' – '+clock(s.end)+' · '+formatDuration(durationHours(s))} onPress={()=>navigation.navigate('Detail',{sessionId:s.id})}/>)}
  </Screen>;
}
