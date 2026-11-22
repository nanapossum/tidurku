import { Image, Text, View } from 'react-native';
import { COLORS } from '../theme/colors';
export default function HeroCard({ label, value, detail, children, suffix }) {
  return <View style={{backgroundColor:COLORS.hero,borderRadius:26,padding:18,minHeight:172,justifyContent:'space-between',gap:8,borderWidth:1,borderColor:'#8260B2'}}>
    <Image source={require('../../assets/design/planet.png')} resizeMode="contain" style={{position:'absolute',right:6,top:12,width:'42%',height:124}}/>
    <Text style={{fontFamily:'Nunito',fontSize:11,color:COLORS.accent}}>{label}</Text>
    <Text style={{color:'white',fontFamily:'Nunito',fontSize:40}}>{value}{suffix && <Text style={{fontSize:17,color:COLORS.secondary}}> {suffix}</Text>}</Text>
    <Text style={{color:'white',fontFamily:'Inter',fontSize:13}}>{detail}</Text>{children}
  </View>;
}
