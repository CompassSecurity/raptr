<script setup lang="ts">
import type { ColumnDef } from '@tanstack/vue-table';
import {
    Lock,
    MoreHorizontal,
    Pencil,
    ShieldCheck,
    ShieldX,
    Trash2,
    UserPlus,
    Users,
} from '@lucide/vue';
import { h, onMounted } from 'vue';
import { toast } from 'vue-sonner';
import CreateUserModal from '@/components/admin/CreateUserModal.vue';
import EditUserModal from '@/components/admin/EditUserModal.vue';
import ManageUserACLModal from '@/components/admin/ManageUserACLModal.vue';
import ResetUserPasswordModal from '@/components/admin/ResetUserPasswordModal.vue';
import ConfirmDialog from '@/components/ConfirmDialog.vue';
import DateTimeDisplay from '@/components/DateTimeDisplay.vue';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import DataTable from '@/components/ui/data-table/DataTable.vue';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useModal, useModalWithData } from '@/composables/useModal';
import { usePagination } from '@/composables/usePagination';
import { useAdminStore } from '@/stores/admin';
import type { UserRead } from '@/types/utils';

const adminStore = useAdminStore();

// Use composables for pagination and sorting
const {
    fetch: fetchUsers,
    handleColumnFilterChange,
    handlePageChange,
    handlePageSizeChange,
    handleSortChange,
    pageSize,
    sortState,
} = usePagination((params) => adminStore.fetchUsers(params), 100);
sortState.value = { column: 'email', direction: 'asc' };

// Use composables for modals
const createModal = useModal();
const editModal = useModalWithData<UserRead>();
const deleteModal = useModalWithData<string>(); // Just store the ID for delete
const resetPasswordModal = useModalWithData<UserRead>();
const resetMFAModal = useModalWithData<UserRead>();
const manageAclModal = useModalWithData<UserRead>();

onMounted(() => {
    fetchUsers();
});

const handleConfirmDelete = async () => {
    if (deleteModal.data.value) {
        try {
            await adminStore.deleteUser(deleteModal.data.value);
            toast.success('User deleted successfully');
            fetchUsers();
        } catch (error) {
            // Error handled globally
        } finally {
            deleteModal.close();
        }
    }
};

const handleConfirmResetMFA = async () => {
    if (resetMFAModal.data.value) {
        try {
            const response = await adminStore.resetUserMFA(
                resetMFAModal.data.value.id,
            );
            console.log('Reset MFA Response:', response);
            if (response?.message) {
                toast.success(response.message);
            } else {
                console.error('No message in MFA response');
                toast.success('MFA reset successfully');
            }
        } catch (error) {
            // Error handled globally
        } finally {
            resetMFAModal.close();
        }
    }
};

// Filter options for select filters
const booleanFilterOptionMFA = [
    { label: 'Verified', value: 'true' },
    { label: 'Not Set', value: 'false' },
];

const booleanFilterOptionDisabled = [
    { label: 'Disabled', value: 'true' },
    { label: 'Active', value: 'false' },
];

const roleFilterOptions = [
    { label: 'Admin', value: 'admin' },
    { label: 'User', value: 'user' },
];

// Columns Definition - filterable columns match backend UserFilter schema
const columns: ColumnDef<UserRead>[] = [
    {
        accessorKey: 'email',
        header: 'Email',
        cell: ({ row }) =>
            h('div', { class: 'font-medium' }, row.getValue('email')),
        enableColumnFilter: true,
    },
    {
        accessorKey: 'role',
        header: 'Role',
        cell: ({ row }) => {
            const role = row.getValue('role') as string;
            return h(
                Badge,
                {
                    variant: role === 'admin' ? 'default' : 'secondary',
                    class: 'capitalize',
                },
                () => role,
            );
        },
        enableColumnFilter: true,
        meta: {
            filterVariant: 'select',
            filterOptions: roleFilterOptions,
        },
    },
    {
        accessorKey: 'id',
        header: 'ID',
        cell: ({ row }) =>
            h(
                'div',
                { class: 'font-mono text-xs text-muted-foreground' },
                row.getValue('id'),
            ),
        enableColumnFilter: false,
    },
    {
        accessorKey: 'mfa_verified',
        header: 'MFA',
        cell: ({ row }) => {
            const verified = row.getValue('mfa_verified') as boolean;
            return h(
                Badge,
                { variant: verified ? 'default' : 'secondary' },
                () => (verified ? 'Verified' : 'Not Set'),
            );
        },
        enableColumnFilter: true,
        meta: {
            filterVariant: 'select',
            filterOptions: booleanFilterOptionMFA,
        },
    },
    {
        accessorKey: 'last_login_at',
        header: 'Last Login',
        cell: ({ row }) =>
            h(DateTimeDisplay, {
                date: row.getValue('last_login_at') as string,
            }),
        enableColumnFilter: false,
    },
    {
        accessorKey: 'disabled',
        header: 'Status',
        cell: ({ row }) => {
            const disabled = row.getValue('disabled') as boolean;
            return h(
                Badge,
                { variant: disabled ? 'destructive' : 'outline' },
                () => (disabled ? 'Disabled' : 'Active'),
            );
        },
        enableColumnFilter: true,
        meta: {
            filterVariant: 'select',
            filterOptions: booleanFilterOptionDisabled,
        },
    },
    {
        id: 'actions',
        enableHiding: false,
        enableColumnFilter: false,
        cell: ({ row }) => {
            const user = row.original;
            return h(
                'div',
                { class: 'text-right' },
                h(
                    DropdownMenu,
                    {},
                    {
                        default: () => [
                            h(DropdownMenuTrigger, { asChild: true }, () =>
                                h(
                                    Button,
                                    { variant: 'ghost', class: 'h-8 w-8 p-0' },
                                    () => [
                                        h(
                                            'span',
                                            { class: 'sr-only' },
                                            'Open menu',
                                        ),
                                        h(MoreHorizontal, { class: 'h-4 w-4' }),
                                    ],
                                ),
                            ),
                            h(DropdownMenuContent, { align: 'end' }, () => {
                                const actions = [
                                    h(DropdownMenuLabel, () => 'Actions'),
                                    h(
                                        DropdownMenuItem,
                                        { onClick: () => editModal.open(user) },
                                        () => [
                                            h(Pencil, {
                                                class: 'mr-2 h-4 w-4',
                                            }),
                                            'Edit',
                                        ],
                                    ),
                                ];

                                if (user.role !== 'admin') {
                                    actions.push(
                                        h(
                                            DropdownMenuItem,
                                            {
                                                onClick: () =>
                                                    manageAclModal.open(user),
                                            },
                                            () => [
                                                h(ShieldCheck, {
                                                    class: 'mr-2 h-4 w-4',
                                                }),
                                                'Manage Access',
                                            ],
                                        ),
                                    );
                                }

                                actions.push(
                                    h(
                                        DropdownMenuItem,
                                        {
                                            onClick: () =>
                                                resetPasswordModal.open(user),
                                        },
                                        () => [
                                            h(Lock, { class: 'mr-2 h-4 w-4' }),
                                            'Reset Password',
                                        ],
                                    ),
                                    h(
                                        DropdownMenuItem,
                                        {
                                            onClick: () =>
                                                resetMFAModal.open(user),
                                        },
                                        () => [
                                            h(ShieldX, {
                                                class: 'mr-2 h-4 w-4',
                                            }),
                                            'Reset MFA',
                                        ],
                                    ),
                                    h(
                                        DropdownMenuItem,
                                        {
                                            class: 'text-destructive',
                                            onClick: () =>
                                                deleteModal.open(user.id),
                                        },
                                        () => [
                                            h(Trash2, {
                                                class: 'mr-2 h-4 w-4',
                                            }),
                                            'Delete User',
                                        ],
                                    ),
                                );

                                return actions;
                            }),
                        ],
                    },
                ),
            );
        },
    },
];
</script>

<template>
    <div class="container mx-auto px-6 py-8">
        <div class="flex items-center justify-between mb-8">
            <div>
                 <h1 class="text-3xl font-bold flex items-center gap-3">
                    <Users class="w-8 h-8" />
                    User Management
                </h1>
                <p class="text-muted-foreground mt-2">
                    Manage user accounts and their role.
                </p>
            </div>
            
            <Button @click="createModal.open">
                <UserPlus class="mr-2 h-4 w-4" />
                Create User
            </Button>
        </div>

        <div class="rounded-md">
            <DataTable
                :columns="columns"
                :data="adminStore.users"
                :pagination="adminStore.pagination"
                :page-size="pageSize"
                manual-sorting
                manual-filtering
                @page-change="handlePageChange"
                @page-size-change="handlePageSizeChange"
                @sort-change="handleSortChange"
                @column-filter-change="handleColumnFilterChange"
            />
        </div>

        <!-- Modals -->
        <CreateUserModal 
            v-model:open="createModal.isOpen.value" 
            @success="fetchUsers"
        />

        <EditUserModal 
            v-model:open="editModal.isOpen.value" 
            :user="editModal.data.value"
            @success="fetchUsers"
            v-if="editModal.data.value"
        />

        <ResetUserPasswordModal 
            v-model:open="resetPasswordModal.isOpen.value" 
            :user="resetPasswordModal.data.value"
            @success="fetchUsers"
        />

        <ManageUserACLModal
            v-if="manageAclModal.data.value"
            v-model:open="manageAclModal.isOpen.value"
            :user="manageAclModal.data.value"
        />

        <ConfirmDialog
            v-model:open="deleteModal.isOpen.value"
            title="Delete User"
            description="Are you sure you want to delete this user? This action cannot be undone."
            variant="destructive"
            confirm-text="Delete"
            :loading="adminStore.loading"
            @confirm="handleConfirmDelete"
        />

        <ConfirmDialog
            v-model:open="resetMFAModal.isOpen.value"
            title="Reset MFA"
            description="Are you sure you want to reset MFA for this user? They will need to setup MFA again."
            confirm-text="Reset MFA"
            @confirm="handleConfirmResetMFA"
        />
    </div>
</template>
