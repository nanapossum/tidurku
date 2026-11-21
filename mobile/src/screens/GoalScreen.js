import {Text} from 'react-native';
import Button from '../components/Button';
import CustomInput from '../components/CustomInput';
import Screen from '../components/Screen';
import {useSleep} from '../context/SleepContext';
import useForm from '../hooks/useForm';
import {validateSettings} from '../utils/validators';
export default function GoalScreen({navigation}){
  const {account,saveSettings}=useSleep();
  const form=useForm(account.settings,validateSettings);
  const hours=Number(form.values.targetHours.replace(',','.'));
  return <Screen title="Ubah target" subtitle="Sesuaikan durasi dan jam tidur ideal." onBack={navigation.goBack}>
    <CustomInput label="Durasi target (jam)" keyboardType="decimal-pad" {...form.field('targetHours')}/>
    {hours>0 && (hours<7||hours>9) && <Text style={{color:'#75500C',backgroundColor:'#FFF1CA',padding:8}}>{hours} jam di luar acuan 7–9 jam.</Text>}
    <CustomInput label="Jam tidur ideal" {...form.field('bedtime')}/>
    <Button title={'Simpan target '+form.values.targetHours+' jam'} onPress={()=>form.submit(v=>{saveSettings({...v,targetHours:v.targetHours.replace(',','.')});navigation.goBack();})}/>
    <Button variant="outline" title="Kembali" onPress={navigation.goBack}/>
  </Screen>;
}
