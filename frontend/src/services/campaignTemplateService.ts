import type {
    CampaignTemplateRead,
    MessageResponse,
    PaginatedResponse,
} from '@/types/utils';
import { api } from './api';

export const campaignTemplateService = {
    async getCampaignTemplates(
        params?: Record<string, unknown>,
    ): Promise<PaginatedResponse<CampaignTemplateRead>> {
        const response = await api.get<PaginatedResponse<CampaignTemplateRead>>(
            '/campaign_template/',
            { params },
        );
        return response.data;
    },

    async getCampaignTemplateById(
        campaignTemplateId: string,
    ): Promise<CampaignTemplateRead> {
        const response = await api.get<CampaignTemplateRead>(
            `/campaign_template/${campaignTemplateId}`,
        );
        return response.data;
    },

    async importCampaignTemplate(
        assessmentId: string,
        campaignTemplateId: string,
    ): Promise<MessageResponse> {
        const response = await api.post<MessageResponse>(
            `/assessments/${assessmentId}/imports/campaign_template`,
            null,
            { params: { campaign_template_id: campaignTemplateId } },
        );
        return response.data;
    },
};
