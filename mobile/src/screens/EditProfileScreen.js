import Screen from '../components/Screen';
import Button from '../components/Button';
import CustomInput from '../components/CustomInput';
import CategoryChips from '../components/CategoryChips';
import {useSleep} from '../context/SleepContext';
import {validateProfile} from '../utils/validators';
import useForm from '../hooks/useForm';
import {reminderTime} from './ProfilScreen';
export default function EditProfileScreen({navigation}){
  const {account,saveProfile,saveSettings,logout}=useSleep();
  const modes=['30 mnt sebelum tidur','Pilih jam sendiri'];
  const form=useForm({name:account.name,age:account.age,mode:modes[Number(!!account.settings.customReminder)],time:reminderTime(account.settings)},v=>{
    const e=validateProfile(v);
    if(v.mode===modes[1]&&!/^([01]\d|2[0-3]):[0-5]\d$/.test(v.time))e.time='Gunakan format HH:mm.';
    return e;
  });
  return <Screen title="Ubah profil" onBack={navigation.goBack}>
    <CustomInput label="Nama" {...form.field('name')}/><CustomInput label="Email" value={account.email} editable={false}/>
    <CustomInput label="Usia" keyboardType="number-pad" {...form.field('age')}/>
    <CategoryChips options={modes} value={form.values.mode} onChange={m=>form.change('mode',m)}/>
    <CustomInput label="Jam pengingat" {...form.field('time')} editable={form.values.mode===modes[1]} value={form.values.mode===modes[1]?form.values.time:reminderTime({...account.settings,customReminder:false})}/>
    <Button title="Simpan perubahan" onPress={()=>form.submit(v=>{saveProfile(v);saveSettings({...account.settings,customReminder:v.mode===modes[1],reminderTime:v.time});navigation.goBack();})}/>
    <Button title="Keluar dari akun" variant="danger" onPress={logout}/>
  </Screen>;
}
