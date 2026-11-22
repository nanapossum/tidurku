import Screen from '../components/Screen';
import TimeField from '../components/TimeField';
import {Alert,Text,View} from 'react-native';
import Button from '../components/Button';
import CustomInput from '../components/CustomInput';
import CategoryChips from '../components/CategoryChips';
import {useSleep} from '../context/SleepContext';
import {validateProfile} from '../utils/validators';
import useForm from '../hooks/useForm';
import {reminderTime} from './ProfilScreen';
import {COLORS} from '../theme/colors';
export default function EditProfileScreen({navigation}){
  const {account,saveProfile,saveSettings,logout}=useSleep();
  const modes=['30 menit','Pilih jam sendiri'];
  const form=useForm({name:account.name,age:account.age,mode:modes[Number(!!account.settings.customReminder)],time:reminderTime(account.settings)},v=>{
    const e=validateProfile(v);
    if(v.mode===modes[1]&&!/^([01]\d|2[0-3]):[0-5]\d$/.test(v.time))e.time='Gunakan format HH:mm.';
    return e;
  });
  const automatic = form.values.mode === modes[0];
  return <Screen title="Ubah profil" onBack={navigation.goBack}>
    <CustomInput label="Nama" {...form.field('name')}/><CustomInput label="Email" value={account.email} editable={false}/>
    <CustomInput label="Usia" unit="tahun" keyboardType="number-pad" {...form.field('age')}/>
    <CategoryChips options={modes} value={form.values.mode} onChange={mode=>form.change('mode',mode)}/>
    <View style={{gap:8}}>
      {automatic
        ? <CustomInput label="Jam pengingat" editable={false} unit="Otomatis" value={reminderTime({...account.settings,customReminder:false})}/>
        : <TimeField label="Jam pengingat" {...form.field('time')}/>}
      {automatic && <Text style={{fontFamily:'Inter',fontSize:12,color:COLORS.muted}}>Otomatis mengikuti jam tidur ideal, 30 menit lebih awal.</Text>}
    </View>
    <Button title="Simpan perubahan" onPress={()=>form.submit(async v=>{try{await saveProfile(v);await saveSettings({...account.settings,customReminder:v.mode===modes[1],reminderTime:v.time});navigation.goBack();}catch(error){Alert.alert('Perubahan belum tersimpan',error.message);}})}/>
    <Button title="Keluar dari akun" variant="danger" onPress={logout}/>
  </Screen>;
}
