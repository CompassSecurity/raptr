import { defineStore } from 'pinia';
import { ref } from 'vue';
import { adminService } from '@/services/adminService';
import { userService } from '@/services/userService';
import type {
    PaginationState,
    UserBase,
    UserCreate,
    UserPasswordReset,
    UserRead,
} from '@/types/utils';

export const useAdminStore = defineStore('admin', () => {
    // State
    const users = ref<UserRead[]>([]);
    const loading = ref(false);
    const pagination = ref<PaginationState>({
        total: 0,
        page: 1,
        size: 100,
        pages: 1,
    });

    // User Management Actions
    async function fetchUsers(params?: Record<string, unknown>) {
        loading.value = true;
        try {
            const data = await userService.getUsers(params);
            users.value = data.items;
            pagination.value = {
                total: data.total,
                page: data.page,
                size: data.size,
                pages: data.pages,
            };
        } finally {
            loading.value = false;
        }
    }

    async function createUser(userData: UserCreate) {
        loading.value = true;
        try {
            await userService.createUser(userData);
            await fetchUsers(); // Refresh list
        } finally {
            loading.value = false;
        }
    }

    async function updateUser(userId: string, userData: UserBase) {
        loading.value = true;
        try {
            await userService.updateUser(userId, userData);
            await fetchUsers();
        } finally {
            loading.value = false;
        }
    }

    async function deleteUser(userId: string) {
        loading.value = true;
        try {
            await userService.deleteUser(userId);
            await fetchUsers(); // Refresh list
        } finally {
            loading.value = false;
        }
    }

    async function resetUserPassword(userId: string, data: UserPasswordReset) {
        loading.value = true;
        try {
            return await userService.resetUserPassword(userId, data);
        } finally {
            loading.value = false;
        }
    }

    async function resetUserMFA(userId: string) {
        loading.value = true;
        try {
            return await userService.resetUserMFA(userId);
        } finally {
            loading.value = false;
        }
    }

    // Admin Import Actions
    async function importMitre() {
        loading.value = true;
        try {
            return await adminService.importMitre();
        } finally {
            loading.value = false;
        }
    }

    async function importARTActivityTemplates() {
        loading.value = true;
        try {
            return await adminService.importARTActivityTemplates();
        } finally {
            loading.value = false;
        }
    }

    async function importCustomerActivityTemplates() {
        loading.value = true;
        try {
            return await adminService.importCustomActivityTemplates();
        } finally {
            loading.value = false;
        }
    }

    return {
        users,
        pagination,
        loading,
        fetchUsers,
        createUser,
        updateUser,
        deleteUser,
        importMitre,
        importARTActivityTemplates,
        importCustomerActivityTemplates,
        resetUserPassword,
        resetUserMFA,
    };
});
