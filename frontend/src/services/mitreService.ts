import type {
    TacticBase,
    TacticWithTechniques,
    TechniqueBase,
} from '@/types/utils';
import { api } from './api';

export type MitreQueryParams = {
    query?: string;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
};

export const mitreService = {
    async getTacticsWithTechniques(
        params?: MitreQueryParams,
    ): Promise<TacticWithTechniques[]> {
        const response = await api.get<TacticWithTechniques[]>(
            '/mitre/tactics-with-techniques',
            { params },
        );
        return response.data;
    },

    async getTactics(params?: MitreQueryParams): Promise<TacticBase[]> {
        const response = await api.get<TacticBase[]>('/mitre/tactics', {
            params,
        });
        return response.data;
    },

    async getTechniques(params?: MitreQueryParams): Promise<TechniqueBase[]> {
        const response = await api.get<TechniqueBase[]>('/mitre/techniques', {
            params,
        });
        return response.data;
    },
};
