import type {
    ActivityBase,
    ActivityGroupBase,
    ActivityGroupRead,
    ActivityGroupUpdate,
    ActivityHistoryRead,
    ActivityRead,
    ActivityUpdate,
    DynamicEvaluationQuestionAssign,
    MessageResponse,
    PaginatedResponse,
} from '@/types/utils';
import { api } from './api';

export type ActivityCreateInput = Pick<
    ActivityBase,
    'name' | 'mitre_tactic' | 'mitre_technique'
>;

export const activityService = {
    async getActivities(
        assessmentId: string,
        params?: Record<string, unknown>,
    ): Promise<PaginatedResponse<ActivityRead>> {
        const response = await api.get<PaginatedResponse<ActivityRead>>(
            `/assessments/${assessmentId}/activity/`,
            { params },
        );
        return response.data;
    },

    async getActivity(
        assessmentId: string,
        activityId: string,
    ): Promise<ActivityRead> {
        const response = await api.get<ActivityRead>(
            `/assessments/${assessmentId}/activity/${activityId}`,
        );
        return response.data;
    },

    async createActivity(
        assessmentId: string,
        data: ActivityCreateInput,
    ): Promise<ActivityRead> {
        const response = await api.post<ActivityRead>(
            `/assessments/${assessmentId}/activity/`,
            data,
        );
        return response.data;
    },

    async updateActivity(
        assessmentId: string,
        activityId: string,
        data: ActivityUpdate,
    ): Promise<ActivityRead> {
        const response = await api.put<ActivityRead>(
            `/assessments/${assessmentId}/activity/${activityId}`,
            data,
        );
        return response.data;
    },

    async cloneActivity(
        assessmentId: string,
        activityId: string,
    ): Promise<ActivityRead> {
        const response = await api.put<ActivityRead>(
            `/assessments/${assessmentId}/activity/${activityId}/clone`,
        );
        return response.data;
    },

    async toggleDeleteActivity(
        assessmentId: string,
        activityId: string,
    ): Promise<void> {
        await api.put(
            `/assessments/${assessmentId}/activity/${activityId}/delete`,
        );
    },

    async toggleVisibleActivity(
        assessmentId: string,
        activityId: string,
    ): Promise<void> {
        await api.put(
            `/assessments/${assessmentId}/activity/${activityId}/visible`,
        );
    },

    async bulkDeleteActivities(
        assessmentId: string,
        activityIds: string[],
    ): Promise<void> {
        await Promise.all(
            activityIds.map((id) =>
                api.put(`/assessments/${assessmentId}/activity/${id}/delete`),
            ),
        );
    },

    async bulkUpdateActivities(
        assessmentId: string,
        activityIds: string[],
        data: Partial<ActivityUpdate>,
    ): Promise<void> {
        await Promise.all(
            activityIds.map((id) =>
                api.put(`/assessments/${assessmentId}/activity/${id}`, data),
            ),
        );
    },

    async bulkMoveToGroup(
        assessmentId: string,
        activityIds: string[],
        groupId: string | null,
    ): Promise<void> {
        const data: ActivityGroupUpdate = { activity_group_id: groupId };
        await Promise.all(
            activityIds.map((id) =>
                api.put(
                    `/assessments/${assessmentId}/activity/${id}/activity_group`,
                    data,
                ),
            ),
        );
    },

    async assignDynamicEvaluationQuestions(
        assessmentId: string,
        activityId: string,
        questions: DynamicEvaluationQuestionAssign[],
    ): Promise<ActivityRead> {
        const response = await api.put<ActivityRead>(
            `/assessments/${assessmentId}/activity/${activityId}/dynamic_evaluation_questions`,
            questions,
        );
        return response.data;
    },

    async getActivityHistoryList(
        assessmentId: string,
        activityId: string,
    ): Promise<ActivityHistoryRead[]> {
        const response = await api.get<ActivityHistoryRead[]>(
            `/assessments/${assessmentId}/activity/${activityId}/version`,
        );
        return response.data;
    },

    async getActivityHistoryVersion(
        assessmentId: string,
        activityId: string,
        versionId: string,
    ): Promise<ActivityHistoryRead> {
        const response = await api.get<ActivityHistoryRead>(
            `/assessments/${assessmentId}/activity/${activityId}/version/${versionId}`,
        );
        return response.data;
    },
};

export type ActivityGroupQueryParams = {
    query?: string;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
};

export const activityGroupService = {
    async getGroups(
        assessmentId: string,
        params?: ActivityGroupQueryParams,
    ): Promise<ActivityGroupRead[]> {
        const response = await api.get<ActivityGroupRead[]>(
            `/assessments/${assessmentId}/activity_group/`,
            { params },
        );
        return response.data;
    },

    async getGroup(
        assessmentId: string,
        groupId: string,
    ): Promise<ActivityGroupRead> {
        const response = await api.get<ActivityGroupRead>(
            `/assessments/${assessmentId}/activity_group/${groupId}`,
        );
        return response.data;
    },

    async createGroup(
        assessmentId: string,
        data: ActivityGroupBase,
    ): Promise<ActivityGroupRead> {
        const response = await api.post<ActivityGroupRead>(
            `/assessments/${assessmentId}/activity_group/`,
            data,
        );
        return response.data;
    },

    async updateGroup(
        assessmentId: string,
        groupId: string,
        data: ActivityGroupBase,
    ): Promise<ActivityGroupRead> {
        const response = await api.put<ActivityGroupRead>(
            `/assessments/${assessmentId}/activity_group/${groupId}`,
            data,
        );
        return response.data;
    },

    async deleteGroup(assessmentId: string, groupId: string): Promise<void> {
        await api.delete(
            `/assessments/${assessmentId}/activity_group/${groupId}`,
        );
    },

    async toggleDeleteGroup(
        assessmentId: string,
        groupId: string,
    ): Promise<void> {
        await api.put(
            `/assessments/${assessmentId}/activity_group/${groupId}/delete`,
        );
    },

    async toggleVisibleGroup(
        assessmentId: string,
        groupId: string,
    ): Promise<void> {
        await api.put(
            `/assessments/${assessmentId}/activity_group/${groupId}/visible`,
        );
    },

    async getGroupActivities(
        assessmentId: string,
        groupId: string,
    ): Promise<ActivityRead[]> {
        const response = await api.get<ActivityRead[]>(
            `/assessments/${assessmentId}/activity_group/${groupId}/activities`,
        );
        return response.data;
    },

    async reorderGroups(
        assessmentId: string,
        groupIds: string[],
    ): Promise<MessageResponse> {
        const response = await api.put<MessageResponse>(
            `/assessments/${assessmentId}/activity_group/reorder`,
            { activity_group_ids: groupIds },
        );
        return response.data;
    },

    async reorderActivities(
        assessmentId: string,
        groupId: string,
        activityIds: string[],
    ): Promise<MessageResponse> {
        const response = await api.put<MessageResponse>(
            `/assessments/${assessmentId}/activity_group/${groupId}/reorder`,
            { activity_ids: activityIds },
        );
        return response.data;
    },
};
