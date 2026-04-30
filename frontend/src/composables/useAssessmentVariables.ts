import { useSessionStorage } from '@vueuse/core';
import { computed } from 'vue';

export const useAssessmentVariables = (assessmentId: string) => {
    // Use sessionStorage key scoped to the assessment
    const variables = useSessionStorage<Record<string, string>>(
        `raptr-assessment-variables-${assessmentId}`,
        {},
    );

    /**
     * Replace placeholders in the format {{KEY}} with their values from the variables store.
     */
    const processContent = (content: string): string => {
        if (!content) return content;

        let processed = content;
        // Iterate over all variables and replace occurrences
        for (const [key, value] of Object.entries(variables.value)) {
            // Create a global regex for {{KEY}}
            // Escape key just in case, though usually keys are simple strings
            const escapedKey = key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            const regex = new RegExp(`{{${escapedKey}}}`, 'g');
            processed = processed.replace(regex, value);
        }

        return processed;
    };

    /**
     * Import variables from a JSON string.
     * Merges with existing variables.
     */
    const importVariables = (jsonContent: string): boolean => {
        try {
            const parsed = JSON.parse(jsonContent);

            // Basic validation: must be an object and values must be strings (or convertable)
            if (typeof parsed !== 'object' || parsed === null) {
                throw new Error('Invalid JSON format: Root must be an object');
            }

            const newVariables: Record<string, string> = {};

            for (const [key, value] of Object.entries(parsed)) {
                if (
                    typeof value === 'string' ||
                    typeof value === 'number' ||
                    typeof value === 'boolean'
                ) {
                    newVariables[key] = String(value);
                }
            }

            // Merge with existing variables
            variables.value = { ...variables.value, ...newVariables };
            return true;
        } catch (e) {
            console.error('Failed to parse variables JSON', e);
            return false;
        }
    };

    /**
     * Clear all variables for this assessment
     */
    const clearVariables = () => {
        variables.value = {};
    };

    const hasVariables = computed(
        () => Object.keys(variables.value).length > 0,
    );
    const variableCount = computed(() => Object.keys(variables.value).length);

    return {
        variables,
        processContent,
        importVariables,
        clearVariables,
        hasVariables,
        variableCount,
    };
};
