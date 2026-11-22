import {useState} from 'react';
import {Modal,Platform,Pressable,Text,View} from 'react-native';
import DateTimePicker, {DateTimePickerAndroid} from '@react-native-community/datetimepicker';
import Button from './Button';
import CustomInput from './CustomInput';
import {COLORS} from '../theme/colors';

export default function TimeField({label,value:time,onChangeText,error}) {
  const [draftTime,setDraftTime] = useState(null);
  function selectTime(date) {
    const time = [date.getHours(),date.getMinutes()].map(n=>String(n).padStart(2,'0')).join(':');
    onChangeText(time);
    setDraftTime(null);
  }
  function openClock() {
    const value = new Date();
    if (/^([01]\d|2[0-3]):[0-5]\d$/.test(time)) {
      const [hours,minutes] = time.split(':').map(Number);
      value.setHours(hours,minutes,0,0);
    }
    if (Platform.OS === 'android') {
      DateTimePickerAndroid.open({value,mode:'time',display:'clock',is24Hour:true,
        onValueChange:(_,date)=>selectTime(date)});
    } else {
      setDraftTime(value);
    }
  }
  return <>
    <Pressable accessibilityRole="button" accessibilityLabel={label+', '+time} onPress={openClock}>
      <View pointerEvents="none">
        <CustomInput label={label} value={time} error={error} editable={false}/>
      </View>
    </Pressable>
    {draftTime && <Modal visible transparent animationType="fade" onRequestClose={()=>setDraftTime(null)}>
      <View style={{flex:1,justifyContent:'center',padding:16,backgroundColor:'#21153599'}}>
        <View style={{backgroundColor:'white',borderRadius:20,padding:16,gap:10}}>
          <Text style={{fontFamily:'Nunito',fontSize:18,color:COLORS.text}}>{label}</Text>
          <DateTimePicker value={draftTime} mode="time" display="spinner" themeVariant="light"
            onValueChange={(_,date)=>setDraftTime(date)}/>
          <Button title="Pilih" onPress={()=>selectTime(draftTime)}/>
          <Button title="Batal" variant="outline" onPress={()=>setDraftTime(null)}/>
        </View>
      </View>
    </Modal>}
  </>;
}
