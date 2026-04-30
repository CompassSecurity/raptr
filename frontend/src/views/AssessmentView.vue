<script setup lang="ts">
import { storeToRefs } from 'pinia';
import { onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { toast } from 'vue-sonner';
import ActivityTable from '@/components/assessment/ActivityTable.vue';
import AssessmentToolbar from '@/components/assessment/AssessmentToolbar.vue';
import CreateActivityGroupModal from '@/components/assessment/CreateActivityGroupModal.vue';
import CreateActivityModal from '@/components/assessment/CreateActivityModal.vue';
import ExportResultsModal from '@/components/assessment/ExportResultsModal.vue';
import GenerateReportModal from '@/components/assessment/GenerateReportModal.vue';
import ImportActivityGroupTemplatesModal from '@/components/assessment/ImportActivityGroupTemplatesModal.vue';
import ImportActivityTemplatesModal from '@/components/assessment/ImportActivityTemplatesModal.vue';
import ImportCampaignTemplatesModal from '@/components/assessment/ImportCampaignTemplatesModal.vue';
import ImportVariablesModal from '@/components/assessment/ImportVariablesModal.vue';
import ManageACLModal from '@/components/assessment/ManageACLModal.vue';
import ManageAssetsModal from '@/components/assessment/ManageAssetsModal.vue';
import ManageDynamicQuestionsModal from '@/components/assessment/ManageDynamicQuestionsModal.vue';
import ManageOrderModal from '@/components/assessment/ManageOrderModal.vue';
import { Button } from '@/components/ui/button';
import {
    Dialog,
    DialogContent,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { useAutoRefresh } from '@/composables/useAutoRefresh';
import { useModal, useModalWithData } from '@/composables/useModal';
import {
    activityGroupService,
    activityService,
} from '@/services/activityService';
import { assessmentService } from '@/services/assessmentService';
import { reportService } from '@/services/reportService';
import { useAssessmentDetailStore } from '@/stores/assessmentDetail';
import { useAuthStore } from '@/stores/auth';
import { usePreferencesStore } from '@/stores/preferences';
import type { ActivityGroupRead, ActivityRead } from '@/types/utils';

const route = useRoute();
const router = useRouter();
const assessmentStore = useAssessmentDetailStore();
const authStore = useAuthStore();
const preferencesStore = usePreferencesStore();
const { activityViewMode: viewMode, activityTableFilters: columnFilters } =
    storeToRefs(preferencesStore);
const assessmentId = route.params.id as string;

// Show deleted state - initialize from localStorage (only for admins or red team)
const getInitialShowDeleted = () => {
    if (!authStore.hasAdminOrRedAccess(assessmentId)) return false;
    try {
        const stored = localStorage.getItem('showDeletedItems');
        return stored ? JSON.parse(stored) : false;
    } catch (error) {
        return false;
    }
};

const showDeleted = ref(getInitialShowDeleted());

// Watch for changes and save to localStorage (only for admins or red team)
watch(showDeleted, (newValue) => {
    if (authStore.hasAdminOrRedAccess(assessmentId)) {
        localStorage.setItem('showDeletedItems', JSON.stringify(newValue));
    }
});

// Pagination and sorting state
const currentPage = ref(1);
const pageSize = ref(100);
const sortBy = ref<string | null>('activity_position');
const sortOrder = ref<'asc' | 'desc' | null>('asc');

const fetchActivitiesWithParams = () => {
    const offset = (currentPage.value - 1) * pageSize.value;
    const params: Record<string, unknown> = {
        offset,
        limit: pageSize.value,
        sort_by: sortBy.value || undefined,
        sort_order: sortOrder.value || undefined,
    };

    // Add column filters to params
    for (const [key, value] of Object.entries(columnFilters.value)) {
        if (value !== undefined && value !== null) {
            if (typeof value === 'string' && value.length === 0) continue;
            if (Array.isArray(value) && value.length === 0) continue;
            params[key] = value;
        }
    }

    assessmentStore.fetchActivities(assessmentId, params);
};

const refreshData = async () => {
    await assessmentStore.fetchGroups(assessmentId);
    fetchActivitiesWithParams();
};

// Setup auto-refresh
useAutoRefresh(refreshData);

onMounted(async () => {
    if (assessmentId) {
        await assessmentStore.fetchAssessment(assessmentId);
        await refreshData();
    }
});

const handlePageChange = (page: number) => {
    currentPage.value = page;
    fetchActivitiesWithParams();
};

const handlePageSizeChange = (size: number) => {
    pageSize.value = size;
    currentPage.value = 1; // Reset to first page when changing page size
    fetchActivitiesWithParams();
};

const handleSortChange = (
    column: string | null,
    direction: 'asc' | 'desc' | null,
) => {
    // Fall back to activity_position when user clears sort
    sortBy.value = column ?? 'activity_position';
    sortOrder.value = direction ?? 'asc';
    currentPage.value = 1; // Reset to first page when sorting changes
    fetchActivitiesWithParams();
};

const handleColumnFilterChange = () => {
    currentPage.value = 1; // Reset to first page when filtering
    fetchActivitiesWithParams();
};

// Modal state
const createActivityModal = useModal();
const createGroupModal = useModal();
const manageAssetsModal = useModal();
const importActivityTemplatesModal = useModal();
const importActivityGroupTemplatesModal = useModal();
const importCampaignTemplatesModal = useModal();
const importVariablesModal = useModal();
const manageOrderModal = useModal();
const generateReportModal = useModal();
const exportResultsModal = useModal();
const aclModal = useModal();
const defaultTemplatesModal = useModal();

// Toolbar action handlers
const handleCreateActivity = () => {
    createActivityModal.open();
};

const handleActivityCreated = () => {
    fetchActivitiesWithParams();
};

const handleCreateGroup = () => {
    createGroupModal.open();
};

const handleGroupCreated = () => {
    assessmentStore.fetchGroups(assessmentId);
};

const handleImport = (type: string) => {
    if (type === 'activity-template') {
        importActivityTemplatesModal.open();
    } else if (type === 'group-template') {
        importActivityGroupTemplatesModal.open();
    } else if (type === 'campaign-template') {
        importCampaignTemplatesModal.open();
    } else if (type === 'variables') {
        importVariablesModal.open();
    } else {
        toast.info(`Import ${type} clicked`);
    }
};

const handleActivityTemplatesImported = () => {
    fetchActivitiesWithParams();
    assessmentStore.fetchGroups(assessmentId);
};

const handleActivityGroupTemplatesImported = () => {
    fetchActivitiesWithParams();
    assessmentStore.fetchGroups(assessmentId);
};

const handleCampaignTemplateImported = () => {
    fetchActivitiesWithParams();
    assessmentStore.fetchGroups(assessmentId);
};

const handleExport = async (type: string) => {
    if (type === 'generate-report') {
        generateReportModal.open();
    } else if (type === 'results-json') {
        exportResultsModal.open();
    } else if (type === 'mitre-navigator') {
        try {
            const { blob, filename } =
                await reportService.exportMitreNavigator(assessmentId);
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            toast.success('MITRE Navigator layer exported successfully');
        } catch {
            // Error handled globally
        }
    } else if (type === 'entire-assessment') {
        try {
            const { blob, filename } =
                await assessmentService.exportAssessment(assessmentId);
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            toast.success('Assessment exported successfully');
        } catch {
            // Error handled globally
        }
    } else {
        toast.info(`Export ${type} clicked`);
    }
};

const handleStatistics = () => {
    router.push({
        name: 'assessment-statistics',
        params: { id: assessmentId },
    });
};

const handleManageAssets = () => {
    manageAssetsModal.open();
};

const handleManageOrder = () => {
    manageOrderModal.open();
};

const handleManageACL = () => {
    aclModal.open();
};

const handleManageTemplates = () => {
    defaultTemplatesModal.open();
};

const handleOrderUpdated = () => {
    assessmentStore.fetchGroups(assessmentId);
    fetchActivitiesWithParams();
};

// Activity table handlers

const handleDeleteActivity = async (activity: ActivityRead) => {
    try {
        await activityService.toggleDeleteActivity(assessmentId, activity.id);
        // Show different message based on current state
        const message = activity.deleted
            ? 'Activity restored successfully'
            : 'Activity deleted successfully';
        toast.success(message);
        fetchActivitiesWithParams();
        // Also refresh groups in case we restored an activity in a deleted group
        assessmentStore.fetchGroups(assessmentId);
    } catch (error) {
        // Error handled globally
    }
};

const handleToggleVisibility = async (activity: ActivityRead) => {
    try {
        await activityService.toggleVisibleActivity(assessmentId, activity.id);
        // Show different message based on current state
        const message = activity.visible
            ? 'Activity hidden successfully'
            : 'Activity made visible successfully';
        toast.success(message);
        fetchActivitiesWithParams();
    } catch (error) {
        // Error handled globally
    }
};

const handleDuplicateActivity = async (activity: ActivityRead) => {
    try {
        await activityService.cloneActivity(assessmentId, activity.id);
        toast.success(`Activity "${activity.name}" cloned successfully`);
        fetchActivitiesWithParams();

        // If we're in grouped view, we should refresh groups too since the new activity
        // might be in the same group or affect group counts
        if (viewMode.value === 'grouped') {
            assessmentStore.fetchGroups(assessmentId);
        }
    } catch (error) {
        // Error handled globally
    }
};

// Move to Group (supports single and bulk)
const moveToGroupOpen = ref(false);
const moveToGroupIds = ref<string[]>([]);
const moveToGroupLabel = ref('');
const selectedGroupId = ref<string>('');
const moveToGroupSaving = ref(false);

const handleMoveToGroup = (activity: ActivityRead) => {
    moveToGroupIds.value = [activity.id];
    moveToGroupLabel.value = activity.name;
    selectedGroupId.value = activity.activity_group_id ?? '';
    moveToGroupOpen.value = true;
};

const handleBulkMoveToGroup = (activityIds: string[]) => {
    moveToGroupIds.value = activityIds;
    moveToGroupLabel.value = `${activityIds.length} activities`;
    selectedGroupId.value = '';
    moveToGroupOpen.value = true;
};

const handleMoveToGroupSave = async () => {
    if (moveToGroupIds.value.length === 0) return;

    moveToGroupSaving.value = true;
    try {
        await activityService.bulkMoveToGroup(
            assessmentId,
            moveToGroupIds.value,
            selectedGroupId.value || null,
        );
        toast.success(
            moveToGroupIds.value.length === 1
                ? `Activity "${moveToGroupLabel.value}" moved successfully`
                : `${moveToGroupIds.value.length} activities moved successfully`,
        );
        fetchActivitiesWithParams();
        assessmentStore.fetchGroups(assessmentId);
        moveToGroupOpen.value = false;
    } catch (error) {
        // Error handled globally
    } finally {
        moveToGroupSaving.value = false;
    }
};

// Bulk delete
const handleBulkDelete = async (activityIds: string[]) => {
    try {
        await activityService.bulkDeleteActivities(assessmentId, activityIds);
        toast.success(`${activityIds.length} activities deleted successfully`);
        fetchActivitiesWithParams();
        assessmentStore.fetchGroups(assessmentId);
    } catch (error) {
        // Error handled globally
    }
};

// Bulk toggle visibility
const handleBulkToggleVisibility = async (activityIds: string[]) => {
    try {
        await Promise.all(
            activityIds.map((id) =>
                activityService.toggleVisibleActivity(assessmentId, id),
            ),
        );
        toast.success(
            `Visibility toggled for ${activityIds.length} activities`,
        );
        fetchActivitiesWithParams();
    } catch (error) {
        // Error handled globally
    }
};

const handleRowClick = (activity: ActivityRead) => {
    router.push({
        name: 'assessment-activity-detail',
        params: {
            id: assessmentId,
            activityId: activity.id,
        },
    });
};

// Group action handlers
const editGroupModal = useModalWithData<ActivityGroupRead>();
const editGroupName = ref('');
const editGroupSaving = ref(false);

const handleGroupEdit = (group: ActivityGroupRead) => {
    editGroupName.value = group.name;
    editGroupModal.open(group);
};

const handleGroupEditSave = async () => {
    const group = editGroupModal.data.value;
    if (!group || !editGroupName.value.trim()) return;

    editGroupSaving.value = true;
    try {
        await activityGroupService.updateGroup(assessmentId, group.id, {
            name: editGroupName.value.trim(),
            visible: group.visible,
        });
        toast.success('Group renamed successfully');
        assessmentStore.fetchGroups(assessmentId);
        editGroupModal.close();
    } catch (error) {
        // Error handled globally
    } finally {
        editGroupSaving.value = false;
    }
};

const handleGroupDelete = async (group: ActivityGroupRead) => {
    try {
        await activityGroupService.toggleDeleteGroup(assessmentId, group.id);
        const message = group.deleted
            ? 'Group restored successfully'
            : 'Group deleted successfully';
        toast.success(message);
        assessmentStore.fetchGroups(assessmentId);
        fetchActivitiesWithParams();
    } catch (error) {
        // Error handled globally
    }
};

const handleGroupToggleVisibility = async (group: ActivityGroupRead) => {
    try {
        await activityGroupService.toggleVisibleGroup(assessmentId, group.id);
        const message = group.visible
            ? 'Group hidden successfully'
            : 'Group made visible successfully';
        toast.success(message);
        assessmentStore.fetchGroups(assessmentId);
    } catch (error) {
        // Error handled globally
    }
};
</script>

<template>
  <div class="flex flex-col h-full">
    <AssessmentToolbar
      :assessment-id="assessmentId"
      :assessment-name="assessmentStore.assessment?.name"
      :loading="assessmentStore.loading"
      :view-mode="viewMode"
      :show-deleted="showDeleted"
      @create-activity="handleCreateActivity"
      @create-group="handleCreateGroup"
      @import="handleImport"
      @export="handleExport"
      @statistics="handleStatistics"
      @manage-assets="handleManageAssets"
      @manageAssets="handleManageAssets"
      @manage-order="handleManageOrder"
      @manage-acl="handleManageACL"
      @manage-templates="handleManageTemplates"
      @update:view-mode="viewMode = $event"
      @update:show-deleted="showDeleted = $event"
    />

    <!-- Content -->
    <ScrollArea class="flex-1">
      <div class="p-2 md:p-6">
        <ActivityTable
        :assessment-id="assessmentId"
        :activities="assessmentStore.activities"
        :groups="assessmentStore.groups"
        :pagination="assessmentStore.activityPagination"
        :page-size="pageSize"
        :view-mode="viewMode"
        :show-deleted="showDeleted"
        @page-change="handlePageChange"
        @page-size-change="handlePageSizeChange"
        @sort-change="handleSortChange"
        @column-filter-change="handleColumnFilterChange"
        @delete="handleDeleteActivity"
        @duplicate="handleDuplicateActivity"
        @move-to-group="handleMoveToGroup"
        @toggle-visibility="handleToggleVisibility"
        @row-click="handleRowClick"
        @group-edit="handleGroupEdit"
        @group-delete="handleGroupDelete"
        @group-toggle-visibility="handleGroupToggleVisibility"
        @bulk-delete="handleBulkDelete"
        @bulk-move-to-group="handleBulkMoveToGroup"
        @bulk-toggle-visibility="handleBulkToggleVisibility"
      />
      </div>
    </ScrollArea>

    <!-- Modals -->
    <CreateActivityModal
      :open="createActivityModal.isOpen.value"
      :assessment-id="assessmentId"
      @update:open="(val) => val ? createActivityModal.open() : createActivityModal.close()"
      @created="handleActivityCreated"
    />
    <CreateActivityGroupModal
      :open="createGroupModal.isOpen.value"
      :assessment-id="assessmentId"
      @update:open="(val) => val ? createGroupModal.open() : createGroupModal.close()"
      @created="handleGroupCreated"
    />
    <ManageAssetsModal
      :open="manageAssetsModal.isOpen.value"
      :assessment-id="assessmentId"
      @update:open="(val) => val ? manageAssetsModal.open() : manageAssetsModal.close()"
    />
    <ImportActivityTemplatesModal
      :open="importActivityTemplatesModal.isOpen.value"
      :assessment-id="assessmentId"
      @update:open="(val) => val ? importActivityTemplatesModal.open() : importActivityTemplatesModal.close()"
      @success="handleActivityTemplatesImported"
    />
    <ImportActivityGroupTemplatesModal
      :open="importActivityGroupTemplatesModal.isOpen.value"
      :assessment-id="assessmentId"
      @update:open="(val) => val ? importActivityGroupTemplatesModal.open() : importActivityGroupTemplatesModal.close()"
      @success="handleActivityGroupTemplatesImported"
    />
    <ImportCampaignTemplatesModal
      :open="importCampaignTemplatesModal.isOpen.value"
      :assessment-id="assessmentId"
      @update:open="(val) => val ? importCampaignTemplatesModal.open() : importCampaignTemplatesModal.close()"
      @success="handleCampaignTemplateImported"
    />
    <ImportVariablesModal
      :open="importVariablesModal.isOpen.value"
      :assessment-id="assessmentId"
      @update:open="(val) => val ? importVariablesModal.open() : importVariablesModal.close()"
      @success="() => {}"
    />
    <ManageOrderModal
      :open="manageOrderModal.isOpen.value"
      :assessment-id="assessmentId"
      @update:open="(val) => val ? manageOrderModal.open() : manageOrderModal.close()"
      @success="handleOrderUpdated"
    />
    <ManageACLModal
      v-if="assessmentStore.assessment"
      :open="aclModal.isOpen.value"
      :assessment="assessmentStore.assessment"
      @update:open="(val) => val ? aclModal.open() : aclModal.close()"
      @success="() => {}"
    />
    <ManageDynamicQuestionsModal
      v-if="assessmentStore.assessment"
      :open="defaultTemplatesModal.isOpen.value"
      mode="assessment"
      :assessment-id="assessmentId"
      :current-questions="(assessmentStore.assessment.default_evaluation_templates as any) ?? []"
      @update:open="(val) => val ? defaultTemplatesModal.open() : defaultTemplatesModal.close()"
      @success="refreshData"
    />
    <GenerateReportModal
      :open="generateReportModal.isOpen.value"
      :assessment-id="assessmentId"
      @update:open="(val) => val ? generateReportModal.open() : generateReportModal.close()"
    />
    <ExportResultsModal
      :open="exportResultsModal.isOpen.value"
      :assessment-id="assessmentId"
      @update:open="(val) => val ? exportResultsModal.open() : exportResultsModal.close()"
    />
    <!-- Edit Group Name Dialog -->
    <Dialog
      :open="editGroupModal.isOpen.value"
      @update:open="(val) => val ? null : editGroupModal.close()"
    >
      <DialogContent class="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle>Edit Group</DialogTitle>
        </DialogHeader>
        <div class="py-4">
          <Label for="group-name">Name</Label>
          <Input
            id="group-name"
            v-model="editGroupName"
            class="mt-2"
            @keydown.enter="handleGroupEditSave"
          />
        </div>
        <DialogFooter>
          <Button variant="outline" @click="editGroupModal.close()">Cancel</Button>
          <Button @click="handleGroupEditSave" :disabled="editGroupSaving || !editGroupName.trim()">
            {{ editGroupSaving ? 'Saving...' : 'Save' }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- Move to Group Dialog -->
    <Dialog
      :open="moveToGroupOpen"
      @update:open="(val) => moveToGroupOpen = val"
    >
      <DialogContent class="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle>Move to Group</DialogTitle>
        </DialogHeader>
        <div class="py-4 space-y-2">
          <Label>{{ moveToGroupIds.length === 1 ? 'Activity' : 'Activities' }}</Label>
          <p class="text-sm text-muted-foreground">{{ moveToGroupLabel }}</p>
          <Label class="mt-4">Group</Label>
          <Select v-model="selectedGroupId">
            <SelectTrigger>
              <SelectValue placeholder="Select a group" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem
                v-for="group in assessmentStore.groups.filter(g => !g.deleted)"
                :key="group.id"
                :value="group.id"
              >
                {{ group.name }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
        <DialogFooter>
          <Button variant="outline" @click="moveToGroupOpen = false">Cancel</Button>
          <Button @click="handleMoveToGroupSave" :disabled="moveToGroupSaving || !selectedGroupId">
            {{ moveToGroupSaving ? 'Moving...' : 'Move' }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
