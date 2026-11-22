import { View, Text, Pressable } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../theme/colors';
const icons = { Catat:'moon-outline', Dashboard:'stats-chart', Profil:'person-outline' };
export default function TabBar({state,navigation}) {
  const {bottom}=useSafeAreaInsets();
  return <View style={{position:'absolute',bottom:Math.max(bottom,12),left:12,right:12,borderRadius:20,borderWidth:1,borderColor:COLORS.border,backgroundColor:'white',flexDirection:'row',paddingHorizontal:6}}>
    {state.routes.map((route,index)=>{
      const active=index===state.index, center=route.name==='Dashboard';
      return <Pressable key={route.key} accessibilityRole="tab" accessibilityState={{selected:active}} onPress={()=>navigation.navigate(route.name)}
        style={{flex:1,height:65,alignItems:'center',justifyContent:'flex-end',paddingBottom:8,gap:4}}>
        <View style={{alignItems:'center',justifyContent:'center',backgroundColor:active ? center ? COLORS.primary : COLORS.surface : center ? COLORS.surface : 'white',width:center?54:64,height:center?54:30,borderRadius:28,borderWidth:center?3:0,borderColor:'white'}}>
          <Ionicons name={icons[route.name]} size={21} color={active&&center ? 'white' : COLORS.primary}/>
        </View>
        <Text style={{fontFamily:'Nunito',fontSize:11,color:active?COLORS.primary:COLORS.muted}}>{route.name==='Catat'?'Catat Tidur':route.name}</Text>
      </Pressable>;
    })}
  </View>;
}
