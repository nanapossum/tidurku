import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS } from '../theme/colors';

const qualityIcons = { 1: 'frown', 2: 'frown', 3: 'meh', 4: 'smile', 5: 'smile' };

export default function CategoryChips({ options, value, onChange }) {
  return (
    <View style={styles.row}>
      {options.map((option) => (
        <Pressable
          key={option}
          accessibilityRole="button"
          accessibilityState={{ selected: value === option }}
          onPress={() => onChange(option)}
          style={[styles.chip, value === option && styles.selected]}
        >
          {qualityIcons[option] && (
            <Feather name={qualityIcons[option]} size={19} color={value === option ? 'white' : COLORS.primary} />
          )}
          <Text style={[styles.label, value === option && {color: "white"}]}>{option}</Text>
        </Pressable>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: {
    minHeight: 44, justifyContent: 'center', paddingHorizontal: 10, alignItems: 'center', flexGrow: 1, backgroundColor: COLORS.surface, borderRadius: 12,
    borderWidth: 1, borderColor: COLORS.border,
  },
  selected: { backgroundColor: COLORS.primary, borderColor: COLORS.primary },
  label: { color: COLORS.text, fontWeight: '600' },
});
