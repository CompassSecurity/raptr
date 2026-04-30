import { defineStore } from 'pinia';
import { ref } from 'vue';
import { statisticsService } from '@/services/statisticsService';
import type { AssessmentStatisticsResponse } from '@/types/utils';

export const useAssessmentStatisticsStore = defineStore(
    'assessmentStatistics',
    () => {
        const statistics = ref<AssessmentStatisticsResponse | null>(null);
        const loading = ref(false);

        async function fetchStatistics(assessmentId: string) {
            loading.value = true;
            try {
                statistics.value =
                    await statisticsService.getAssessmentStatistics(
                        assessmentId,
                    );
            } finally {
                loading.value = false;
            }
        }

        function reset() {
            statistics.value = null;
        }

        return {
            statistics,
            loading,
            fetchStatistics,
            reset,
        };
    },
);
