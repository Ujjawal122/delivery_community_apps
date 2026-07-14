/**
 * HazardDebugScreen.tsx
 *
 * Developer-only screen for:
 *  - Simulating user movement without physically moving
 *  - Real-time distance display to every hazard
 *  - Inside/outside radius indicator
 *  - Notification trigger simulation (fires exactly as production)
 *  - Detailed log of every event
 *  - Configurable radius slider
 *
 * Access: Add a tab or deep-link to this screen in dev builds only.
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Switch,
  StyleSheet,
  Alert,
  Dimensions,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withRepeat,
  withSequence,
  withTiming,
  FadeInDown,
} from 'react-native-reanimated';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { haversineDistance, checkHazardProximity, ProximityResult } from '../../services/locationTracking';
import { useTheme } from '../../constants/theme';

const BASE_URL = 'http://10.0.2.2:8000';
const { width } = Dimensions.get('window');

// ── Types ────────────────────────────────────────────────────────────────────
interface LogEntry {
  id: number;
  time: string;
  level: 'info' | 'warn' | 'error' | 'success';
  message: string;
}

interface SimHazard {
  id: string;
  title: string;
  latitude: number;
  longitude: number;
}

// ── Log colours ──────────────────────────────────────────────────────────────
const LOG_COLORS = {
  info:    '#60A5FA',
  warn:    '#FBBF24',
  error:   '#EF4444',
  success: '#34D399',
};

const LOG_ICONS = {
  info:    'information-circle-outline',
  warn:    'warning-outline',
  error:   'close-circle-outline',
  success: 'checkmark-circle-outline',
};

// ── Animated pulsing dot ─────────────────────────────────────────────────────
function PulseDot({ inside }: { inside: boolean }) {
  const scale = useSharedValue(1);
  useEffect(() => {
    if (inside) {
      scale.value = withRepeat(
        withSequence(withTiming(1.4, { duration: 600 }), withTiming(1, { duration: 600 })),
        -1, false,
      );
    } else {
      scale.value = withTiming(1);
    }
  }, [inside]);

  const style = useAnimatedStyle(() => ({ transform: [{ scale: scale.value }] }));
  return (
    <Animated.View
      style={[
        styles.pulseDot,
        { backgroundColor: inside ? '#EF4444' : '#34D399' },
        style,
      ]}
    />
  );
}

// ── Main Screen ──────────────────────────────────────────────────────────────
export default function HazardDebugScreen() {
  const theme = useTheme();

  // Simulated user position
  const [simLat, setSimLat] = useState('');
  const [simLon, setSimLon] = useState('');
  const [radius, setRadius] = useState('500');
  const [autoMove, setAutoMove] = useState(false);
  const [autoStep, setAutoStep] = useState('0.0005'); // ~55m per step

  // Real location
  const [useRealGPS, setUseRealGPS] = useState(false);

  // Hazards from backend
  const [hazards, setHazards] = useState<SimHazard[]>([]);
  const [loadingHazards, setLoadingHazards] = useState(false);

  // Last proximity result
  const [result, setResult] = useState<ProximityResult | null>(null);

  // Logs
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const logIdRef = useRef(0);
  const scrollRef = useRef<ScrollView>(null);

  // Auto-movement timer
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ── Logging helper ──────────────────────────────────────────────────────────
  const log = useCallback((message: string, level: LogEntry['level'] = 'info') => {
    const now = new Date();
    const time = `${now.getHours().toString().padStart(2,'0')}:${now.getMinutes().toString().padStart(2,'0')}:${now.getSeconds().toString().padStart(2,'0')}`;
    setLogs(prev => {
      const next = [...prev, { id: logIdRef.current++, time, level, message }];
      return next.slice(-100); // keep last 100 entries
    });
    setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 50);
  }, []);

  // ── Fetch hazards ───────────────────────────────────────────────────────────
  const fetchHazards = useCallback(async () => {
    setLoadingHazards(true);
    log('Fetching hazards from backend...');
    try {
      const token = await AsyncStorage.getItem('access_token');
      const resp = await axios.get(`${BASE_URL}/hazards`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        timeout: 8000,
      });
      const raw = resp.data?.data ?? [];
      const mapped: SimHazard[] = raw.map((h: any) => ({
        id: h.id,
        title: h.title,
        latitude: h.latitude ?? 0,
        longitude: h.longitude ?? 0,
      })).filter((h: SimHazard) => h.latitude !== 0);
      setHazards(mapped);
      log(`✅ Loaded ${mapped.length} hazard(s)`, 'success');
    } catch (e: any) {
      log(`❌ Failed to fetch hazards: ${e?.message}`, 'error');
    } finally {
      setLoadingHazards(false);
    }
  }, [log]);

  useEffect(() => { fetchHazards(); }, []);

  // ── Run proximity check ─────────────────────────────────────────────────────
  const runCheck = useCallback(async (lat: number, lon: number) => {
    const r = parseFloat(radius) || 500;
    log(`▶ Running proximity check at (${lat.toFixed(6)}, ${lon.toFixed(6)}) radius=${r}m`);
    try {
      const res = await checkHazardProximity(lat, lon, hazards, r);
      setResult(res);

      const inside = res.hazards.filter(h => h.insideRadius);
      const notified = res.hazards.filter(h => h.notificationSent);

      if (inside.length === 0) {
        log(`🟩 Outside all hazard radii`, 'info');
      } else {
        inside.forEach(h => {
          log(
            `🟥 INSIDE radius of "${h.title}" — ${h.distanceM}m`,
            'warn',
          );
        });
      }

      notified.forEach(h => {
        log(`🔔 Notification triggered for "${h.title}"`, 'success');
      });

      const skipped = inside.filter(h => !h.notificationSent);
      skipped.forEach(h => {
        log(`⏭️ Notification skipped (cooldown) for "${h.title}"`, 'warn');
      });

    } catch (e: any) {
      log(`❌ Proximity check error: ${e?.message}`, 'error');
    }
  }, [hazards, radius, log]);

  // ── Manual check ───────────────────────────────────────────────────────────
  const handleManualCheck = useCallback(() => {
    const lat = parseFloat(simLat);
    const lon = parseFloat(simLon);
    if (isNaN(lat) || isNaN(lon)) {
      Alert.alert('Invalid', 'Enter valid latitude and longitude');
      return;
    }
    runCheck(lat, lon);
  }, [simLat, simLon, runCheck]);

  // ── Seed coordinates from first hazard ─────────────────────────────────────
  const seedFromHazard = useCallback((h: SimHazard) => {
    // Place user 600m north of the hazard (outside radius)
    const offsetLat = h.latitude + (600 / 111_000);
    setSimLat(offsetLat.toFixed(6));
    setSimLon(h.longitude.toFixed(6));
    log(`📌 Seeded user 600m north of "${h.title}"`, 'info');
  }, [log]);

  // ── Auto-movement: step toward hazard every second ─────────────────────────
  useEffect(() => {
    if (!autoMove) {
      if (timerRef.current) clearInterval(timerRef.current);
      return;
    }
    const step = parseFloat(autoStep) || 0.0005;
    log(`🚶 Auto-move started (step=${step}°/s ≈ ${Math.round(step * 111_000)}m/s)`, 'info');

    timerRef.current = setInterval(() => {
      setSimLat(prev => {
        const next = parseFloat(prev) - step; // move south (toward lower lat)
        runCheck(next, parseFloat(simLon) || 0);
        return next.toFixed(6);
      });
    }, 1000);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [autoMove, autoStep, simLon, runCheck, log]);

  // ── Use real GPS ────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!useRealGPS) return;
    let sub: Location.LocationSubscription | null = null;
    (async () => {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        log('❌ GPS permission denied', 'error');
        setUseRealGPS(false);
        return;
      }
      log('📡 Real GPS mode active', 'success');
      sub = await Location.watchPositionAsync(
        { accuracy: Location.Accuracy.High, timeInterval: 2000, distanceInterval: 5 },
        (loc) => {
          const { latitude, longitude } = loc.coords;
          setSimLat(latitude.toFixed(6));
          setSimLon(longitude.toFixed(6));
          runCheck(latitude, longitude);
        },
      );
    })();
    return () => { sub?.remove(); };
  }, [useRealGPS]);

  // ── Render ─────────────────────────────────────────────────────────────────
  const checkedLat = parseFloat(simLat) || 0;
  const checkedLon = parseFloat(simLon) || 0;
  const anyInside = result?.hazards.some(h => h.insideRadius) ?? false;

  return (
    <SafeAreaView style={[styles.root, { backgroundColor: theme.bg }]}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 40 }}>

        {/* Header */}
        <Animated.View entering={FadeInDown.duration(400)} style={[styles.header, { backgroundColor: theme.bgCard, borderBottomColor: theme.border }]}>
          <View style={styles.headerLeft}>
            <View style={[styles.devBadge, { backgroundColor: '#7C3AED20' }]}>
              <Text style={[styles.devBadgeText, { color: '#7C3AED' }]}>DEV ONLY</Text>
            </View>
            <Text style={[styles.title, { color: theme.textPrimary }]}>Hazard Debug</Text>
          </View>
          <PulseDot inside={anyInside} />
        </Animated.View>

        {/* Status Card */}
        {result && (
          <Animated.View entering={FadeInDown.delay(100).duration(400)} style={[styles.card, { backgroundColor: theme.bgCard, borderColor: theme.border }]}>
            <Text style={[styles.cardTitle, { color: theme.textPrimary }]}>Live Status</Text>
            <Row label="User Location" value={`${simLat}, ${simLon}`} color={theme.textPrimary} />
            <Row label="Radius" value={`${radius}m`} color={theme.accent} />
            <Row label="Hazards checked" value={`${result.hazards.length}`} color={theme.textPrimary} />
            <Row label="Inside radius" value={anyInside ? '🟥 YES' : '🟩 NO'} color={anyInside ? '#EF4444' : '#34D399'} />
            <Row label="Last checked" value={result.checkedAt.toLocaleTimeString()} color={theme.textMuted} />
          </Animated.View>
        )}

        {/* Coordinate Input */}
        <Animated.View entering={FadeInDown.delay(150).duration(400)} style={[styles.card, { backgroundColor: theme.bgCard, borderColor: theme.border }]}>
          <Text style={[styles.cardTitle, { color: theme.textPrimary }]}>Simulate User Location</Text>

          <View style={styles.row}>
            <View style={{ flex: 1 }}>
              <Text style={[styles.label, { color: theme.textSecondary }]}>Latitude</Text>
              <TextInput
                style={[styles.input, { backgroundColor: theme.bgSubtle, color: theme.textPrimary, borderColor: theme.border }]}
                value={simLat}
                onChangeText={setSimLat}
                keyboardType="numeric"
                placeholder="e.g. 12.971599"
                placeholderTextColor={theme.textMuted}
              />
            </View>
            <View style={{ width: 12 }} />
            <View style={{ flex: 1 }}>
              <Text style={[styles.label, { color: theme.textSecondary }]}>Longitude</Text>
              <TextInput
                style={[styles.input, { backgroundColor: theme.bgSubtle, color: theme.textPrimary, borderColor: theme.border }]}
                value={simLon}
                onChangeText={setSimLon}
                keyboardType="numeric"
                placeholder="e.g. 77.594566"
                placeholderTextColor={theme.textMuted}
              />
            </View>
          </View>

          <View style={styles.row}>
            <View style={{ flex: 1 }}>
              <Text style={[styles.label, { color: theme.textSecondary }]}>Radius (metres)</Text>
              <TextInput
                style={[styles.input, { backgroundColor: theme.bgSubtle, color: theme.textPrimary, borderColor: theme.border }]}
                value={radius}
                onChangeText={setRadius}
                keyboardType="numeric"
                placeholder="500"
                placeholderTextColor={theme.textMuted}
              />
            </View>
            <View style={{ width: 12 }} />
            <View style={{ flex: 1 }}>
              <Text style={[styles.label, { color: theme.textSecondary }]}>Step size (°)</Text>
              <TextInput
                style={[styles.input, { backgroundColor: theme.bgSubtle, color: theme.textPrimary, borderColor: theme.border }]}
                value={autoStep}
                onChangeText={setAutoStep}
                keyboardType="numeric"
                placeholder="0.0005"
                placeholderTextColor={theme.textMuted}
              />
            </View>
          </View>

          <TouchableOpacity
            style={[styles.btn, { backgroundColor: theme.accent }]}
            onPress={handleManualCheck}
          >
            <Ionicons name="locate" size={18} color="#fff" />
            <Text style={styles.btnText}>Run Proximity Check</Text>
          </TouchableOpacity>
        </Animated.View>

        {/* Toggles */}
        <Animated.View entering={FadeInDown.delay(200).duration(400)} style={[styles.card, { backgroundColor: theme.bgCard, borderColor: theme.border }]}>
          <Text style={[styles.cardTitle, { color: theme.textPrimary }]}>Controls</Text>

          <ToggleRow
            label="Auto-Move (1 step/sec southward)"
            icon="walk-outline"
            value={autoMove}
            onChange={setAutoMove}
            theme={theme}
          />
          <ToggleRow
            label="Use Real GPS"
            icon="navigate-outline"
            value={useRealGPS}
            onChange={setUseRealGPS}
            theme={theme}
          />
        </Animated.View>

        {/* Hazard List */}
        <Animated.View entering={FadeInDown.delay(250).duration(400)} style={[styles.card, { backgroundColor: theme.bgCard, borderColor: theme.border }]}>
          <View style={styles.cardHeader}>
            <Text style={[styles.cardTitle, { color: theme.textPrimary }]}>Hazards ({hazards.length})</Text>
            <TouchableOpacity onPress={fetchHazards} style={[styles.refreshBtn, { backgroundColor: theme.bgSubtle }]}>
              <Ionicons name="refresh" size={16} color={theme.accent} />
            </TouchableOpacity>
          </View>

          {hazards.map(h => {
            const resultH = result?.hazards.find(r => r.id === h.id);
            const dist = resultH?.distanceM ?? (checkedLat && checkedLon ? Math.round(haversineDistance(checkedLat, checkedLon, h.latitude, h.longitude)) : null);
            const inside = resultH?.insideRadius ?? false;

            return (
              <TouchableOpacity
                key={h.id}
                style={[styles.hazardRow, { borderColor: inside ? '#EF444440' : theme.border, backgroundColor: inside ? '#EF444408' : 'transparent' }]}
                onPress={() => seedFromHazard(h)}
              >
                <View style={[styles.hazardDot, { backgroundColor: inside ? '#EF4444' : theme.textMuted }]} />
                <View style={{ flex: 1 }}>
                  <Text style={[styles.hazardTitle, { color: theme.textPrimary }]}>{h.title}</Text>
                  <Text style={[styles.hazardCoord, { color: theme.textMuted }]}>
                    {h.latitude.toFixed(5)}, {h.longitude.toFixed(5)}
                  </Text>
                </View>
                <View style={{ alignItems: 'flex-end' }}>
                  {dist !== null && (
                    <Text style={[styles.distanceText, { color: inside ? '#EF4444' : theme.textSecondary }]}>
                      {dist < 1000 ? `${dist}m` : `${(dist / 1000).toFixed(2)}km`}
                    </Text>
                  )}
                  <Text style={{ fontSize: 10, color: inside ? '#EF4444' : '#34D399' }}>
                    {inside ? '▶ INSIDE' : '○ outside'}
                  </Text>
                </View>
              </TouchableOpacity>
            );
          })}

          {hazards.length === 0 && !loadingHazards && (
            <Text style={[styles.empty, { color: theme.textMuted }]}>No hazards loaded. Tap refresh or create a hazard first.</Text>
          )}
        </Animated.View>

        {/* Log Panel */}
        <Animated.View entering={FadeInDown.delay(300).duration(400)} style={[styles.card, { backgroundColor: '#0F172A', borderColor: '#1E293B' }]}>
          <View style={styles.cardHeader}>
            <Text style={[styles.cardTitle, { color: '#94A3B8' }]}>Event Log</Text>
            <TouchableOpacity onPress={() => setLogs([])} style={[styles.refreshBtn, { backgroundColor: '#1E293B' }]}>
              <Ionicons name="trash-outline" size={16} color="#94A3B8" />
            </TouchableOpacity>
          </View>
          <ScrollView ref={scrollRef} style={styles.logScroll} nestedScrollEnabled>
            {logs.map(entry => (
              <View key={entry.id} style={styles.logRow}>
                <Text style={[styles.logTime, { color: '#475569' }]}>{entry.time}</Text>
                <Ionicons
                  name={LOG_ICONS[entry.level] as any}
                  size={13}
                  color={LOG_COLORS[entry.level]}
                  style={{ marginHorizontal: 4 }}
                />
                <Text style={[styles.logMsg, { color: LOG_COLORS[entry.level] }]} numberOfLines={3}>
                  {entry.message}
                </Text>
              </View>
            ))}
            {logs.length === 0 && (
              <Text style={{ color: '#475569', fontFamily: 'monospace', fontSize: 12 }}>
                No events yet. Run a proximity check.
              </Text>
            )}
          </ScrollView>
        </Animated.View>

      </ScrollView>
    </SafeAreaView>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────
function Row({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <View style={styles.statRow}>
      <Text style={styles.statLabel}>{label}</Text>
      <Text style={[styles.statValue, { color }]}>{value}</Text>
    </View>
  );
}

function ToggleRow({ label, icon, value, onChange, theme }: any) {
  return (
    <View style={[styles.toggleRow, { borderBottomColor: theme.border }]}>
      <Ionicons name={icon} size={18} color={theme.textMuted} style={{ marginRight: 10 }} />
      <Text style={[styles.toggleLabel, { color: theme.textPrimary }]}>{label}</Text>
      <Switch
        value={value}
        onValueChange={onChange}
        trackColor={{ false: theme.bgMuted, true: theme.accent }}
        thumbColor="#fff"
      />
    </View>
  );
}

// ─── Import Location for real GPS ─────────────────────────────────────────────
import * as Location from 'expo-location';

// ─── Styles ───────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  root: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: Platform.OS === 'ios' ? 8 : 16,
    paddingBottom: 14,
    borderBottomWidth: 1,
  },
  headerLeft: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  devBadge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  devBadgeText: { fontSize: 10, fontWeight: '800', letterSpacing: 1 },
  title: { fontSize: 20, fontWeight: '800' },
  pulseDot: { width: 16, height: 16, borderRadius: 8 },
  card: {
    margin: 16,
    marginBottom: 0,
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
  },
  cardHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 },
  cardTitle: { fontSize: 15, fontWeight: '700', marginBottom: 12 },
  row: { flexDirection: 'row', marginBottom: 8 },
  label: { fontSize: 12, fontWeight: '600', marginBottom: 5 },
  input: {
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    fontFamily: 'monospace',
  },
  btn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 14,
    borderRadius: 12,
    marginTop: 8,
  },
  btnText: { color: '#fff', fontWeight: '700', fontSize: 15 },
  refreshBtn: { width: 32, height: 32, borderRadius: 8, alignItems: 'center', justifyContent: 'center' },
  statRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: '#1E293B20' },
  statLabel: { fontSize: 13, color: '#64748B' },
  statValue: { fontSize: 13, fontWeight: '600', fontFamily: 'monospace' },
  toggleRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 12, borderBottomWidth: StyleSheet.hairlineWidth },
  toggleLabel: { flex: 1, fontSize: 14 },
  hazardRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    paddingHorizontal: 8,
    borderRadius: 10,
    borderWidth: 1,
    marginBottom: 8,
    gap: 10,
  },
  hazardDot: { width: 10, height: 10, borderRadius: 5 },
  hazardTitle: { fontSize: 13, fontWeight: '600' },
  hazardCoord: { fontSize: 10, fontFamily: 'monospace', marginTop: 2 },
  distanceText: { fontSize: 13, fontWeight: '700', fontFamily: 'monospace' },
  empty: { fontSize: 13, textAlign: 'center', paddingVertical: 16 },
  logScroll: { maxHeight: 260 },
  logRow: { flexDirection: 'row', alignItems: 'flex-start', marginBottom: 6, flexWrap: 'wrap' },
  logTime: { fontSize: 10, fontFamily: 'monospace', marginRight: 2, paddingTop: 1 },
  logMsg: { fontSize: 11, fontFamily: 'monospace', flex: 1 },
});
