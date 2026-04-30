<script setup lang="ts">
import type { ColumnDef } from '@tanstack/vue-table';
import {
    MoreHorizontal,
    Pencil,
    Plus,
    Settings2,
    ShieldCheck,
    Trash2,
    Upload,
} from 'lucide-vue-next';
import { h, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { toast } from 'vue-sonner';
import CreateAssessmentModal from '@/components/assessment/CreateAssessmentModal.vue';
import EditAssessmentModal from '@/components/assessment/EditAssessmentModal.vue';
import ManageACLModal from '@/components/assessment/ManageACLModal.vue';
import ManageDynamicQuestionsModal from '@/components/assessment/ManageDynamicQuestionsModal.vue';
import ConfirmDialog from '@/components/ConfirmDialog.vue';
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
import { assessmentService } from '@/services/assessmentService';
import { useAssessmentListStore } from '@/stores/assessmentList';
import { useAuthStore } from '@/stores/auth';
import type { AssessmentRead } from '@/types/utils';

const authStore = useAuthStore();
const router = useRouter();
const assessmentStore = useAssessmentListStore();

// Use composables for pagination and modals
const {
    fetch: fetchAssessments,
    handleColumnFilterChange,
    handlePageChange,
    handlePageSizeChange,
    handleSortChange,
    pageSize,
    sortState,
} = usePagination((params) => assessmentStore.fetchAssessments(params), 100);
sortState.value = { column: 'name', direction: 'asc' };

const createModal = useModal();
const editModal = useModalWithData<AssessmentRead>();
const deleteModal = useModalWithData<AssessmentRead>();
const aclModal = useModalWithData<AssessmentRead>();
const defaultTemplatesModal = useModalWithData<AssessmentRead>();

onMounted(() => {
    fetchAssessments();
});

const confirmDelete = async () => {
    if (deleteModal.data.value) {
        try {
            await assessmentStore.deleteAssessment(deleteModal.data.value.id);
            toast.success('Assessment deleted successfully');
            fetchAssessments();
        } catch (error) {
            // Error handled globally
        } finally {
            deleteModal.close();
        }
    }
};

const handleModalSuccess = () => {
    fetchAssessments();
};

// Import assessment
const fileInputRef = ref<HTMLInputElement | null>(null);
const importing = ref(false);

const triggerImport = () => {
    fileInputRef.value?.click();
};

const handleImportFile = async (event: Event) => {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    importing.value = true;
    try {
        const result = await assessmentService.importAssessment(file);
        toast.success(result.message);
        if (result.warnings && result.warnings.length > 0) {
            for (const warning of result.warnings) {
                toast.warning(warning);
            }
        }
        fetchAssessments();
    } catch {
        // Error handled globally
    } finally {
        importing.value = false;
        input.value = ''; // reset so same file can be re-selected
    }
};

const handleRowClick = (assessment: AssessmentRead) => {
    router.push({ name: 'assessment-detail', params: { id: assessment.id } });
};

// Filter options for assessment type
const typeFilterOptions = [
    { label: 'Purple Team', value: 'PurpleTeam' },
    { label: 'Red Team', value: 'RedTeam' },
];

// Columns Definition - filterable columns match backend AssessmentFilter schema
const columns: ColumnDef<AssessmentRead>[] = [
    {
        accessorKey: 'name',
        header: 'Name',
        cell: ({ row }) =>
            h('div', { class: 'font-medium' }, row.getValue('name')),
        enableColumnFilter: true,
    },
    {
        accessorKey: 'description',
        header: 'Description',
        cell: ({ row }) =>
            h(
                'div',
                { class: 'text-sm text-muted-foreground truncate max-w-md' },
                row.getValue('description'),
            ),
        enableColumnFilter: false,
    },
    {
        accessorKey: 'assessment_type',
        header: 'Type',
        cell: ({ row }) => {
            const type = row.getValue('assessment_type') as string;
            return h(
                Badge,
                {
                    variant: type === 'PurpleTeam' ? 'default' : 'destructive',
                },
                () => type,
            );
        },
        enableColumnFilter: true,
        meta: {
            filterVariant: 'select',
            filterOptions: typeFilterOptions,
        },
    },
    {
        id: 'actions',
        enableHiding: false,
        enableColumnFilter: false,
        cell: ({ row }) => {
            const assessment = row.original;

            // Check for Admin or Red Team access using the store helper
            // This helper returns true if user is Global Admin OR has 'red' role on this assessment
            const canEdit = authStore.hasAdminOrRedAccess(assessment.id);

            // If user doesn't even have Red Team access, show nothing
            if (!canEdit) return null;

            const isAdmin = authStore.user?.role === 'admin';

            // Build menu items array dynamically
            const menuItems = [
                h(DropdownMenuLabel, () => 'Actions'),
                // Edit and Manage Templates are visible to Admin and Red Team
                h(
                    DropdownMenuItem,
                    {
                        onClick: () => editModal.open(assessment),
                    },
                    () => [h(Pencil, { class: 'mr-2 h-4 w-4' }), 'Edit'],
                ),
            ];

            // Manage ACLs is Admin only
            if (isAdmin) {
                menuItems.push(
                    h(
                        DropdownMenuItem,
                        {
                            onClick: () => aclModal.open(assessment),
                        },
                        () => [
                            h(ShieldCheck, { class: 'mr-2 h-4 w-4' }),
                            'Manage ACLs',
                        ],
                    ),
                );
            }

            // Default Templates is Admin and Red Team
            menuItems.push(
                h(
                    DropdownMenuItem,
                    {
                        onClick: () => defaultTemplatesModal.open(assessment),
                    },
                    () => [
                        h(Settings2, { class: 'mr-2 h-4 w-4' }),
                        'Default Evaluation Templates',
                    ],
                ),
            );

            // Delete is Admin only
            if (isAdmin) {
                menuItems.push(
                    h(
                        DropdownMenuItem,
                        {
                            class: 'text-destructive',
                            onClick: () => deleteModal.open(assessment),
                        },
                        () => [h(Trash2, { class: 'mr-2 h-4 w-4' }), 'Delete'],
                    ),
                );
            }

            return h(
                'div',
                {
                    class: 'text-right',
                    onClick: (e: Event) => e.stopPropagation(),
                },
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
                            h(
                                DropdownMenuContent,
                                { align: 'end' },
                                () => menuItems,
                            ),
                        ],
                    },
                ),
            );
        },
    },
];
</script>

<template>
  <div class="container mx-auto px-4 md:px-6 py-8">
    <div class="flex flex-col md:flex-row items-start md:items-center justify-between mb-8 gap-4">
      <div>
        <h1 class="text-3xl font-bold">Assessments</h1>
        <p class="text-muted-foreground mt-2">
          Manage and organize your security assessments.
        </p>
      </div>
      
      <div v-if="authStore.user?.role === 'admin'" class="flex gap-2">
        <Button @click="triggerImport" variant="outline" :disabled="importing">
          <Upload class="mr-2 h-4 w-4" />
          {{ importing ? 'Importing...' : 'Import Assessment' }}
        </Button>
        <input
          ref="fileInputRef"
          type="file"
          accept=".zip"
          class="hidden"
          @change="handleImportFile"
        />
        <Button @click="createModal.open">
          <Plus class="mr-2 h-4 w-4" />
          Create Assessment
        </Button>
      </div>
    </div>
    
    <div class="rounded-md">
      <DataTable
        :columns="columns"
        :data="assessmentStore.assessments"
        :pagination="assessmentStore.pagination"
        :page-size="pageSize"
        manual-sorting
        manual-filtering
        @page-change="handlePageChange"
        @page-size-change="handlePageSizeChange"
        @sort-change="handleSortChange"
        @column-filter-change="handleColumnFilterChange"
        @row-click="handleRowClick"
      />
    </div>

    <CreateAssessmentModal 
      v-model:open="createModal.isOpen.value" 
      @success="handleModalSuccess"
    />

    <EditAssessmentModal 
      v-model:open="editModal.isOpen.value" 
      :assessment="editModal.data.value"
      @success="handleModalSuccess"
      v-if="editModal.data.value"
    />

    <ManageACLModal
      v-model:open="aclModal.isOpen.value"
      :assessment="aclModal.data.value"
      @success="handleModalSuccess"
      v-if="aclModal.data.value"
    />

    <ManageDynamicQuestionsModal
      v-if="defaultTemplatesModal.data.value"
      v-model:open="defaultTemplatesModal.isOpen.value"
      mode="assessment"
      :assessment-id="defaultTemplatesModal.data.value.id"
      :current-questions="(defaultTemplatesModal.data.value.default_evaluation_templates as any) ?? []"
      @success="handleModalSuccess"
    />

    <ConfirmDialog
      v-model:open="deleteModal.isOpen.value"
      title="Delete Assessment?"
      description="This action cannot be undone. This will permanently delete the assessment and remove all associated data."
      confirm-text="Delete"
      variant="destructive"
      :loading="assessmentStore.loading"
      @confirm="confirmDelete"
    />
  </div>
</template>
