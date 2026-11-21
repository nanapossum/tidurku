import { useFonts } from 'expo-font';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { SleepProvider } from './src/context/SleepContext';
import AppNavigator from './src/navigation/AppNavigator';

export default function App() {
  const [loaded, error] = useFonts({
    Nunito: require('@expo-google-fonts/nunito/800ExtraBold/Nunito_800ExtraBold.ttf'),
    Inter: require('@expo-google-fonts/inter/400Regular/Inter_400Regular.ttf'),
  });
  if (!loaded && !error) return null;
  return (
    <SafeAreaProvider>
      <SleepProvider>
        <AppNavigator />
      </SleepProvider>
    </SafeAreaProvider>
  );
}
