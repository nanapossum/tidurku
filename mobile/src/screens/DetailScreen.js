import {useState} from 'react';
import {Alert,Modal,Text,View} from 'react-native';
import Card from '../components/Card';
import Button from '../components/Button';
import Screen from '../components/Screen';
import HeroCard from '../components/HeroCard';
import {useSleep} from '../context/SleepContext';
import {formatDuration,durationHours,formatDate,sleepScore} from '../utils/sleep';
import {clock} from './HomeScreen';
import {COLORS} from '../theme/colors';
export default function DetailScreen({navigation,route}){
  const {account,deleteSession}=useSleep(),[confirm,setConfirm]=useState(false);
  const session=account.sessions.find(s=>s.id===route.params.sessionId);
  if(!session)return <Screen title="Detail sesi" onBack={navigation.goBack}/>;
  const {start,end,quality,caffeine,screenMinutes,stress,notes}=session;
  return <Screen title="Detail sesi" subtitle={formatDate(end)} onBack={navigation.goBack}>
    <HeroCard label="DURASI TIDUR" value={formatDuration(durationHours(session))} detail={'Skor tidur · '+sleepScore(session,account.settings.targetHours)+' / 100'}/>
    <View style={{flexDirection:'row',gap:10}}>{[[start,'Mulai tidur'],[end,'Bangun']].map(([t,label])=><View key={label} style={{flex:1}}><Card title={label} subtitle={clock(t)+' · '+formatDate(t)}/></View>)}</View>
    <Card title="Kualitas tidur" subtitle={quality?quality+' / 5':'Belum diisi'}/>
    <Card title="Faktor sebelum tidur" subtitle={'Kafein · '+(caffeine||0)+' shot\nWaktu layar · '+(screenMinutes||0)+' menit\nTingkat stres · '+(stress||'—')}/>
    <Card title="Catatan" subtitle={notes||'—'}/>
    <Button title="Ubah sesi" onPress={()=>navigation.navigate('SessionForm',{sessionId:session.id})}/>
    <Button title="Hapus sesi" variant="danger" onPress={()=>setConfirm(true)}/>
    <Modal visible={confirm} transparent animationType="fade" onRequestClose={()=>setConfirm(false)}>
      <View style={{flex:1,backgroundColor:'#21153599',justifyContent:'flex-end'}}><View style={{backgroundColor:'white',borderRadius:24,padding:24,paddingBottom:40,gap:12}}>
        <Text style={{fontFamily:'Nunito',fontSize:22,color:COLORS.text}}>Hapus sesi tidur?</Text><Text>Ringkasan tidur akan diperbarui.</Text>
        <Card title={formatDate(end)} subtitle={clock(start)+' – '+clock(end)}/>
        <Button title="Hapus sesi" variant="danger" onPress={async()=>{try{await deleteSession(session.id);setConfirm(false);navigation.goBack();}catch(error){setConfirm(false);Alert.alert('Sesi belum terhapus',error.message);}}}/>
        <Button title="Batal" variant="outline" onPress={()=>setConfirm(false)}/>
      </View></View>
    </Modal>
  </Screen>;
}
