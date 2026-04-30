import type { AssessmentStatisticsResponse } from '@/types/utils';
import { api } from './api';

export const statisticsService = {
    async getAssessmentStatistics(
        assessmentId: string,
    ): Promise<AssessmentStatisticsResponse> {
        const response = await api.get<AssessmentStatisticsResponse>(
            `/assessments/${assessmentId}/statistics/`,
        );
        return response.data;
    },
};
