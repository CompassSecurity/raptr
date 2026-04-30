import type {
    EvaluationTemplateRead,
    PaginatedResponse,
    PaginationParams,
} from '@/types/utils';
import { api } from './api';

export const evaluationTemplateService = {
    async getAll(
        params?: PaginationParams,
    ): Promise<PaginatedResponse<EvaluationTemplateRead>> {
        const response = await api.get<
            PaginatedResponse<EvaluationTemplateRead>
        >('/evaluation_template/', { params });
        return response.data;
    },

    async getById(id: string): Promise<EvaluationTemplateRead> {
        const response = await api.get<EvaluationTemplateRead>(
            `/evaluation_template/${id}`,
        );
        return response.data;
    },
};
