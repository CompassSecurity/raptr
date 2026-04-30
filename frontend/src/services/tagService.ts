import type {
    PaginatedResponse,
    PaginationParams,
    TagBase,
    TagRead,
} from '@/types/utils';
import { api } from './api';

export const tagService = {
    async getTags(
        assessmentId: string,
        params?: PaginationParams,
    ): Promise<PaginatedResponse<TagRead>> {
        const response = await api.get<PaginatedResponse<TagRead>>(
            `/assessments/${assessmentId}/tag/`,
            { params },
        );
        return response.data;
    },

    async createTag(assessmentId: string, data: TagBase): Promise<TagRead> {
        const response = await api.post<TagRead>(
            `/assessments/${assessmentId}/tag/`,
            data,
        );
        return response.data;
    },
};
