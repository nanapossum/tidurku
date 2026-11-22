import { Ionicons } from '@expo/vector-icons';
import { StyleSheet, Text, TextInput, View } from 'react-native';
import { COLORS } from '../theme/colors';

export default function CustomInput({ label, error, icon, ...inputProps }) {
  return (
    <View style={styles.field}>
      <Text style={styles.label}>{label}</Text>
      <View style={[styles.control, error && styles.invalid]}>
        {icon ? <Ionicons name={icon} size={20} color={COLORS.accent} /> : null}
        <TextInput accessibilityLabel={label} placeholderTextColor={COLORS.muted} {...inputProps} style={styles.input} />
      </View>
      {error ? <Text accessibilityLiveRegion="polite" style={styles.error}>{error}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  field: { gap: 6 },
  label: { color: COLORS.text, fontFamily: 'Nunito' },
  control: {
    flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 12,
    borderWidth: 1, borderColor: COLORS.border, borderRadius: 12, backgroundColor: COLORS.background,
  },
  input: { flex: 1, fontFamily: "Inter", minHeight: 48, color: COLORS.text, fontSize: 16 },
  invalid: { borderColor: COLORS.danger },
  error: { color: COLORS.danger },
});
