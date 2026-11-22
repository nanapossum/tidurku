import {useState} from 'react';
import {Pressable,Text,View,Alert,Modal,Platform} from 'react-native';
import DateTimePicker, {DateTimePickerAndroid} from '@react-native-community/datetimepicker';
import Screen from '../components/Screen';
import Button from '../components/Button';
import CustomInput from '../components/CustomInput';
import CategoryChips from '../components/CategoryChips';
import {useSleep} from '../context/SleepContext';
import useForm from '../hooks/useForm';
import {localDateValue,parseDateTime,validateSession} from '../utils/validators';
import {formatDuration} from '../utils/sleep';
import {clock} from './HomeScreen';
import {COLORS} from '../theme/colors';

export default function TrackScreen({navigation,route}){
  const {account,saveSession}=useSleep();
  const previous=account.sessions.find(s=>s.id===route.params?.sessionId);
  const tracking=!!route.params?.start;
  const end=previous?.end ?? route.params?.end ?? Date.now();
  const start=previous?.start ?? route.params?.start ?? end-8*3600000;
  const [editing,setEditing]=useState(null);
  const form=useForm({
    startDate:localDateValue(new Date(start)),startTime:clock(start),endDate:localDateValue(new Date(end)),endTime:clock(end),
    quality:String(previous?.quality||''),notes:previous?.notes||'',stress:previous?.stress||'',
    caffeine:String(previous?.caffeine||0),screenMinutes:String(previous?.screenMinutes||0),
  },v=>{
    const errors=validateSession(v,account.sessions.filter(s=>s.id!==previous?.id));
    for(const field of ['caffeine','screenMinutes'])if(!/^\d{1,4}$/.test(v[field]))errors[field]='Masukkan bilangan bulat 0–9999.';
    return errors;
  });
  const values=form.values;
  const from=parseDateTime(values.startDate,values.startTime),to=parseDateTime(values.endDate,values.endTime);
  const heading={fontFamily:'Nunito',fontSize:18,color:COLORS.text};
  function applySelection(key, mode, date) {
    if (mode === 'date') form.change(key+'Date', localDateValue(date));
    else form.change(key+'Time', clock(date));
  }
  function openPicker(key, mode) {
    const value = new Date(parseDateTime(values[key+'Date'], values[key+'Time']));
    if (Platform.OS === 'android') {
      DateTimePickerAndroid.open({
        value, mode, display: mode === 'date' ? 'calendar' : 'clock', is24Hour: true,
        onValueChange: (_, date) => applySelection(key, mode, date),
      });
    } else {
      setEditing({key, mode, value});
    }
  }
  async function save(v){
    try {
      await saveSession({id:previous?.id,start:from,end:to,quality:v.quality?Number(v.quality):null,
        stress:v.stress,notes:v.notes.trim(),caffeine:Number(v.caffeine),screenMinutes:Number(v.screenMinutes)});
      if(previous)navigation.goBack();
      else navigation.popTo('Main',{screen:'Dashboard'});
    } catch (error) {
      Alert.alert('Tidak dapat menyimpan sesi', error.message);
    }
  }
  return <Screen title={previous?'Ubah sesi':tracking?'Tinjau sesi tidur':'Catat manual'} onBack={navigation.goBack}
    subtitle={tracking?'Koreksi waktunya bila perlu sebelum menyimpan.':'Isi tanggal dan jam tidur serta bangun.'}>
    <View style={{flexDirection:'row',alignItems:'center',justifyContent:'space-between'}}>
      <Text style={heading}>Waktu sesi</Text><Text style={{color:COLORS.primary}}>{from!=null && to>from?'Durasi '+formatDuration((to-from)/3600000):'—'}</Text>
    </View>
    <View style={{flexDirection:'row',gap:10}}>{[['start','Mulai tidur'],['end','Bangun']].map(([key,label])=><View key={key} style={{flex:1,padding:14,borderRadius:16,backgroundColor:'white',borderWidth:1,borderColor:COLORS.border}}>
      <Text style={{color:COLORS.muted}}>{label}</Text>
      <Pressable accessibilityRole="button" accessibilityLabel={'Jam '+label+', '+values[key+'Time']} onPress={()=>openPicker(key,'time')} style={{minHeight:44,justifyContent:'center'}}>
        <Text style={{...heading,fontSize:26}}>{values[key+'Time']}</Text>
      </Pressable>
      <Pressable accessibilityRole="button" accessibilityLabel={'Tanggal '+label+', '+values[key+'Date']} onPress={()=>openPicker(key,'date')} style={{minHeight:44,justifyContent:'center'}}>
        <Text style={{color:COLORS.primary}}>{values[key+'Date']}</Text>
      </Pressable>
    </View>)}</View>
    {editing && <Modal visible transparent animationType="fade" onRequestClose={()=>setEditing(null)}>
      <View style={{flex:1,justifyContent:'center',padding:16,backgroundColor:'#21153599'}}>
        <View style={{backgroundColor:'white',borderRadius:20,padding:16,gap:10}}>
          <Text style={heading}>{editing.mode==='date'?'Tanggal':'Jam'} {editing.key==='start'?'mulai tidur':'bangun'}</Text>
          <DateTimePicker themeVariant="light" mode={editing.mode} value={editing.value} display={editing.mode==='date'?'inline':'spinner'}
            onValueChange={(_,value)=>setEditing(current=>current && {...current,value})}/>
          <Button title="Pilih" onPress={()=>{applySelection(editing.key,editing.mode,editing.value);setEditing(null);}}/>
          <Button title="Batal" variant="outline" onPress={()=>setEditing(null)}/>
        </View>
      </View>
    </Modal>}
    <Text style={{color:COLORS.muted,fontSize:12}}>Ketuk tanggal untuk membuka kalender atau jam untuk memilih waktu.</Text>
    {Object.keys(form.errors).some(k=>form.errors[k] && /Date|Time/.test(k)) && <Text accessibilityRole="alert" style={{color:COLORS.danger}}>{Object.entries(form.errors).find(([k,v])=>v && /Date|Time/.test(k))[1]}</Text>}
    <Text style={heading}>Kualitas tidur</Text><CategoryChips options={['1','2','3','4','5']} value={values.quality} onChange={v=>form.change('quality',v)}/>
    <View style={{flexDirection:'row',gap:8}}>
      <Text style={{flex:1,color:COLORS.muted,fontSize:12}}>1 · Sangat buruk</Text>
      <Text style={{flex:1,textAlign:'right',color:COLORS.muted,fontSize:12}}>5 · Sangat baik</Text>
    </View>
    <Text style={heading}>Faktor sebelum tidur</Text>
    <View style={{flexDirection:'row',gap:10}}>
      {[['caffeine','Kafein','shots'],['screenMinutes','Waktu layar','menit']].map(([key,label,unit])=>(
        <View key={key} style={{flex:1}}>
          <CustomInput label={label} unit={unit} keyboardType="number-pad" {...form.field(key)}/>
        </View>
      ))}
    </View>
    <Text>Tingkat stres</Text><CategoryChips options={['Rendah','Sedang','Tinggi']} value={values.stress} onChange={v=>form.change('stress',v)}/>
    <CustomInput label="Catatan" placeholder="Contoh: terbangun tengah malam" {...form.field('notes')}/>
    <Button title={previous?'Simpan perubahan':'Simpan sesi'} onPress={()=>form.submit(save)}/>
  </Screen>;
}
