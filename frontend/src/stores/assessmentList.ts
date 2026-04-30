import { defineStore } from 'pinia';
import { ref } from 'vue';
import { aclService } from '@/services/aclService';
import { assessmentService } from '@/services/assessmentService';
import type { AclBase, AssessmentRead, PaginationState } from '@/types/utils';

export const useAssessmentListStore = defineStore('assessmentList', () => {
    const assessments = ref<AssessmentRead[]>([]);
    const loading = ref(false);
    const pagination = ref<PaginationState>({
        total: 0,
        page: 1,
        size: 100,
        pages: 1,
    });

    async function fetchAssessments(params?: Record<string, unknown>) {
        loading.value = true;
        try {
            const data = await assessmentService.getAssessments(params);
            assessments.value = data.items;
            pagination.value = {
                total: data.total,
                page: data.page,
                size: data.size,
                pages: data.pages,
            };
        } finally {
            loading.value = false;
        }
    }

    async function createAssessment(
        data: import('@/types/utils').AssessmentBase,
    ) {
        loading.value = true;
        try {
            const result = await assessmentService.createAssessment(data);
            return result;
        } finally {
            loading.value = false;
        }
    }

    async function updateAssessment(
        id: string,
        data: import('@/types/utils').AssessmentBase,
    ) {
        loading.value = true;
        try {
            const result = await assessmentService.updateAssessment(id, data);
            return result;
        } finally {
            loading.value = false;
        }
    }

    async function deleteAssessment(id: string) {
        loading.value = true;
        try {
            await assessmentService.deleteAssessment(id);
        } finally {
            loading.value = false;
        }
    }

    async function fetchAssessmentAcls(assessmentId: string) {
        loading.value = true;
        try {
            return await aclService.getAssessmentAcls(assessmentId);
        } finally {
            loading.value = false;
        }
    }

    async function createAcl(data: AclBase) {
        loading.value = true;
        try {
            return await aclService.createAcl(data);
        } finally {
            loading.value = false;
        }
    }

    async function updateAcl(aclId: string, data: AclBase) {
        loading.value = true;
        try {
            return await aclService.updateAcl(aclId, data);
        } finally {
            loading.value = false;
        }
    }

    async function deleteAcl(aclId: string) {
        loading.value = true;
        try {
            await aclService.deleteAcl(aclId);
        } finally {
            loading.value = false;
        }
    }

    async function fetchUserAcls(userId: string) {
        loading.value = true;
        try {
            return await aclService.getUserAcls(userId);
        } finally {
            loading.value = false;
        }
    }

    return {
        assessments,
        pagination,
        loading,
        fetchAssessments,
        createAssessment,
        updateAssessment,
        deleteAssessment,
        fetchAssessmentAcls,
        fetchUserAcls,
        createAcl,
        updateAcl,
        deleteAcl,
    };
});
