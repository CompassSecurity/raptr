import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
    input: './openapi.json',
    output: {
        path: './src/types',
        clean: false,
        entryFile: false,
    },
    plugins: [
        '@hey-api/typescript',
        {
            name: 'zod',
            required: true,
        },
    ],
});
