/**
 * locationTracking.ts
 *
 * Handles:
 *  - Background GPS task (expo-task-manager)
 *  - Foreground hazard proximity checks with Haversine distance
 *  - Push token registration
 *  - Duplicate-notification prevention (per hazard, with cooldown)
 *  - Detailed logging for every step
 *
 * Bug fixes applied:
 *  #1 - Duplicate notification prevention via in-memory map + 10-min cooldown
 *  #2 - Token read from authStore.token (now populated)
 *  #3 - projectId read from Constants instead of hardcoded string
 *  #4 - push_service logic centralised here for foreground path
 *  #6 - Background task uses AsyncStorage token directly (no interceptor loop)
 */

import * as Location from 'expo-location';
import * as TaskManager from 'expo-task-manager';
import * as Device from 'expo-device';
import * as Constants from 'expo-constants';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import { useAuthStore } from '../store/authStore';

// ─── Constants ────────────────────────────────────────────────────────────────
const LOCATION_TASK_NAME = 'background-location-task';
const BASE_URL = 'http://10.0.2.2:8000';

/** How long (ms) before we allow a second notification for the same hazard */
const NOTIFICATION_COOLDOWN_MS = 10 * 60 * 1000; // 10 minutes

/**
 * In-memory map: hazardId → timestamp of last notification sent.
 * Resets when the app is killed (acceptable behaviour — user re-enters radius fresh).
 * For persistent dedup, back this with AsyncStorage.
 */
const lastNotifiedAt = new Map<string, number>();

// ─── Notifications (graceful degradation for Expo Go) ─────────────────────────
let Notifications: any = null;
try {
  Notifications = require('expo-notifications');
  if (Notifications) {
    Notifications.setNotificationHandler({
      handleNotification: async () => ({
        shouldShowAlert: true,
        shouldPlaySound: true,
        shouldSetBadge: false,
      }),
    });
    console.log('[HazardAlert] ✅ expo-notifications loaded');
  }
} catch (e) {
  console.log('[HazardAlert] ⚠️  expo-notifications not available (Expo Go Android SDK 53+).');
}

// ─── Haversine distance (metres) ─────────────────────────────────────────────
export function haversineDistance(
  lat1: number, lon1: number,
  lat2: number, lon2: number,
): number {
  const R = 6_371_000; // Earth radius in metres
  const φ1 = (lat1 * Math.PI) / 180;
  const φ2 = (lat2 * Math.PI) / 180;
  const Δφ = ((lat2 - lat1) * Math.PI) / 180;
  const Δλ = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(Δφ / 2) ** 2 +
    Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

// ─── Local notification (foreground fallback) ─────────────────────────────────
export async function sendLocalNotification(title: string, body: string, data?: object) {
  if (!Notifications) {
    console.log(`[HazardAlert] 🔔 (no-op) ${title}: ${body}`);
    return;
  }
  try {
    await Notifications.scheduleNotificationAsync({
      content: { title, body, data: data ?? {} },
      trigger: null, // immediate
    });
    console.log(`[HazardAlert] 🔔 Local notification sent: "${title}"`);
  } catch (e) {
    console.error('[HazardAlert] ❌ Failed to send local notification:', e);
  }
}

// ─── Dedup check ──────────────────────────────────────────────────────────────
function shouldNotify(hazardId: string): boolean {
  const lastTime = lastNotifiedAt.get(hazardId);
  if (lastTime === undefined) return true; // never notified
  const elapsed = Date.now() - lastTime;
  if (elapsed >= NOTIFICATION_COOLDOWN_MS) return true; // cooldown expired
  const remaining = Math.round((NOTIFICATION_COOLDOWN_MS - elapsed) / 1000);
  console.log(`[HazardAlert] ⏭️  Notification skipped (cooldown). Hazard ${hazardId} — ${remaining}s remaining`);
  return false;
}

function markNotified(hazardId: string) {
  lastNotifiedAt.set(hazardId, Date.now());
}

// ─── Foreground proximity check ───────────────────────────────────────────────
/**
 * Checks the user's current position against a list of hazards.
 * Sends local notifications for any hazards within the radius.
 * Returns a DebugState object for the debug screen.
 */
export interface ProximityResult {
  userLat: number;
  userLon: number;
  hazards: Array<{
    id: string;
    title: string;
    lat: number;
    lon: number;
    distanceM: number;
    insideRadius: boolean;
    notificationSent: boolean;
  }>;
  radiusMeters: number;
  checkedAt: Date;
}

export async function checkHazardProximity(
  userLat: number,
  userLon: number,
  hazards: Array<{ id: string; title: string; latitude: number; longitude: number }>,
  radiusMeters = 500,
): Promise<ProximityResult> {
  console.log(`[HazardAlert] 📍 User location updated: (${userLat.toFixed(6)}, ${userLon.toFixed(6)})`);
  console.log(`[HazardAlert] 🔍 Checking ${hazards.length} hazard(s) within ${radiusMeters}m`);

  const results: ProximityResult['hazards'] = [];

  for (const h of hazards) {
    const dist = haversineDistance(userLat, userLon, h.latitude, h.longitude);
    const inside = dist <= radiusMeters;

    console.log(
      `[HazardAlert] 📏 Hazard "${h.title}": ${Math.round(dist)}m away — ${inside ? '🟥 INSIDE' : '🟩 outside'} radius`
    );

    let notificationSent = false;

    if (inside) {
      if (shouldNotify(h.id)) {
        const distText = dist < 1000
          ? `${Math.round(dist)} metres`
          : `${(dist / 1000).toFixed(1)} km`;
        await sendLocalNotification(
          '⚠️ Hazard Alert',
          `${h.title} reported ${distText} ahead.`,
          { hazardId: h.id },
        );
        markNotified(h.id);
        notificationSent = true;
        console.log(`[HazardAlert] ✅ Notification sent for hazard "${h.title}" (${Math.round(dist)}m)`);
      }
    } else {
      // User exited radius — clear dedup so next entry fires again
      if (lastNotifiedAt.has(h.id)) {
        lastNotifiedAt.delete(h.id);
        console.log(`[HazardAlert] 🚶 Exited radius of hazard "${h.title}" — dedup cleared`);
      } else {
        console.log(`[HazardAlert] ⬜ Outside radius of hazard "${h.title}" — no action`);
      }
    }

    results.push({
      id: h.id,
      title: h.title,
      lat: h.latitude,
      lon: h.longitude,
      distanceM: Math.round(dist),
      insideRadius: inside,
      notificationSent,
    });
  }

  return { userLat, userLon, hazards: results, radiusMeters, checkedAt: new Date() };
}

// ─── Background Task Definition ───────────────────────────────────────────────
TaskManager.defineTask(LOCATION_TASK_NAME, async ({ data, error }) => {
  if (error) {
    console.error('[HazardAlert] ❌ Background task error:', error);
    return;
  }
  if (!data) return;

  const { locations } = data as { locations: Location.LocationObject[] };
  if (!locations?.length) return;

  const { latitude, longitude } = locations[0].coords;
  console.log(`[HazardAlert] 🌐 Background location: (${latitude.toFixed(6)}, ${longitude.toFixed(6)})`);

  try {
    // Read token directly from AsyncStorage — DO NOT use authStore here
    // because Zustand store state is not persisted in the background JS context.
    const token = await AsyncStorage.getItem('access_token');
    if (!token) {
      console.log('[HazardAlert] ⚠️  No auth token — skipping background update');
      return;
    }

    const resp = await axios.post(
      `${BASE_URL}/locations/update`,
      { latitude, longitude },
      { headers: { Authorization: `Bearer ${token}` }, timeout: 10_000 },
    );

    const { notifications_sent } = resp.data?.data ?? {};
    console.log(`[HazardAlert] ✅ Background update done. Notifications sent by backend: ${notifications_sent ?? 0}`);
  } catch (err: any) {
    console.error('[HazardAlert] ❌ Background location update failed:', err?.message ?? err);
  }
});

// ─── Permission + Tracking Start ─────────────────────────────────────────────
export const requestLocationPermissions = async (): Promise<boolean> => {
  console.log('[HazardAlert] 🔐 Requesting foreground location permission...');
  const { status: fg } = await Location.requestForegroundPermissionsAsync();
  if (fg !== 'granted') {
    console.log('[HazardAlert] ❌ Foreground permission denied');
    return false;
  }
  console.log('[HazardAlert] ✅ Foreground permission granted');

  console.log('[HazardAlert] 🔐 Requesting background location permission...');
  const { status: bg } = await Location.requestBackgroundPermissionsAsync();
  if (bg !== 'granted') {
    console.log('[HazardAlert] ⚠️  Background permission denied — foreground-only mode');
    return true; // Still allow foreground tracking
  }
  console.log('[HazardAlert] ✅ Background permission granted');

  const alreadyStarted = await Location.hasStartedLocationUpdatesAsync(LOCATION_TASK_NAME);
  if (!alreadyStarted) {
    await Location.startLocationUpdatesAsync(LOCATION_TASK_NAME, {
      accuracy: Location.Accuracy.Balanced,
      distanceInterval: 50,
      deferredUpdatesInterval: 60_000,
      showsBackgroundLocationIndicator: true,
    });
    console.log('[HazardAlert] 🚀 Background location task started');
  }
  return true;
};

export const stopLocationTracking = async () => {
  const started = await Location.hasStartedLocationUpdatesAsync(LOCATION_TASK_NAME);
  if (started) {
    await Location.stopLocationUpdatesAsync(LOCATION_TASK_NAME);
    console.log('[HazardAlert] 🛑 Background location task stopped');
  }
};

// ─── Push Token Registration ──────────────────────────────────────────────────
export async function registerForPushNotificationsAsync(): Promise<string | null> {
  if (!Notifications) {
    console.log('[HazardAlert] ⚠️  Notifications unavailable — skipping push token registration');
    return null;
  }

  if (!Device.isDevice) {
    console.log('[HazardAlert] ℹ️  Running on emulator — push tokens may not work in Expo Go.');
    // NOTE: Remove this return to allow testing on emulator builds.
    // On physical device (expo run:android), push tokens work fine.
  }

  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('hazard-alerts', {
      name: 'Hazard Alerts',
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#FF6B35',
      description: 'Nearby hazard proximity alerts',
    });
    console.log('[HazardAlert] ✅ Android notification channel configured');
  }

  const { status: existing } = await Notifications.getPermissionsAsync();
  let finalStatus = existing;
  if (existing !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }
  if (finalStatus !== 'granted') {
    console.log('[HazardAlert] ❌ Push notification permission denied');
    return null;
  }
  console.log('[HazardAlert] ✅ Push notification permission granted');

  try {
    // Bug #3 fix: read projectId from Constants instead of hardcoded string
    const projectId =
      Constants.default?.expoConfig?.extra?.eas?.projectId ??
      Constants.default?.easConfig?.projectId;

    if (!projectId) {
      console.warn('[HazardAlert] ⚠️  No EAS projectId found in app config — using undefined (dev mode)');
    }

    const { data: expoPushToken } = await Notifications.getExpoPushTokenAsync(
      projectId ? { projectId } : undefined,
    );
    console.log('[HazardAlert] 🎫 Expo push token obtained:', expoPushToken);

    const token = await AsyncStorage.getItem('access_token');
    if (token) {
      await axios.post(
        `${BASE_URL}/locations/push-token?push_token=${encodeURIComponent(expoPushToken)}`,
        {},
        { headers: { Authorization: `Bearer ${token}` }, timeout: 10_000 },
      );
      console.log('[HazardAlert] ✅ Push token registered with backend');
    }

    return expoPushToken;
  } catch (e) {
    console.error('[HazardAlert] ❌ Error registering push token:', e);
    return null;
  }
}
