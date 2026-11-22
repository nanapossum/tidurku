import {NavigationContainer} from '@react-navigation/native';
import {createNativeStackNavigator} from '@react-navigation/native-stack';
import {createBottomTabNavigator} from '@react-navigation/bottom-tabs';
import TabBar from '../components/TabBar';
import WelcomeScreen from '../screens/WelcomeScreen';
import LoginScreen from '../screens/LoginScreen';
import HomeScreen from '../screens/HomeScreen';
import TrackerScreen from '../screens/TrackerScreen';
import TrackScreen from '../screens/TrackScreen';
import DetailScreen from '../screens/DetailScreen';
import ProfilScreen from '../screens/ProfilScreen';
import EditProfileScreen from '../screens/EditProfileScreen';
import GoalScreen from '../screens/GoalScreen';
import HistoryScreen from '../screens/HistoryScreen';
import InsightScreen from '../screens/InsightScreen';
import {useSleep} from '../context/SleepContext';
const Tab=createBottomTabNavigator(),Stack=createNativeStackNavigator();
function MainTabs(){
  return <Tab.Navigator initialRouteName="Dashboard" tabBar={props=><TabBar {...props}/>} screenOptions={{headerShown:false}}>
    <Tab.Screen name="Catat" component={TrackerScreen}/><Tab.Screen name="Dashboard" component={HomeScreen}/><Tab.Screen name="Profil" component={ProfilScreen}/>
  </Tab.Navigator>;
}
export default function AppNavigator(){
  const {account}=useSleep();
  return <NavigationContainer><Stack.Navigator screenOptions={{headerShown:false}}>
    {account?<>
      <Stack.Screen name="Main" component={MainTabs}/><Stack.Screen name="Detail" component={DetailScreen}/>
      <Stack.Screen name="TrackerActive" component={TrackerScreen}/>
      <Stack.Screen name="SessionForm" component={TrackScreen}/><Stack.Screen name="EditProfile" component={EditProfileScreen}/>
      <Stack.Screen name="EditTarget" component={GoalScreen}/><Stack.Screen name="Riwayat" component={HistoryScreen}/>
      <Stack.Screen name="Wawasan" component={InsightScreen}/>
    </>:<><Stack.Screen name="Welcome" component={WelcomeScreen}/><Stack.Screen name="Login" component={LoginScreen}/></>}
  </Stack.Navigator></NavigationContainer>;
}
