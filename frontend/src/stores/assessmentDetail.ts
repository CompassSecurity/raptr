import { defineStore } from 'pinia';
import { ref } from 'vue';
import {
    activityGroupService,
    activityService,
} from '@/services/activityService';
import { assessmentService } from '@/services/assessmentService';
import type {
    ActivityGroupRead,
    ActivityRead,
    AssessmentRead,
    PaginationState,
} from '@/types/utils';

export const useAssessmentDetailStore = defineStore('assessmentDetail', () => {
    const assessment = ref<AssessmentRead | null>(null);
    const groups = ref<ActivityGroupRead[]>([]);
    const activities = ref<ActivityRead[]>([]);
    const activityPagination = ref<PaginationState>({
        total: 0,
        page: 1,
        size: 100,
        pages: 1,
    });
    const loading = ref(false);
    // Last activity query, so a refetch keeps the caller's sort order and limit
    let lastActivityParams: Record<string, unknown> | undefined;

    async function fetchAssessment(id: string) {
        loading.value = true;
        try {
            assessment.value = await assessmentService.getAssessment(id);
        } finally {
            loading.value = false;
        }
    }

    async function fetchActivities(
        assessmentId: string,
        params?: Record<string, unknown>,
    ) {
        lastActivityParams = params;
        loading.value = true;
        try {
            const data = await activityService.getActivities(
                assessmentId,
                params,
            );
            activities.value = data.items;
            activityPagination.value = {
                total: data.total,
                page: data.page,
                size: data.size,
                pages: data.pages,
            };
        } finally {
            loading.value = false;
        }
    }

    async function fetchGroups(assessmentId: string, query?: string) {
        loading.value = true;
        try {
            groups.value = await activityGroupService.getGroups(assessmentId, {
                ...(query ? { query } : {}),
                sort_by: 'activity_group_position',
                sort_order: 'asc',
            });
        } finally {
            loading.value = false;
        }
    }

    async function refreshActivity(assessmentId: string, activityId: string) {
        const fresh = await activityService.getActivity(
            assessmentId,
            activityId,
        );
        const idx = activities.value.findIndex((a) => a.id === activityId);
        if (idx !== -1) {
            activities.value[idx] = fresh;
        }
        return fresh;
    }

    async function reorderGroups(assessmentId: string, groupIds: string[]) {
        await activityGroupService.reorderGroups(assessmentId, groupIds);
        await fetchGroups(assessmentId);
    }

    /**
     * Put an activity at its new place in a group. A move from another group
     * lands at the end of the target group, so the target is reordered after.
     * orderedActivityIds must list every non-deleted activity of the group.
     */
    async function placeActivity(
        assessmentId: string,
        activityId: string,
        groupId: string,
        orderedActivityIds: string[],
        fromOtherGroup: boolean,
    ) {
        if (fromOtherGroup) {
            await activityService.bulkMoveToGroup(
                assessmentId,
                [activityId],
                groupId,
            );
        }
        await activityGroupService.reorderActivities(
            assessmentId,
            groupId,
            orderedActivityIds,
        );
        await fetchActivities(assessmentId, lastActivityParams);
    }

    return {
        assessment,
        groups,
        activities,
        activityPagination,
        loading,
        fetchAssessment,
        fetchActivities,
        fetchGroups,
        refreshActivity,
        reorderGroups,
        placeActivity,
    };
});
