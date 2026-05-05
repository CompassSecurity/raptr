# Frontend Development

The frontend is a Vue 3 single-page application built with Vite, TailwindCSS v4, and Pinia for state management.

??? bug "Full disclaimer"
    The frontend was generated primarily using AI agents. I'm sorry. You will probably find a lot of AI Slop in the code. Nevertheless, the reality is that without AI this project would not exist. If you are a frontend developer and you find some time to improve the code quality, I would be very grateful. 

## Prerequisites

- [Bun](https://bun.sh/) — JavaScript runtime and package manager

## Dev Setup

```bash
cd frontend
bun install          # Install dependencies
bun run dev          # Start Vite dev server (port 5173)
```

The dev server proxies API requests to `http://localhost:8000/api/v1` (configured in `.env.development`).

## Project Structure

```
frontend/src/
├── main.ts                  # Vue app initialization
├── App.vue                  # Root component
├── router/index.ts          # Vue Router configuration
├── services/                # API communication layer
│   ├── api.ts               #   Axios instance with interceptors
│   ├── assessmentService.ts
│   ├── activityService.ts
│   └── ...                  #   One service per domain
├── stores/                  # Pinia state management
│   ├── auth.ts              #   Authentication and tokens
│   ├── assessmentDetail.ts  #   Single assessment with activities
│   ├── assessmentList.ts    #   Assessment list for home view
│   ├── preferences.ts       #   User preferences (timezone, format)
│   └── admin.ts             #   Admin user operations
├── components/
│   ├── ui/                  #   shadcn-vue base components (Reka UI)
│   ├── assessment/          #   Assessment-related modals
│   ├── admin/               #   Admin components
│   └── profile/             #   User profile settings
├── composables/             # Reusable composition functions
├── types/
│   ├── types.gen.ts         #   Auto-generated TypeScript types (@hey-api/openapi-ts)
│   ├── zod.gen.ts           #   Auto-generated Zod schemas (@hey-api/openapi-ts)
│   ├── utils.ts             #   Re-exports from types.gen + shared utility types
│   └── components.ts        #   Component-specific types
├── utils/
│   ├── zodAdapter.ts        #   Zod v4 → vee-validate TypedSchema adapter
│   └── ...                  #   other utility functions
└── views/                   # Route-level page components
```

## Key Patterns

### Service Layer

Stores **never** make API calls directly. All HTTP communication goes through services:

```typescript
// services/widgetService.ts
import { api } from './api';
import type { WidgetRead, PaginatedResponse } from '@/types/utils';

export const widgetService = {
    async getAll(): Promise<PaginatedResponse<WidgetRead>> {
        const response = await api.get<PaginatedResponse<WidgetRead>>('/widgets/');
        return response.data;
    },
};
```

### Store Pattern

Stores manage reactive state and delegate to services:

```typescript
// stores/widget.ts
import { defineStore } from 'pinia';
import { ref } from 'vue';
import { widgetService } from '@/services/widgetService';

export const useWidgetStore = defineStore('widget', () => {
    const items = ref<WidgetRead[]>([]);
    const loading = ref(false);  // Always 'loading', never 'isLoading'

    async function fetchItems() {
        loading.value = true;
        try {
            const data = await widgetService.getAll();
            items.value = data.items;
        } finally {
            loading.value = false;
        }
    }

    return { items, loading, fetchItems };
});
```

### Type Imports

Always import entity types from `@/types/utils` — `utils.ts` re-exports the named types from `types.gen.ts` and adds hand-written utility types:

```typescript
// Correct
import type { UserRead, AssessmentRead } from '@/types/utils';

// Wrong — `components` is not exported by the generator
import type { components } from '@/types/types.gen';
type UserRead = components['schemas']['UserRead'];
```

If a type isn't re-exported yet, add the name to the `export type { … } from './types.gen'` block in `utils.ts`.

### Form Validation

Forms use [vee-validate](https://vee-validate.logaretm.com/) with the auto-generated Zod schemas. Each schema is exported individually with a `z` prefix (`zUserBase`, `zAssessmentBase`, …) — there is no `schemas` namespace.

```typescript
import { useForm } from 'vee-validate';
import { toTypedSchema } from '@/utils/zodAdapter';
import { zUserBase } from '@/types/zod.gen';

const { handleSubmit } = useForm({
    validationSchema: toTypedSchema(zUserBase),
});
```

`toTypedSchema` is a small local adapter (`utils/zodAdapter.ts`) that bridges Zod v4 schemas to vee-validate's `TypedSchema` interface — the published `@vee-validate/zod` package only supports Zod v3.

Validation runs **only on form submit** (configured globally in `main.ts`). After a failed submit, vee-validate auto-revalidates each field as the user edits it, so errors clear live once they've been surfaced. The default Zod v4 message for missing required fields (`"Invalid input: expected string, received undefined"`) is overridden to `"Required"` via a global `z.config({ customError })` — see `main.ts`.

### Composables

Use built-in composables instead of manual state management:

- **`usePagination`** — Handles paginated data tables (page state, search, fetching)
- **`useModal`** / **`useModalWithData<T>`** — Modal open/close state with optional data
- **`useConfirmDialog<T>`** — Confirmation dialogs with typed items

### Components

All components use `<script setup lang="ts">`. UI primitives come from shadcn-vue (Reka UI based).

## Type Generation

Frontend types are generated from the backend's OpenAPI schema using [`@hey-api/openapi-ts`](https://heyapi.dev/). Configuration lives in `frontend/openapi-ts.config.ts`.

After any backend API change, regenerate the frontend types:

```bash
bun run update:api   # Requires backend running on localhost:8000
```

This runs two steps:

1. `fetch:openapi` — downloads `openapi.json` from the running backend
2. `gen:api` — runs `@hey-api/openapi-ts` to produce `src/types/types.gen.ts` (TypeScript types) and `src/types/zod.gen.ts` (Zod schemas)

Each script can also be run individually.

!!! warning
    Never edit `types.gen.ts` or `zod.gen.ts` manually — they are overwritten on each generation. Add re-exports to `utils.ts` instead.

## Linting and Formatting

We use [Biome](https://biomejs.dev/) for linting and formatting:

```bash
bun run lint         # Check for lint and format issues
bun run lint:fix     # Auto-fix issues
```

## Building

```bash
bun run build        # Type-check (vue-tsc) + production build (Vite)
```

This runs `vue-tsc` first to catch type errors, then builds optimized assets. Both lint and build checks run automatically in CI on pull requests.
