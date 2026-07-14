import { useColorScheme } from 'nativewind';

// ── Color Palette ───────────────────────────────────────────────────────────
export const palette = {
  // Brand
  blue: {
    50: '#EFF6FF',
    100: '#DBEAFE',
    200: '#BFDBFE',
    400: '#60A5FA',
    500: '#3B82F6',
    600: '#2563EB',
    700: '#1D4ED8',
    900: '#1E3A8A',
    950: '#172554',
  },
  // Neutrals
  zinc: {
    50: '#FAFAFA',
    100: '#F4F4F5',
    200: '#E4E4E7',
    300: '#D4D4D8',
    400: '#A1A1AA',
    500: '#71717A',
    600: '#52525B',
    700: '#3F3F46',
    800: '#27272A',
    900: '#18181B',
    950: '#09090B',
  },
  slate: {
    50: '#F8FAFC',
    100: '#F1F5F9',
    200: '#E2E8F0',
    300: '#CBD5E1',
    400: '#94A3B8',
    500: '#64748B',
    600: '#475569',
    700: '#334155',
    800: '#1E293B',
    850: '#172033',
    900: '#0F172A',
    950: '#020617',
  },
  // Semantic
  green: { 400: '#4ADE80', 500: '#22C55E', 900: '#14532D' },
  red: { 400: '#F87171', 500: '#EF4444', 900: '#7F1D1D' },
  purple: { 400: '#C084FC', 500: '#A855F7', 900: '#4A1D96' },
  amber: { 400: '#FBBF24', 500: '#F59E0B' },
  emerald: { 400: '#34D399', 500: '#10B981' },
  orange: { 400: '#FB923C', 500: '#F97316' },
  pink: { 400: '#F472B6', 500: '#EC4899' },
};

// ── Theme Tokens ────────────────────────────────────────────────────────────
export interface ThemeTokens {
  // Backgrounds
  bg: string;
  bgCard: string;
  bgElevated: string;
  bgSubtle: string;
  bgMuted: string;

  // Text
  textPrimary: string;
  textSecondary: string;
  textMuted: string;
  textInverse: string;

  // Borders
  border: string;
  borderStrong: string;

  // Brand
  accent: string;
  accentLight: string;
  accentDark: string;

  // Status
  success: string;
  error: string;
  warning: string;

  // Tab bar
  tabActive: string;
  tabInactive: string;
  tabBg: string;
  tabBorder: string;

  // Misc
  isDark: boolean;
  separator: string;
  overlay: string;
  skeleton: string;
}

const lightTheme: ThemeTokens = {
  bg: '#F8FAFC',
  bgCard: '#FFFFFF',
  bgElevated: '#FFFFFF',
  bgSubtle: '#F1F5F9',
  bgMuted: '#E2E8F0',

  textPrimary: '#0F172A',
  textSecondary: '#475569',
  textMuted: '#94A3B8',
  textInverse: '#FFFFFF',

  border: '#E2E8F0',
  borderStrong: '#CBD5E1',

  accent: '#2563EB',
  accentLight: '#DBEAFE',
  accentDark: '#1D4ED8',

  success: '#22C55E',
  error: '#EF4444',
  warning: '#F59E0B',

  tabActive: '#2563EB',
  tabInactive: '#94A3B8',
  tabBg: '#FFFFFF',
  tabBorder: '#E2E8F0',

  isDark: false,
  separator: '#F1F5F9',
  overlay: 'rgba(0,0,0,0.4)',
  skeleton: '#E2E8F0',
};

const darkTheme: ThemeTokens = {
  bg: '#0A0F1E',
  bgCard: '#111827',
  bgElevated: '#1A2236',
  bgSubtle: '#1E293B',
  bgMuted: '#334155',

  textPrimary: '#F1F5F9',
  textSecondary: '#94A3B8',
  textMuted: '#64748B',
  textInverse: '#0F172A',

  border: '#1E293B',
  borderStrong: '#334155',

  accent: '#60A5FA',
  accentLight: '#1E3A8A',
  accentDark: '#3B82F6',

  success: '#4ADE80',
  error: '#F87171',
  warning: '#FBBF24',

  tabActive: '#60A5FA',
  tabInactive: '#475569',
  tabBg: '#0A0F1E',
  tabBorder: '#1E293B',

  isDark: true,
  separator: '#1E293B',
  overlay: 'rgba(0,0,0,0.7)',
  skeleton: '#1E293B',
};

// ── useTheme hook ─────────────────────────────────────────────────────────
export function useTheme(): ThemeTokens {
  const { colorScheme } = useColorScheme();
  return colorScheme === 'dark' ? darkTheme : lightTheme;
}

// ── Post type metadata ────────────────────────────────────────────────────
export const POST_TYPE_META: Record<string, { emoji: string; label: string; color: string; bg: string; darkBg: string }> = {
  question:       { emoji: '❓', label: 'Question',      color: '#F59E0B', bg: '#FEF3C7', darkBg: '#92400E' },
  share:          { emoji: '📢', label: 'Share',         color: '#3B82F6', bg: '#DBEAFE', darkBg: '#1E3A8A' },
  discussion:     { emoji: '💬', label: 'Discussion',    color: '#8B5CF6', bg: '#EDE9FE', darkBg: '#4C1D95' },
  meme:           { emoji: '🎭', label: 'Meme',          color: '#EC4899', bg: '#FCE7F3', darkBg: '#831843' },
  tip:            { emoji: '💡', label: 'Tip',           color: '#10B981', bg: '#D1FAE5', darkBg: '#064E3B' },
  news:           { emoji: '📰', label: 'News',          color: '#EF4444', bg: '#FEE2E2', darkBg: '#7F1D1D' },
  company_update: { emoji: '🏢', label: 'Update',        color: '#6366F1', bg: '#E0E7FF', darkBg: '#312E81' },
};

// ── Community purpose metadata ────────────────────────────────────────────
export const COMMUNITY_PURPOSE_META: Record<string, { emoji: string; color: string }> = {
  education:  { emoji: '🎓', color: '#3B82F6' },
  fun:        { emoji: '🎉', color: '#EC4899' },
  technology: { emoji: '💻', color: '#8B5CF6' },
  sports:     { emoji: '⚽', color: '#22C55E' },
  gaming:     { emoji: '🎮', color: '#F59E0B' },
  business:   { emoji: '💼', color: '#6366F1' },
  other:      { emoji: '🌐', color: '#64748B' },
};
