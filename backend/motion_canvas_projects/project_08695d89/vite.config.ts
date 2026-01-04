import {defineConfig} from 'vite';
import motionCanvas from '@motion-canvas/vite-plugin';

export default defineConfig({
  plugins: [
    // Handle both default export and function export
    (motionCanvas as any).default ? (motionCanvas as any).default() : (motionCanvas as any)(),
  ],
});
