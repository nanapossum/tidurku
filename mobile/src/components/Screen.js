import { ImageBackground, KeyboardAvoidingView, Platform, ScrollView, StyleSheet, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import HeaderBar from './HeaderBar';
import { COLORS } from '../theme/colors';

export default function Screen({ title, subtitle, onBack, background, backgroundEdgeColors, children, tabs = false }) {
  const { top, bottom } = useSafeAreaInsets();
  return <View style={{flex:1,backgroundColor:COLORS.background}}>
    {background && <View pointerEvents="none" style={StyleSheet.absoluteFill}>
      {backgroundEdgeColors?.map((color, index) => (
        <View key={index} style={{flex:1,backgroundColor:color}} />
      ))}
      <ImageBackground source={background} resizeMode="stretch" style={StyleSheet.absoluteFill} />
    </View>}
    <StatusBar style={background ? 'light' : 'dark'} />
    <KeyboardAvoidingView style={{flex:1,paddingTop:top}} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={{padding:24,gap:16,width:'100%',maxWidth:600,alignSelf:'center',paddingBottom:tabs ? bottom+110 : bottom+24}}>
        {title && <HeaderBar title={title} subtitle={subtitle} onBack={onBack} light={!!background} />}
        {children}
      </ScrollView>
    </KeyboardAvoidingView>
  </View>;
}
