# AGENT.md

This file provides guidance to AI agents when working with code in this repository.

## Quick Reference — Critical Rules

> **Read this section first before making any changes.**

### ✅ DO

1. **Use `loading` not `isLoading`** for all loading state in stores
2. **Import types from `@/types/utils`** — never define local type aliases
3. **Delegate API calls from stores to services** — stores manage state only
4. **Use `<script setup lang="ts">`** for all Vue components
5. **Use composables** (`usePagination`, `useModalWithData`) for common patterns
6. **Run `bun run build`** to verify TypeScript after any changes

### ❌ DON'T

1. **Don't edit `schema.ts` or `zod.ts`** — they are auto-generated
2. **Don't make API calls directly from stores** — use the service layer
3. **Don't define types like `type UserRead = components['schemas']['UserRead']`** — import from utils
4. **Don't use `isLoading`** — always use `loading`
5. **Don't manually manage pagination state** — use `usePagination` composable

---

## Project Overview

Vue 3 + TypeScript frontend for RAPTR (assessment management system). Uses Vite, Pinia, and shadcn-vue components.

## Development Commands

```bash
bun dev          # Start dev server
bun run build    # Type-check and build for production
bun run preview  # Preview production build

# Type generation (requires backend on localhost:8000)
bun run gen:types  # Generate TypeScript types from OpenAPI
bun run gen:zod    # Generate Zod schemas from OpenAPI
```

---

## Architecture Patterns

### 1. Type Imports

**Always import from `@/types/utils`** — this is the single source of truth for entity types.

```typescript
// ✅ CORRECT
import type { UserRead, AssessmentRead, PaginationParams } from '@/types/utils';

// ❌ WRONG - Don't define local type aliases
import type { components } from '@/types/schema';
type UserRead = components['schemas']['UserRead'];  // Never do this!
```

**Available types in `utils.ts`:**
- Entity types: `AssessmentRead`, `ActivityRead`, `UserRead`, `AclRead`, `TagRead`, `AssetRead`
- Base types: `AssessmentBase`, `ActivityBase`, `UserBase`, `ActivityGroupBase`
- Update types: `ActivityUpdate`, `ActivityGroupUpdate`, `UserPasswordReset`
- Enums: `ActivityPriority`, `ActivityState`, `ActivitySeverity`, `UserRole`, `AclRole`
- Utilities: `PaginatedResponse<T>`, `PaginationParams`, `PaginationState`, `MessageResponse`

If you need a type that's not exported, **add it to `utils.ts`** first.

---

### 2. Store Pattern

Stores manage state only. They **must** delegate API calls to the service layer.

```typescript
// src/stores/myStore.ts
import { defineStore } from 'pinia';
import { ref } from 'vue';
import { myService } from '@/services/myService';
import type { MyType, PaginationParams, PaginationState } from '@/types/utils';

export const useMyStore = defineStore('myStore', () => {
    // State
    const items = ref<MyType[]>([]);
    const loading = ref(false);  // ✅ Always 'loading', never 'isLoading'
    const pagination = ref<PaginationState>({ total: 0, page: 1, size: 100, pages: 1 });

    // Actions - delegate to service
    async function fetchItems(params?: PaginationParams) {
        loading.value = true;
        try {
            const data = await myService.getItems(params);
            items.value = data.items;
            pagination.value = { total: data.total, page: data.page, size: data.size, pages: data.pages };
        } finally {
            loading.value = false;
        }
    }

    return { items, loading, pagination, fetchItems };
});
```

**Store files location:** `src/stores/`
- `auth.ts` — Authentication, token management
- `admin.ts` — Admin user operations (uses `userService` and `adminService`)
- `assessmentList.ts` — Assessment list for home view
- `assessmentDetail.ts` — Single assessment with activities/groups
- `preferences.ts` — User preferences (timezone, date format)

---

### 3. Service Layer

Services handle all API communication. They return typed data directly.

```typescript
// src/services/myService.ts
import { api } from './api';
import type { MyType, PaginatedResponse, PaginationParams } from '@/types/utils';

export const myService = {
    async getItems(params?: PaginationParams): Promise<PaginatedResponse<MyType>> {
        const response = await api.get<PaginatedResponse<MyType>>('/my-endpoint/', { params });
        return response.data;
    },

    async createItem(data: MyTypeBase): Promise<MyType> {
        const response = await api.post<MyType>('/my-endpoint/', data);
        return response.data;
    },
};
```

**Service files location:** `src/services/`
- `api.ts` — Axios instance with interceptors (token, error handling)
- `assessmentService.ts` — Assessment CRUD
- `activityService.ts` — Activity operations, bulk actions, groups
- `userService.ts` — User management
- `adminService.ts` — Admin-only operations (MITRE import, templates)
- `assetService.ts`, `tagService.ts`, `aclService.ts`

---

### 4. Composables

**Use composables instead of manual state management.**

#### `usePagination` — For paginated data tables

```typescript
import { usePagination } from '@/composables/usePagination';

const { fetch, handleSearch, handlePageChange } = usePagination(
    (params) => myStore.fetchItems(params),
    100  // page size
);

onMounted(() => fetch());
```

Replaces manual `currentPage`, `pageSize`, `searchQuery` refs.

#### `useModal` — For simple modals

```typescript
import { useModal } from '@/composables/useModal';

const createModal = useModal();
// Template: :open="createModal.isOpen.value"
// Button: @click="createModal.open"
```

#### `useModalWithData<T>` — For edit/delete modals with data

```typescript
import { useModalWithData } from '@/composables/useModal';

const editModal = useModalWithData<UserRead>();
// Open with data: editModal.open(user)
// Access data: editModal.data.value
// Close: editModal.close()  (auto-clears data after animation)
```

#### `useConfirmDialog<T>` — For confirmation dialogs

```typescript
import { useConfirmDialog } from '@/composables/useConfirmDialog';

const deleteDialog = useConfirmDialog<string>();
deleteDialog.open(userId);
// In template: :item="deleteDialog.item.value"
```

---

### 5. Component Patterns

**All components use `<script setup lang="ts">`.**

#### Modal Pattern
```vue
<script setup lang="ts">
import type { UserRead } from '@/types/utils';

const props = defineProps<{
  open: boolean;
  user: UserRead | null;
}>();

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void;
  (e: 'success'): void;
}>();
</script>
```

#### Form Validation
```typescript
import { useForm } from 'vee-validate';
import { toTypedSchema } from '@vee-validate/zod';
import { schemas } from '@/types/zod';

const formSchema = toTypedSchema(schemas.UserBase);
const { handleSubmit, isSubmitting } = useForm({ validationSchema: formSchema });
```

---

### 6. File Organization

```
src/
├── components/
│   ├── ui/              # shadcn-vue base components
│   ├── admin/           # User management modals
│   ├── assessment/      # Assessment CRUD modals
│   └── profile/         # Profile settings
├── composables/         # Reusable composition functions
├── services/            # API communication layer
├── stores/              # Pinia state management
├── types/
│   ├── schema.ts        # 🔒 Auto-generated - DO NOT EDIT
│   ├── zod.ts           # 🔒 Auto-generated - DO NOT EDIT
│   ├── utils.ts         # ✅ Shared entity types (add new types here)
│   └── components.ts    # ✅ Component-specific types
├── utils/               # Utility functions
└── views/               # Route components
```

---

## Common Tasks

### Adding a New API Endpoint

1. **Create/update service** in `src/services/`:
   ```typescript
   async newMethod(): Promise<ResponseType> {
       const response = await api.post<ResponseType>('/endpoint/');
       return response.data;
   }
   ```

2. **Add types to `utils.ts`** if needed:
   ```typescript
   export type NewType = components['schemas']['NewType'];
   ```

3. **Update store** to use the service:
   ```typescript
   async function newAction() {
       loading.value = true;
       try {
           await myService.newMethod();
       } finally {
           loading.value = false;
       }
   }
   ```

### Adding a New Modal

1. Create component in appropriate folder (`admin/`, `assessment/`, etc.)
2. Use `defineProps<{ open: boolean; data?: DataType }>()` pattern
3. Emit `update:open` and `success` events
4. In parent view, use `useModalWithData<DataType>()` composable

### After Backend API Changes

```bash
bun run gen:types  # Regenerate schema.ts
bun run gen:zod    # Regenerate zod.ts
```

Then add any new types to `utils.ts` as exports.

---

## Environment Variables

```env
VITE_API_URL=http://localhost:8000/api/v1
```

## Error Handling

Centralized in `src/utils/errorHandler.ts`:
- Auto-logout on 401 Unauthorized
- Toast notifications via vue-sonner
- Validation error formatting

## Notes

- Package manager: Bun (`bun.lock`)
- Styling: Tailwind CSS v4 with Vite plugin
- UI Components: shadcn-vue (Reka UI based)
- Data Tables: TanStack Vue Table
- Date formatting respects user timezone preferences (`src/utils/dateFormatter.ts`)
