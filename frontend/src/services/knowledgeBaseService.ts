import type { KnowledgeBaseRead, PaginatedResponse } from '@/types/utils';
import { api } from './api';

// KB-specific filter params (flat, not nested)
export interface KnowledgeBaseFilterParams {
    mitre_technique_id?: string;
    names?: string[];
    offset?: number;
    limit?: number;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
}

export const knowledgeBaseService = {
    async getKnowledgeBaseArticles(
        params?: KnowledgeBaseFilterParams,
    ): Promise<PaginatedResponse<KnowledgeBaseRead>> {
        const response = await api.get<PaginatedResponse<KnowledgeBaseRead>>(
            '/knowledge-base/',
            { params },
        );
        return response.data;
    },
};
