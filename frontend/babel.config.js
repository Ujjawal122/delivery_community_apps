module.exports = function (api) {
  api.cache(true);
  return {
    presets: [
      // babel-preset-expo handles jsxImportSource for nativewind internally.
      // Do NOT add "nativewind/babel" as a second preset — it conflicts with
      // RN 0.81 / Expo SDK 54 and leaves private class fields untranspiled.
      ["babel-preset-expo", { jsxImportSource: "nativewind" }],
    ],
    plugins: [
      // Reanimated plugin MUST be last.
      "react-native-reanimated/plugin",
    ],
  };
};
