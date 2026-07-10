import { View, Text } from 'react-native';

export default function BookmarksScreen() {
  return (
    <View className="flex-1 items-center justify-center bg-white dark:bg-black">
      <Text className="text-xl font-bold text-black dark:text-white">There are no bookmarks to display.</Text>
    </View>
  );
}
