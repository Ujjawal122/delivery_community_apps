import * as Location from 'expo-location';
import * as TaskManager from 'expo-task-manager';
import * as Device from 'expo-device';
import { Platform } from 'react-native';
import axios from 'axios';
import { useAuthStore } from '../store/authStore';

const LOCATION_TASK_NAME = 'background-location-task';
let Notifications: any = null;
try {
  Notifications = require('expo-notifications');
  
  // Configure Notifications if successfully loaded
  if (Notifications) {
    Notifications.setNotificationHandler({
      handleNotification: async () => ({
        shouldShowAlert: true,
        shouldPlaySound: true,
        shouldSetBadge: false,
      }),
    });
  }
} catch (e) {
  console.log("expo-notifications is not supported in this environment (likely Expo Go Android SDK 53+).");
}

// Define the background task for location tracking
TaskManager.defineTask(LOCATION_TASK_NAME, async ({ data, error }) => {
  if (error) {
    console.error(error);
    return;
  }
  if (data) {
    const { locations } = data as { locations: Location.LocationObject[] };
    if (locations && locations.length > 0) {
      const location = locations[0];
      const { latitude, longitude } = location.coords;
      
      try {
        const token = useAuthStore.getState().token;
        if (token) {
          await axios.post('http://10.0.2.2:8000/locations/update', {
            latitude,
            longitude,
          }, {
            headers: {
              Authorization: `Bearer ${token}`
            }
          });
          // Note: Push notifications are triggered by the backend
        }
      } catch (err) {
        console.error('Failed to update background location:', err);
      }
    }
  }
});

export const requestLocationPermissions = async () => {
  const { status: foregroundStatus } = await Location.requestForegroundPermissionsAsync();
  if (foregroundStatus === 'granted') {
    const { status: backgroundStatus } = await Location.requestBackgroundPermissionsAsync();
    if (backgroundStatus === 'granted') {
      await Location.startLocationUpdatesAsync(LOCATION_TASK_NAME, {
        accuracy: Location.Accuracy.Balanced,
        distanceInterval: 50, // receive updates every 50 meters
        deferredUpdatesInterval: 1000 * 60, // Minimum time to wait between updates (1 minute)
        // iOS specific options
        showsBackgroundLocationIndicator: true,
      });
      return true;
    }
  }
  return false;
};

export const stopLocationTracking = async () => {
  const hasStarted = await Location.hasStartedLocationUpdatesAsync(LOCATION_TASK_NAME);
  if (hasStarted) {
    await Location.stopLocationUpdatesAsync(LOCATION_TASK_NAME);
  }
};

export async function registerForPushNotificationsAsync() {
  let token;

  if (!Notifications) {
    console.log("Notifications module is not available. Skipping push registration.");
    return null;
  }

  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('default', {
      name: 'default',
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#FF231F7C',
    });
  }

  if (Device.isDevice) {
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;
    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }
    if (finalStatus !== 'granted') {
      alert('Failed to get push token for push notification!');
      return;
    }
    try {
      const projectId = 'your-project-id'; // Normally Constants.expoConfig.extra.eas.projectId
      token = (await Notifications.getExpoPushTokenAsync({ projectId })).data;
      
      const authToken = useAuthStore.getState().token;
      if (authToken) {
        await axios.post(`http://10.0.2.2:8000/locations/push-token?push_token=${token}`, {}, {
            headers: {
              Authorization: `Bearer ${authToken}`
            }
        });
      }

    } catch (e) {
      console.error(e);
    }
  } else {
    alert('Must use physical device for Push Notifications');
  }

  return token;
}
