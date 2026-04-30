import type {
    ReportContextRequest,
    ReportGenerateRequest,
    ReportTemplateRead,
} from '@/types/utils';
import { api } from './api';

export const reportService = {
    async getReportTemplates(): Promise<ReportTemplateRead[]> {
        const response =
            await api.get<ReportTemplateRead[]>('/report_template/');
        return response.data;
    },

    async generateReport(
        assessmentId: string,
        data: ReportGenerateRequest,
    ): Promise<{ blob: Blob; filename: string }> {
        const response = await api.post(
            `/assessments/${assessmentId}/export/report/generate`,
            data,
            { responseType: 'blob' },
        );

        // Extract filename from Content-Disposition header if available
        const disposition = response.headers['content-disposition'] as
            | string
            | undefined;
        let filename = 'report';
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

    async exportMitreNavigator(
        assessmentId: string,
    ): Promise<{ blob: Blob; filename: string }> {
        const response = await api.post(
            `/assessments/${assessmentId}/export/mitre`,
            null,
            { responseType: 'blob' },
        );

        const disposition = response.headers['content-disposition'] as
            | string
            | undefined;
        let filename = 'mitre_attack_navigator_export.json';
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

    async getReportContext(
        assessmentId: string,
        data: ReportContextRequest,
    ): Promise<{ blob: Blob; filename: string }> {
        const response = await api.post(
            `/assessments/${assessmentId}/export/report/context`,
            data,
            { responseType: 'blob' },
        );

        const disposition = response.headers['content-disposition'] as
            | string
            | undefined;
        let filename = 'report_context.json';
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
};
