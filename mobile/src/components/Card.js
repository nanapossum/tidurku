import { Pressable, StyleSheet, Text, View } from 'react-native';
import { COLORS } from '../theme/colors';

export default function Card({ title, subtitle, children, onPress }) {
  const Container = onPress ? Pressable : View;
  return (
    <Container style={styles.card} {...(onPress && { onPress, accessibilityRole: 'button' })}>
      <Text style={styles.title}>{title}</Text>
      {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
      {children}
    </Container>
  );
}

const styles = StyleSheet.create({
  card: { backgroundColor: COLORS.card, borderRadius: 20, padding: 18, gap: 8 },
  title: { color: COLORS.text, fontSize: 18, fontFamily: 'Nunito' },
  subtitle: { color: COLORS.muted, fontFamily: "Inter", fontSize: 14 },
});
