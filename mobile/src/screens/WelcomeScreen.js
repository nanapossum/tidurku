import { Image, Text, View, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import Button from '../components/Button';
import { COLORS } from '../theme/colors';
export default function WelcomeScreen({navigation}) {
  return <SafeAreaView style={{flex:1,backgroundColor:COLORS.background}}><StatusBar style="dark"/>
    <ScrollView contentContainerStyle={{flexGrow:1,justifyContent:'space-evenly',padding:24,gap:18}}>
      <Image source={require('../../assets/design/welcome.png')} resizeMode="contain" style={{width:'100%',height:undefined,aspectRatio:0.96,maxHeight:385}}/>
      <View style={{alignItems:'center',gap:6}}>
        <Text style={{fontFamily:'Nunito',fontSize:18,color:COLORS.muted}}>Selamat datang di</Text>
        <Text style={{fontFamily:'Nunito',fontSize:44,color:COLORS.text}}>TidurKu</Text>
        <Text style={{textAlign:'center',color:COLORS.muted,fontFamily:'Inter',lineHeight:23}}>Kenali pola tidurmu,{'\n'}satu malam demi satu malam.</Text>
      </View>
      <Button title="Mulai" onPress={()=>navigation.navigate('Login')}/>
    </ScrollView>
  </SafeAreaView>;
}
