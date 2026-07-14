import React, { useEffect, useState } from 'react';
import { View, Text, Switch, FlatList, TouchableOpacity, Modal, TextInput, Alert, StyleSheet, LogBox, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as Location from 'expo-location';

LogBox.ignoreLogs(['Background location is limited in Expo Go']);
import apiClient from '../../app/api/client'; // central client with correct URL + auth interceptor
import { useAuthStore } from '../../store/authStore';
import { requestLocationPermissions, stopLocationTracking, registerForPushNotificationsAsync } from '../../services/locationTracking';
import { useRouter } from 'expo-router';
import Header from '../../components/Header';
const HAZARD_CATEGORIES = [
  { id: "Waterlogging", icon: "water" },
  { id: "Bad Roads", icon: "hammer" },
  { id: "Stray Dogs", icon: "paw" },
  { id: "Poor Lighting", icon: "flash-off" },
  { id: "Harassment Spot", icon: "hand-left" },
  { id: "Unsafe Area", icon: "warning" },
  { id: "Accident", icon: "medkit" },
];

export default function LocationsScreen() {
  const [isTracking, setIsTracking] = useState(false);
  const [activeTab, setActiveTab] = useState<'hazards' | 'gates'>('hazards');
  
  // Hazards State
  const [hazards, setHazards] = useState<any[]>([]);
  const [showHazardModal, setShowHazardModal] = useState(false);
  const [newHazardTitle, setNewHazardTitle] = useState('');
  const [newHazardDesc, setNewHazardDesc] = useState('');
  
  // Gates State
  const [gates, setGates] = useState<any[]>([]);
  const [showGateModal, setShowGateModal] = useState(false);
  const [newGateName, setNewGateName] = useState('');
  
  // Gate Review State
  const [selectedGate, setSelectedGate] = useState<any>(null);
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [gateReviews, setGateReviews] = useState<any[]>([]);
  const [newReview, setNewReview] = useState({
    waiting_time: '',
    lift_available: false,
    parking: false,
    delivery_difficulty: 3,
    guard_behavior: 3,
    comment: ''
  });

  const router = useRouter();

  useEffect(() => {
    fetchHazards();
    fetchGates();
    checkTrackingStatus();
  }, []);

  const fetchHazards = async () => {
    try {
      const response = await apiClient.get('/hazards');
      setHazards(response.data.data || []);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchGates = async () => {
    try {
      const response = await apiClient.get('/gates');
      setGates(response.data.data || []);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchGateReviews = async (gateId: string) => {
    try {
      const response = await apiClient.get(`/gates/${gateId}/reviews`);
      setGateReviews(response.data.data || []);
    } catch (e) {
      console.error(e);
    }
  };

  const checkTrackingStatus = async () => {
    try {
      const hasStarted = await Location.hasStartedLocationUpdatesAsync('background-location-task');
      setIsTracking(hasStarted);
    } catch (e) {}
  };

  const toggleTracking = async () => {
    if (isTracking) {
      await stopLocationTracking();
      setIsTracking(false);
    } else {
      await registerForPushNotificationsAsync();
      const granted = await requestLocationPermissions();
      if (granted) {
        setIsTracking(true);
      } else {
        Alert.alert("Permission Denied", "Background location permission is required.");
      }
    }
  };

  const handleCreateHazard = async () => {
    if (!newHazardTitle) return;
    try {
      let location;
      try {
        const { status } = await Location.requestForegroundPermissionsAsync();
        if (status !== 'granted') {
          Alert.alert("Permission Denied", "Location permission is required.");
          return;
        }
        location = await Location.getCurrentPositionAsync({});
      } catch (locErr) {
        location = await Location.getLastKnownPositionAsync({});
        if (!location) {
          Alert.alert("Location Error", "Make sure location services are enabled.");
          return;
        }
      }

      await apiClient.post('/hazards', {
        title: newHazardTitle,
        description: newHazardDesc,
        latitude: location.coords.latitude,
        longitude: location.coords.longitude,
        severity: 'medium',
      });
      setShowHazardModal(false);
      setNewHazardTitle('');
      setNewHazardDesc('');
      fetchHazards();
    } catch (e) {
      console.error(e);
      Alert.alert("Error", "Failed to report hazard.");
    }
  };

  const handleCreateGate = async () => {
    if (!newGateName) return;
    try {
      let location;
      try {
        const { status } = await Location.requestForegroundPermissionsAsync();
        if (status !== 'granted') {
          Alert.alert("Permission Denied", "Location permission is required.");
          return;
        }
        location = await Location.getCurrentPositionAsync({});
      } catch (locErr) {
        location = await Location.getLastKnownPositionAsync({});
        if (!location) {
          Alert.alert("Location Error", "Make sure location services are enabled.");
          return;
        }
      }

      await apiClient.post('/gates', {
        society_name: newGateName,
        latitude: location.coords.latitude,
        longitude: location.coords.longitude,
      });
      setShowGateModal(false);
      setNewGateName('');
      fetchGates();
    } catch (e) {
      console.error(e);
      Alert.alert("Error", "Failed to create gate.");
    }
  };

  const handleSubmitReview = async () => {
    if (!selectedGate) return;
    try {
      await apiClient.post(`/gates/${selectedGate.id}/reviews`, {
        waiting_time: parseInt(newReview.waiting_time) || 0,
        lift_available: newReview.lift_available,
        parking: newReview.parking,
        delivery_difficulty: newReview.delivery_difficulty,
        guard_behavior: newReview.guard_behavior,
        comment: newReview.comment,
      });
      setShowReviewModal(false);
      setNewReview({ waiting_time: '', lift_available: false, parking: false, delivery_difficulty: 3, guard_behavior: 3, comment: '' });
      fetchGateReviews(selectedGate.id);
    } catch (e) {
      console.error(e);
      Alert.alert("Error", "Failed to submit review.");
    }
  };

  const openGateDetails = (gate: any) => {
    setSelectedGate(gate);
    fetchGateReviews(gate.id);
  };

  return (
    <View style={styles.container}>
      <Header title="Location Intelligence" />
      <View style={styles.trackingContainer}>
        <Text style={styles.trackingText}>Background Tracking & Alerts</Text>
        <Switch value={isTracking} onValueChange={toggleTracking} />
      </View>

      <View style={styles.tabContainer}>
        <TouchableOpacity style={[styles.tab, activeTab === 'hazards' && styles.activeTab]} onPress={() => setActiveTab('hazards')}>
          <Text style={[styles.tabText, activeTab === 'hazards' && styles.activeTabText]}>Hazards</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.tab, activeTab === 'gates' && styles.activeTab]} onPress={() => setActiveTab('gates')}>
          <Text style={[styles.tabText, activeTab === 'gates' && styles.activeTabText]}>Gates</Text>
        </TouchableOpacity>
      </View>

      {activeTab === 'hazards' ? (
        <FlatList
          data={hazards}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <View style={styles.listItem}>
              <View style={styles.listIcon}><Ionicons name="warning" size={24} color="#ff3b30" /></View>
              <View style={styles.listContent}>
                <Text style={styles.listTitle}>{item.title}</Text>
                <Text style={styles.listDesc}>{item.description}</Text>
                <Text style={styles.listStatus}>Severity: {item.severity}</Text>
              </View>
            </View>
          )}
          ListEmptyComponent={<Text style={styles.emptyText}>No hazards reported nearby.</Text>}
        />
      ) : (
        <FlatList
          data={gates}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <TouchableOpacity style={styles.listItem} onPress={() => openGateDetails(item)}>
              <View style={styles.listIcon}><Ionicons name="business" size={24} color="#007AFF" /></View>
              <View style={styles.listContent}>
                <Text style={styles.listTitle}>{item.society_name}</Text>
                <Text style={styles.listDesc}>Tap to view intelligence & reviews</Text>
              </View>
            </TouchableOpacity>
          )}
          ListEmptyComponent={<Text style={styles.emptyText}>No society gates added yet.</Text>}
        />
      )}

      {/* FAB */}
      <TouchableOpacity 
        style={styles.fab} 
        onPress={() => activeTab === 'hazards' ? setShowHazardModal(true) : setShowGateModal(true)}
      >
        <Ionicons name="add" size={30} color="#fff" />
      </TouchableOpacity>

      {/* Hazard Creation Modal */}
      <Modal visible={showHazardModal} animationType="slide" transparent={true}>
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Report a Hazard</Text>
            <Text style={styles.label}>Select Category</Text>
            <View style={styles.chipGrid}>
              {HAZARD_CATEGORIES.map(cat => (
                <TouchableOpacity 
                  key={cat.id} 
                  style={[styles.chip, newHazardTitle === cat.id && styles.activeChip]}
                  onPress={() => setNewHazardTitle(cat.id)}
                >
                  <Ionicons 
                    name={cat.icon as any} 
                    size={20} 
                    color={newHazardTitle === cat.id ? '#fff' : '#007AFF'} 
                    style={{marginBottom: 4}}
                  />
                  <Text style={[styles.chipText, newHazardTitle === cat.id && styles.activeChipText]}>{cat.id}</Text>
                </TouchableOpacity>
              ))}
            </View>
            
            <TextInput 
              style={[styles.input, styles.textArea, {marginTop: 12}]} 
              placeholder="Additional Details (Optional)" 
              multiline
              value={newHazardDesc}
              onChangeText={setNewHazardDesc}
            />
            <View style={styles.modalButtons}>
              <TouchableOpacity style={styles.cancelButton} onPress={() => setShowHazardModal(false)}>
                <Text style={styles.cancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.submitButton} onPress={handleCreateHazard}>
                <Text style={styles.submitText}>Submit</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Gate Creation Modal */}
      <Modal visible={showGateModal} animationType="slide" transparent={true}>
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Add Society Gate</Text>
            <TextInput 
              style={styles.input} 
              placeholder="Society Name (e.g., Prestige Shantiniketan)" 
              value={newGateName}
              onChangeText={setNewGateName}
            />
            <View style={styles.modalButtons}>
              <TouchableOpacity style={styles.cancelButton} onPress={() => setShowGateModal(false)}>
                <Text style={styles.cancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.submitButton} onPress={handleCreateGate}>
                <Text style={styles.submitText}>Add Gate</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Gate Intelligence Modal */}
      <Modal visible={!!selectedGate} animationType="slide" transparent={true}>
        <View style={styles.fullModalContainer}>
          <SafeAreaView style={styles.fullModalContent}>
            <View style={styles.header}>
              <TouchableOpacity onPress={() => setSelectedGate(null)} style={styles.backButton}>
                <Ionicons name="close" size={28} color="#000" />
              </TouchableOpacity>
              <Text style={styles.title}>{selectedGate?.society_name}</Text>
              <View style={{width: 28}} />
            </View>

            <ScrollView style={styles.gateDetailsScroll}>
              <Text style={styles.sectionTitle}>Gate Intelligence</Text>
              {gateReviews.length === 0 ? (
                <Text style={styles.emptyText}>No reviews yet. Be the first to share intelligence!</Text>
              ) : (
                gateReviews.map(review => (
                  <View key={review.id} style={styles.reviewCard}>
                    <Text>Waiting Time: {review.waiting_time} mins</Text>
                    <Text>Lift Available: {review.lift_available ? 'Yes' : 'No'}</Text>
                    <Text>Parking: {review.parking ? 'Yes' : 'No'}</Text>
                    <Text>Guard Behavior (1-5): {review.guard_behavior}</Text>
                    {review.comment ? <Text style={styles.reviewComment}>"{review.comment}"</Text> : null}
                  </View>
                ))
              )}

              <TouchableOpacity style={styles.addReviewBtn} onPress={() => setShowReviewModal(true)}>
                <Text style={styles.addReviewBtnText}>Add Intelligence Review</Text>
              </TouchableOpacity>
            </ScrollView>
          </SafeAreaView>
        </View>
      </Modal>

      {/* Submit Gate Review Modal */}
      <Modal visible={showReviewModal} animationType="slide" transparent={true}>
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Submit Intelligence</Text>
            
            <Text style={styles.label}>Avg Waiting Time (mins)</Text>
            <TextInput style={styles.input} keyboardType="numeric" value={newReview.waiting_time} onChangeText={(t) => setNewReview({...newReview, waiting_time: t})} />
            
            <View style={styles.switchRow}>
              <Text>Lift Available?</Text>
              <Switch value={newReview.lift_available} onValueChange={(v) => setNewReview({...newReview, lift_available: v})} />
            </View>

            <View style={styles.switchRow}>
              <Text>Parking Available?</Text>
              <Switch value={newReview.parking} onValueChange={(v) => setNewReview({...newReview, parking: v})} />
            </View>

            <TextInput style={[styles.input, styles.textArea, {marginTop: 12}]} placeholder="Additional Comments (Guard strictness, entry rules...)" multiline value={newReview.comment} onChangeText={(t) => setNewReview({...newReview, comment: t})} />
            
            <View style={styles.modalButtons}>
              <TouchableOpacity style={styles.cancelButton} onPress={() => setShowReviewModal(false)}>
                <Text style={styles.cancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.submitButton} onPress={handleSubmitReview}>
                <Text style={styles.submitText}>Submit</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f2f2f7' },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16, backgroundColor: '#fff' },
  backButton: { padding: 4 },
  title: { fontSize: 20, fontWeight: 'bold' },
  trackingContainer: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16, backgroundColor: '#fff', marginTop: 1 },
  trackingText: { fontSize: 16, fontWeight: '500' },
  tabContainer: { flexDirection: 'row', margin: 16, backgroundColor: '#e5e5ea', borderRadius: 8, padding: 4 },
  tab: { flex: 1, paddingVertical: 8, alignItems: 'center', borderRadius: 6 },
  activeTab: { backgroundColor: '#fff', shadowColor: '#000', shadowOpacity: 0.1, shadowRadius: 2, elevation: 2 },
  tabText: { fontSize: 15, fontWeight: '500', color: '#8e8e93' },
  activeTabText: { color: '#000' },
  sectionTitle: { fontSize: 18, fontWeight: '600', margin: 16, marginTop: 24 },
  listItem: { flexDirection: 'row', backgroundColor: '#fff', padding: 16, marginHorizontal: 16, marginBottom: 8, borderRadius: 8, alignItems: 'center' },
  listIcon: { marginRight: 16 },
  listContent: { flex: 1 },
  listTitle: { fontSize: 16, fontWeight: 'bold' },
  listDesc: { fontSize: 14, color: '#666', marginTop: 4 },
  listStatus: { fontSize: 12, color: '#ff3b30', marginTop: 8 },
  emptyText: { textAlign: 'center', color: '#888', marginTop: 32 },
  modalContainer: { flex: 1, justifyContent: 'center', backgroundColor: 'rgba(0,0,0,0.5)' },
  modalContent: { backgroundColor: '#fff', margin: 24, padding: 24, borderRadius: 12 },
  fullModalContainer: { flex: 1, backgroundColor: '#f2f2f7' },
  fullModalContent: { flex: 1 },
  modalTitle: { fontSize: 20, fontWeight: 'bold', marginBottom: 16 },
  label: { fontSize: 14, fontWeight: '600', marginBottom: 8, color: '#333' },
  input: { backgroundColor: '#f2f2f7', padding: 12, borderRadius: 8, marginBottom: 12 },
  textArea: { height: 80, textAlignVertical: 'top' },
  modalButtons: { flexDirection: 'row', justifyContent: 'flex-end', marginTop: 16 },
  cancelButton: { padding: 12, marginRight: 16 },
  cancelText: { color: '#007AFF', fontSize: 16 },
  submitButton: { backgroundColor: '#007AFF', paddingHorizontal: 24, paddingVertical: 12, borderRadius: 8 },
  submitText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  chipGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 12, justifyContent: 'space-between' },
  chip: { backgroundColor: '#e5e5ea', width: '31%', paddingVertical: 12, borderRadius: 12, alignItems: 'center', justifyContent: 'center', marginBottom: 8 },
  activeChip: { backgroundColor: '#007AFF' },
  chipText: { color: '#333', fontSize: 11, fontWeight: '600', textAlign: 'center' },
  activeChipText: { color: '#fff' },
  gateDetailsScroll: { flex: 1 },
  reviewCard: { backgroundColor: '#fff', padding: 16, marginHorizontal: 16, marginBottom: 12, borderRadius: 8 },
  reviewComment: { marginTop: 8, fontStyle: 'italic', color: '#666' },
  addReviewBtn: { backgroundColor: '#007AFF', margin: 16, padding: 16, borderRadius: 8, alignItems: 'center' },
  addReviewBtnText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  switchRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, backgroundColor: '#f2f2f7', padding: 12, borderRadius: 8 },
  fab: {
    position: 'absolute',
    bottom: 24,
    right: 20,
    width: 58,
    height: 58,
    borderRadius: 29,
    backgroundColor: '#007AFF',
    alignItems: 'center',
    justifyContent: 'center',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.35,
    shadowRadius: 12,
    elevation: 8,
  }
});
