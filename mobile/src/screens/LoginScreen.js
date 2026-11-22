import { useState } from 'react';
import { View, Text, ScrollView, ImageBackground, Pressable, KeyboardAvoidingView, Platform } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { Ionicons } from '@expo/vector-icons';
import Button from '../components/Button';
import CustomInput from '../components/CustomInput';
import { useSleep } from '../context/SleepContext';
import useForm from '../hooks/useForm';
import { validateAccount } from '../utils/validators';
import { COLORS } from '../theme/colors';

export default function LoginScreen({navigation}) {
  const {login,register}=useSleep();
  const {top,bottom}=useSafeAreaInsets();
  const [registering,setRegistering]=useState(false);
  const [message,setMessage]=useState('');
  const [visible,setVisible]=useState(false);
  const form=useForm({name:'',age:'',email:'',password:''},values=>validateAccount(values,registering));
  const title=registering?'Buat akun':'Masuk';
  function switchMode() {setRegistering(!registering);setMessage('');setVisible(false);form.reset();}
  async function submit(values) {
    setMessage('');
    try {
      if (registering) await register(values);
      else await login(values);
    } catch (error) {
      setMessage(error.message);
    }
  }
  return <KeyboardAvoidingView style={{flex:1,backgroundColor:'white'}} behavior={Platform.OS==='ios'?'padding':undefined}>
    <StatusBar style="light"/>
    <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={{flexGrow:1,paddingBottom:bottom}}>
      <ImageBackground source={require('../../assets/design/auth.png')} resizeMode="stretch" style={{paddingTop:top+12,height:top+255,alignItems:'center'}}>
        <Pressable accessibilityLabel="Kembali" accessibilityRole="button" hitSlop={12} onPress={registering?switchMode:navigation.goBack} style={{position:'absolute',left:24,top:top+12}}><Ionicons name="arrow-back" color="white" size={22}/></Pressable>
        <Text style={{fontFamily:'Nunito',color:'white',fontSize:19}}>TidurKu</Text>

      </ImageBackground>
      <View style={{borderTopLeftRadius:32,borderTopRightRadius:32,marginTop:-18,backgroundColor:'white',padding:24,gap:12}}>
        <Text style={{fontFamily:'Nunito',fontSize:26,color:COLORS.text}}>{title}</Text>
        {!registering && <Text style={{fontFamily:'Inter',color:COLORS.muted}}>Lanjut lihat catatan dan pola tidurmu.</Text>}
        {message ? <Text accessibilityRole="alert" style={{backgroundColor:'#3E2B5A',color:'white',padding:12,borderRadius:12}}>{message}</Text>:null}
        {registering && <CustomInput label="Nama" placeholder="Nama lengkap" {...form.field('name')}/>}
        <CustomInput label="Email" placeholder="nama@contoh.id" autoCapitalize="none" keyboardType="email-address" {...form.field('email')}/>
        <View><CustomInput label="Kata sandi" placeholder="Masukkan kata sandi" secureTextEntry={!visible} {...form.field('password')}/>
          <Pressable accessibilityLabel="Tampilkan atau sembunyikan kata sandi" hitSlop={8} onPress={()=>setVisible(!visible)} style={{position:'absolute',right:12,top:35}}><Ionicons name={visible?'eye-off-outline':'eye-outline'} size={18} color={COLORS.muted}/></Pressable>
        </View>
        {registering && <CustomInput label="Usia" unit="tahun" placeholder="Contoh: 21" keyboardType="number-pad" {...form.field('age')}/>}
        <Button title={registering?'Daftar':'Masuk'} onPress={()=>form.submit(submit)}/>
        <Text accessibilityRole="button" onPress={switchMode} style={{textAlign:'center',padding:12,color:COLORS.primary,fontFamily:'Nunito'}}>{registering?'Sudah punya akun? Masuk':'Belum punya akun? Daftar'}</Text>
      </View>
    </ScrollView>
  </KeyboardAvoidingView>;
}
