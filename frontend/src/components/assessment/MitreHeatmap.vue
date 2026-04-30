<script setup lang="ts">
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from '@/components/ui/tooltip';
import type {
    MitreTacticScoreItem,
    MitreTechniqueScoreItem,
} from '@/types/utils';

const props = defineProps<{
    data: MitreTacticScoreItem[];
}>();

// Helps us color the background dynamically.
function getTechniqueStyle(technique: MitreTechniqueScoreItem) {
    if (technique.overall_score == null) {
        return {
            backgroundColor: 'transparent',
            borderColor: 'var(--border)',
            color: 'var(--muted-foreground)',
        };
    }

    // Calculate color based on score (0 to 100).
    // 100 = Green (#22c55e)
    // 50 = Yellow (#eab308)
    // 0 = Red (#ef4444)
    const baseScore = Math.min(Math.max(technique.overall_score, 0), 100);

    let r, g, b;
    if (baseScore >= 50) {
        // Green to Yellow (100 to 50)
        // Red increases from 34 to 234
        // Green decreases from 197 to 179
        // Blue decreases from 94 to 8
        const percentage = (baseScore - 50) / 50; // 0 to 1 (50=0, 100=1)
        r = Math.round(234 - 200 * percentage);
        g = Math.round(179 + 18 * percentage);
        b = Math.round(8 + 86 * percentage);
    } else {
        // Yellow to Red (50 to 0)
        // Red increases from 234 to 239
        // Green decreases from 179 to 68
        // Blue stays around 8 to 68
        const percentage = baseScore / 50; // 0 to 1 (0=0, 50=1)
        r = Math.round(239 - 5 * percentage);
        g = Math.round(68 + 111 * percentage);
        b = Math.round(68 - 60 * percentage);
    }

    // Add a slight alpha for UI softness
    const opacity = 0.8;

    return {
        backgroundColor: `rgba(${r}, ${g}, ${b}, ${opacity})`,
        borderColor: `rgba(${r}, ${g}, ${b}, 1)`,
        color: baseScore < 30 || baseScore > 70 ? 'white' : 'var(--foreground)',
    };
}
</script>

<template>
    <div class="w-full overflow-x-auto pb-4 custom-scrollbar">
        <div class="flex gap-2 min-w-max">
            <!-- Tactic Column -->
            <div 
                v-for="tactic in data" 
                :key="tactic.tactic"
                class="flex flex-col w-[160px] flex-shrink-0"
            >
                <!-- Tactic Header -->
                <TooltipProvider :delayDuration="100">
                    <Tooltip>
                        <TooltipTrigger as-child>
                            <div class="bg-muted px-3 py-2 text-sm font-semibold text-center border-b-2 border-primary mb-2 truncate cursor-help">
                                {{ tactic.tactic }}
                            </div>
                        </TooltipTrigger>
                        <TooltipContent class="max-w-[300px] bg-popover text-popover-foreground border-2 shadow-xl">
                            <p class="font-semibold text-sm">{{ tactic.tactic }}</p>
                        </TooltipContent>
                    </Tooltip>
                </TooltipProvider>
                
                <!-- Techniques -->
                <div class="flex flex-col gap-1.5 flex-1">
                    <TooltipProvider v-for="technique in tactic.techniques" :key="technique.technique" :delayDuration="100">
                        <Tooltip>
                            <TooltipTrigger as-child>
                                <div 
                                    class="text-xs p-2 rounded border cursor-help transition-all hover:ring-2 hover:ring-primary hover:ring-offset-1 truncate text-center"
                                    :style="getTechniqueStyle(technique)"
                                >
                                    {{ technique.technique }}
                                </div>
                            </TooltipTrigger>
                            <TooltipContent side="right" class="max-w-[300px] p-0 overflow-hidden border-2 shadow-xl bg-popover text-popover-foreground">
                                <div class="bg-secondary/50 px-3 py-2 font-semibold text-sm border-b truncate">
                                    {{ technique.technique }}
                                </div>
                                <div class="px-3 py-2 space-y-2 text-xs">
                                     <div class="flex justify-between items-center bg-primary/10 -mx-3 px-3 py-1 font-semibold text-primary">
                                        <span>Overall Score</span>
                                        <span>{{ technique.overall_score != null ? Math.round(technique.overall_score) + '%' : 'N/A' }}</span>
                                    </div>
                                    <div class="grid grid-cols-2 gap-x-4 gap-y-1">
                                        <span class="text-muted-foreground">Expected Logged:</span>
                                        <span class="text-right font-mono">{{ technique.expected_logged_score != null ? Math.round(technique.expected_logged_score) + '%' : '-' }}</span>
                                        
                                        <span class="text-muted-foreground">Actual Logged:</span>
                                        <span class="text-right font-mono">{{ technique.logged_score != null ? Math.round(technique.logged_score) + '%' : '-' }}</span>
                                        
                                        <div class="col-span-2 border-t my-1"></div>
                                        
                                        <span class="text-muted-foreground">Expected Prevention:</span>
                                        <span class="text-right font-mono">{{ technique.expected_prevented_score != null ? Math.round(technique.expected_prevented_score) + '%' : '-' }}</span>
                                        
                                        <span class="text-muted-foreground">Actual Prevention:</span>
                                        <span class="text-right font-mono">{{ technique.prevented_score != null ? Math.round(technique.prevented_score) + '%' : '-' }}</span>
                                        
                                        <div class="col-span-2 border-t my-1"></div>
                                        
                                        <span class="text-muted-foreground">Expected Alerted:</span>
                                        <span class="text-right font-mono">{{ technique.expected_alerted_score != null ? Math.round(technique.expected_alerted_score) + '%' : '-' }}</span>

                                        <span class="text-muted-foreground">Actual Alerted:</span>
                                        <span class="text-right font-mono">{{ technique.alerted_score != null ? Math.round(technique.alerted_score) + '%' : '-' }}</span>
                                        
                                        <div class="col-span-2 border-t my-1"></div>
                                        
                                        <span class="text-muted-foreground">Exp Notified:</span>
                                        <span class="text-right font-mono">{{ technique.expected_stakeholder_notified_score != null ? Math.round(technique.expected_stakeholder_notified_score) + '%' : '-' }}</span>

                                        <span class="text-muted-foreground">Actual Notified:</span>
                                        <span class="text-right font-mono">{{ technique.stakeholder_notified_score != null ? Math.round(technique.stakeholder_notified_score) + '%' : '-' }}</span>
                                    </div>
                                </div>
                            </TooltipContent>
                        </Tooltip>
                    </TooltipProvider>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
/* Custom scrollbar to make it look cleaner */
.custom-scrollbar::-webkit-scrollbar {
    height: 8px;
}
.custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
    border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
    background: var(--muted-foreground);
    opacity: 0.5;
    border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: var(--primary);
}
</style>
