import type {
    ActivityGroupTemplateRead,
    MessageResponse,
    PaginatedResponse,
} from '@/types/utils';
import { api } from './api';

export const activityGroupTemplateService = {
    async getActivityGroupTemplates(
        params?: Record<string, unknown>,
    ): Promise<PaginatedResponse<ActivityGroupTemplateRead>> {
        const response = await api.get<
            PaginatedResponse<ActivityGroupTemplateRead>
        >('/activity_group_template/', { params });
        return response.data;
    },

    async importActivityGroupTemplates(
        assessmentId: string,
        groupTemplateIds: string[],
    ): Promise<MessageResponse> {
        const response = await api.post<MessageResponse>(
            `/assessments/${assessmentId}/imports/activity_group_templates`,
            groupTemplateIds,
        );
        return response.data;
    },
};
