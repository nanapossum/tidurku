import { Pressable,Text } from 'react-native';
import { COLORS } from '../theme/colors';
const variants = {
  primary:[COLORS.primary,'white'], outline:[COLORS.surface,COLORS.primary],
  danger:['#FFE5F0',COLORS.danger], destructive:[COLORS.danger,'white'], lavender:[COLORS.secondary,COLORS.text], night:[COLORS.hero,'white'],
};
export default function Button({ title,onPress,variant='primary',disabled=false }) {
  const [backgroundColor,color]=variants[variant];
  return <Pressable accessibilityRole="button" disabled={disabled} onPress={onPress}
    style={({pressed})=>({backgroundColor,borderRadius:24,minHeight:48,paddingHorizontal:14,alignItems:'center',justifyContent:'center',opacity:(pressed || disabled) ? 0.65 : 1})}>
    <Text style={{color,fontFamily:'Nunito',fontSize:15}}>{title}</Text>
  </Pressable>;
}
