import type {
    AssessmentBase,
    AssessmentRead,
    DynamicEvaluationQuestionAssign,
    ImportResponse,
    PaginatedResponse,
} from '@/types/utils';
import { api } from './api';

export const assessmentService = {
    async getAssessments(
        params?: Record<string, unknown>,
    ): Promise<PaginatedResponse<AssessmentRead>> {
        const response = await api.get<PaginatedResponse<AssessmentRead>>(
            '/assessment/',
            { params },
        );
        return response.data;
    },

    async getAssessment(id: string): Promise<AssessmentRead> {
        const response = await api.get<AssessmentRead>(`/assessment/${id}`);
        return response.data;
    },

    async createAssessment(data: AssessmentBase): Promise<AssessmentRead> {
        const response = await api.post<AssessmentRead>('/assessment/', data);
        return response.data;
    },

    async updateAssessment(
        id: string,
        data: AssessmentBase,
    ): Promise<AssessmentRead> {
        const response = await api.put<AssessmentRead>(
            `/assessment/${id}`,
            data,
        );
        return response.data;
    },

    async deleteAssessment(id: string): Promise<void> {
        await api.delete(`/assessment/${id}`);
    },

    async updateDefaultEvaluationTemplates(
        assessmentId: string,
        questions: DynamicEvaluationQuestionAssign[],
    ): Promise<AssessmentRead> {
        const response = await api.put<AssessmentRead>(
            `/assessment/${assessmentId}/default_evaluation_templates`,
            questions,
        );
        return response.data;
    },

    async exportAssessment(
        assessmentId: string,
    ): Promise<{ blob: Blob; filename: string }> {
        const response = await api.post(
            `/assessments/${assessmentId}/export/assessment`,
            null,
            { responseType: 'blob' },
        );

        const disposition = response.headers['content-disposition'] as
            | string
            | undefined;
        let filename = 'assessment_export.zip';
        if (disposition) {
            const match = disposition.match(
                /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/,
            );
            if (match?.[1]) {
                filename = match[1].replace(/['"]/g, '');
            }
        }

        return { blob: response.data as Blob, filename };
    },

    async importAssessment(file: File): Promise<ImportResponse> {
        const formData = new FormData();
        formData.append('file', file);
        const response = await api.post<ImportResponse>(
            '/assessment/import',
            formData,
            {
                headers: { 'Content-Type': 'multipart/form-data' },
            },
        );
        return response.data;
    },
};
