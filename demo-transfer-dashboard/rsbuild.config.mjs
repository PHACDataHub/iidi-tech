import { defineConfig } from '@rsbuild/core';
import { pluginReact } from '@rsbuild/plugin-react';

export default defineConfig({
  plugins: [pluginReact()],
  source: {
    define: {
      'process.env.ON_OUTBOUND_URL': JSON.stringify(
        process.env.ON_OUTBOUND_URL,
      ),
      'process.env.BC_OUTBOUND_URL': JSON.stringify(
        process.env.BC_OUTBOUND_URL,
      ),
    },
  },
});
