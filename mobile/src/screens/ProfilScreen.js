import { Image,Text,View,Switch,Alert } from 'react-native';
import Screen from '../components/Screen';
import Button from '../components/Button';
import {useSleep} from '../context/SleepContext';
import {COLORS} from '../theme/colors';
export function reminderTime(settings){
  if(settings.customReminder)return settings.reminderTime;
  const [h,m]=settings.bedtime.split(':').map(Number),t=(h*60+m+1410)%1440;
  return [Math.floor(t/60),t%60].map(v=>String(v).padStart(2,'0')).join(':');
}
export default function ProfilScreen({navigation}){
  const {account,saveSettings}=useSleep();
  return <Screen title="Profil" background={require('../../assets/design/profile.png')} backgroundEdgeColors={['#352746', '#675572']} tabs>
    <View style={{backgroundColor:'white',borderRadius:26,overflow:'hidden'}}>
      <Image source={require('../../assets/design/avatar.png')} resizeMode="contain" style={{width:'100%',height:undefined,aspectRatio:480/278}}/>
      <View style={{padding:20,gap:10,alignItems:'center'}}>
        <Text style={{fontFamily:'Nunito',fontSize:25,color:COLORS.text}}>{account.name}</Text>
        <Text style={{color:COLORS.muted}}>{account.email}</Text>
        <Text style={{backgroundColor:COLORS.surface,color:COLORS.primary,borderRadius:12,padding:6}}>{account.age} tahun</Text>
        <View style={{alignSelf:'stretch'}}><Button title="Ubah profil" onPress={()=>navigation.navigate('EditProfile')}/></View>
      </View>
    </View>
    <View style={{backgroundColor:COLORS.surface,borderRadius:20,padding:18,flexDirection:'row',alignItems:'center',gap:10}}>
      <View style={{flex:1,gap:5}}><Text style={{fontFamily:'Nunito',fontSize:17}}>Pengingat tidur</Text>
      <Text style={{color:COLORS.muted}}>{account.settings.reminder?'Aktif · Setiap hari, '+reminderTime(account.settings):'Nonaktif'}</Text></View>
      <Switch accessibilityLabel="Pengingat tidur" value={account.settings.reminder} onValueChange={async reminder=>{try{await saveSettings({...account.settings,reminder});}catch(error){Alert.alert('Pengaturan belum tersimpan',error.message);}}}/>
    </View>
  </Screen>;
}
