import { useState,useEffect } from 'react';
import { View,Text,Image } from 'react-native';
import Screen from '../components/Screen';
import Button from '../components/Button';
import { clock } from './HomeScreen';
import { useSleep } from '../context/SleepContext';
export default function TrackerScreen({navigation,route}) {
  const {account}=useSleep(),[now,setNow]=useState(Date.now);
  const start=route.params?.start;
  useEffect(()=>{const timer=setInterval(()=>setNow(Date.now()),1000);return ()=>clearInterval(timer);},[]);
  const white={color:'white',fontFamily:'Nunito',textAlign:'center'};
  return <Screen background={require('../../assets/design/tracker.png')} tabs={!start}>
    <Text style={[white,{fontSize:22}]}>{start?'Pelacak tidur':'Catat tidur'}</Text>
    <Image source={require('../../assets/design/moon.png')} resizeMode="contain" style={{width:'88%',height:undefined,aspectRatio:1.1,alignSelf:'center',marginTop:20}}/>
    {start && <Text style={white}>●  SEDANG MELACAK</Text>}
    <Text style={[white,{fontSize:56}]}>{clock(now)}</Text>
    <Text style={white}>{new Date(now).toLocaleDateString('id-ID',{weekday:'long',day:'numeric',month:'long'})}</Text>
    {start ? <>
      <View style={{backgroundColor:'white',borderRadius:18,padding:16,flexDirection:'row',justifyContent:'space-around'}}>
        {[[clock(start),'Mulai sesi'],[Math.floor((now-start)/60000)+' m','Waktu berjalan'],[account.settings.targetHours+' j','Target tidur']].map(([value,label])=><View key={label} style={{alignItems:'center',gap:6}}><Text style={{fontFamily:'Nunito'}}>{value}</Text><Text style={{fontSize:11}}>{label}</Text></View>)}
      </View><Button variant="lavender" title="Akhiri sesi tidur" onPress={()=>{navigation.replace('SessionForm',{start,end:Date.now()});}}/>
    </>:<>
      <Text style={white}>Siap mulai sesi tidur?</Text>
      <Button title="Mulai tidur" variant="lavender" onPress={()=>{navigation.navigate('TrackerActive',{start:Date.now()});}}/>
      <Button title="Catat manual" variant="night" onPress={()=>navigation.navigate('SessionForm')}/>
    </>}
  </Screen>;
}
