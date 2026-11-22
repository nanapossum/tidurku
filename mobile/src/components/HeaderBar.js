import { Pressable,Text,View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../theme/colors';

export default function HeaderBar({ title, subtitle, onBack, light }) {
  const color=light ? '#FFFFFF' : COLORS.text;
  return <View style={{gap:8}}>
    <View style={{flexDirection:'row',alignItems:'center',gap:8}}>
      {onBack && <Pressable accessibilityRole="button" accessibilityLabel="Kembali" hitSlop={10} onPress={onBack}><Ionicons name="arrow-back" size={24} color={light ? color : COLORS.primary}/></Pressable>}
      <Text accessibilityRole="header" style={{color,fontFamily:'Nunito',fontSize:24}}>{title}</Text>
    </View>
    {subtitle && <Text style={{color: light ? color : COLORS.muted,fontFamily:'Inter',fontSize:13}}>{subtitle}</Text>}
  </View>;
}
