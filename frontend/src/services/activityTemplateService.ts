import type {
    ActivityTemplateRead,
    MessageResponse,
    PaginatedResponse,
} from '@/types/utils';
import { api } from './api';

export const activityTemplateService = {
    /**
     * Get all activity templates with pagination and filtering
     */
    async getActivityTemplates(
        params?: Record<string, unknown>,
    ): Promise<PaginatedResponse<ActivityTemplateRead>> {
        const response = await api.get<PaginatedResponse<ActivityTemplateRead>>(
            '/activity_template/',
            { params },
        );
        return response.data;
    },

    /**
     * Import activity templates into an assessment
     */
    async importActivityTemplates(
        assessmentId: string,
        templateIds: string[],
    ): Promise<MessageResponse> {
        const response = await api.post<MessageResponse>(
            `/assessments/${assessmentId}/imports/activity_templates`,
            templateIds,
        );
        return response.data;
    },
};
