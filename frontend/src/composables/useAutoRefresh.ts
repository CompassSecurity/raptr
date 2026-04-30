import { onUnmounted, ref, watch } from 'vue';
import { usePreferencesStore } from '@/stores/preferences';

/**
 * Composable for auto-refresh functionality
 * @param refreshCallback - Function to call on each refresh
 * @returns Object with methods to control auto-refresh
 */
export function useAutoRefresh(refreshCallback: () => void | Promise<void>) {
    const preferencesStore = usePreferencesStore();
    const intervalId = ref<ReturnType<typeof setInterval> | null>(null);
    const isRefreshing = ref(false);

    const startAutoRefresh = () => {
        // Clear any existing interval
        stopAutoRefresh();

        if (!preferencesStore.autoRefreshEnabled) {
            return;
        }

        // Convert seconds to milliseconds
        const intervalMs = preferencesStore.autoRefreshInterval * 1000;

        intervalId.value = setInterval(async () => {
            if (isRefreshing.value) {
                return; // Skip if already refreshing
            }

            try {
                isRefreshing.value = true;
                await refreshCallback();
            } catch (error) {
                console.error('Auto-refresh error:', error);
            } finally {
                isRefreshing.value = false;
            }
        }, intervalMs);
    };

    const stopAutoRefresh = () => {
        if (intervalId.value) {
            clearInterval(intervalId.value);
            intervalId.value = null;
        }
    };

    // Watch for changes in auto-refresh settings
    watch(
        () => [
            preferencesStore.autoRefreshEnabled,
            preferencesStore.autoRefreshInterval,
        ],
        () => {
            if (preferencesStore.autoRefreshEnabled) {
                startAutoRefresh();
            } else {
                stopAutoRefresh();
            }
        },
        { immediate: true },
    );

    // Watch for manual refresh triggers
    watch(
        () => preferencesStore.manualRefreshTrigger,
        async (newVal, oldVal) => {
            // Check diff to ensure it's an actual trigger event (not just component mount initialization)
            if (newVal !== oldVal && !isRefreshing.value) {
                try {
                    isRefreshing.value = true;
                    await refreshCallback();
                } catch (error) {
                    console.error('Manual refresh error:', error);
                } finally {
                    isRefreshing.value = false;
                }
            }
        },
    );

    // Clean up on unmount
    onUnmounted(() => {
        stopAutoRefresh();
    });

    return {
        isRefreshing,
        startAutoRefresh,
        stopAutoRefresh,
    };
}
