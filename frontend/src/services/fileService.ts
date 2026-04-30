import type {
    FileRead,
    FileUploadResponse,
    MessageResponse,
} from '@/types/utils';
import { api } from './api';

export const fileService = {
    async getFiles(
        assessmentId: string,
        activityId: string,
    ): Promise<FileRead[]> {
        const response = await api.get<FileRead[]>(
            `/assessments/${assessmentId}/activity/${activityId}/files`,
        );
        return response.data;
    },

    async uploadFile(
        assessmentId: string,
        activityId: string,
        file: File,
    ): Promise<FileUploadResponse> {
        const formData = new FormData();
        formData.append('file', file);
        const response = await api.post<FileUploadResponse>(
            `/assessments/${assessmentId}/activity/${activityId}/upload`,
            formData,
            { headers: { 'Content-Type': 'multipart/form-data' } },
        );
        return response.data;
    },

    async deleteFile(
        assessmentId: string,
        activityId: string,
        fileId: string,
    ): Promise<MessageResponse> {
        const response = await api.delete<MessageResponse>(
            `/assessments/${assessmentId}/activity/${activityId}/files/${fileId}`,
        );
        return response.data;
    },

    async downloadFile(
        assessmentId: string,
        activityId: string,
        fileId: string,
        filename: string,
    ): Promise<void> {
        const response = await api.get(
            `/assessments/${assessmentId}/activity/${activityId}/files/${fileId}/download`,
            { responseType: 'blob' },
        );
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', filename);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
    },
};
