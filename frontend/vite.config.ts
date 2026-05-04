import path from 'node:path';
import tailwindcss from '@tailwindcss/vite';
import vue from '@vitejs/plugin-vue';
import { defineConfig } from 'vite';
import pkg from './package.json';

export default defineConfig({
    plugins: [vue(), tailwindcss()],
    resolve: {
        alias: {
            '@': path.resolve(__dirname, './src'),
        },
    },
    define: {
        __APP_VERSION__: JSON.stringify(
            process.env.VITE_APP_VERSION || pkg.version,
        ),
    },
});
