import { computed, onMounted, ref } from 'vue';
import { mitreService } from '@/services/mitreService';
import type { TacticWithTechniques, TechniqueBase } from '@/types/utils';

export function useMitre() {
    const tactics = ref<TacticWithTechniques[]>([]);
    const loading = ref(false);

    const tacticOptions = computed(() =>
        tactics.value.map((tactic) => ({
            value: tactic.mitre_id,
            label: `${tactic.mitre_id} - ${tactic.name}`,
            techniques: tactic.techniques,
        })),
    );

    const getTechniqueOptions = (tacticId?: string) => {
        // If a tactic is selected, only return techniques for that tactic
        if (tacticId) {
            const tactic = tactics.value.find((t) => t.mitre_id === tacticId);
            if (tactic) {
                return tactic.techniques
                    .map((tech) => ({
                        value: tech.mitre_id,
                        label: `${tech.mitre_id} - ${tech.name}`,
                    }))
                    .sort((a, b) => a.label.localeCompare(b.label));
            }
            return [];
        }

        // Always return all techniques from all tactics to allow free selection
        const allTechniques = new Map<string, TechniqueBase>();
        tactics.value.forEach((tactic) => {
            tactic.techniques.forEach((tech) => {
                allTechniques.set(tech.mitre_id, tech);
            });
        });
        return Array.from(allTechniques.values())
            .map((tech) => ({
                value: tech.mitre_id,
                label: `${tech.mitre_id} - ${tech.name}`,
            }))
            .sort((a, b) => a.label.localeCompare(b.label));
    };

    const getTacticOptionsForTechnique = () => {
        // Always return all tactics to allow free selection
        return tacticOptions.value;
    };

    async function fetchTactics() {
        loading.value = true;
        try {
            tactics.value = await mitreService.getTacticsWithTechniques({
                sort_by: 'mitre_id',
                sort_order: 'asc',
            });
        } finally {
            loading.value = false;
        }
    }

    onMounted(() => {
        fetchTactics();
    });

    return {
        tactics,
        loading,
        tacticOptions,
        getTechniqueOptions,
        getTacticOptionsForTechnique,
        fetchTactics,
    };
}
