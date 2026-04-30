<script setup lang="ts">
import {
    ArcElement,
    BarElement,
    CategoryScale,
    Chart as ChartJS,
    Filler,
    Legend,
    LinearScale,
    LineElement,
    PointElement,
    RadialLinearScale,
    Title,
    Tooltip,
} from 'chart.js';
import { Loader2 } from 'lucide-vue-next';
import { computed, onMounted } from 'vue';
import { Bar as BarChart, Doughnut, Radar } from 'vue-chartjs';
import { useRoute } from 'vue-router';
import MitreHeatmap from '@/components/assessment/MitreHeatmap.vue';
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from '@/components/ui/card';
import { useAutoRefresh } from '@/composables/useAutoRefresh';
import { useAssessmentStatisticsStore } from '@/stores/assessmentStatistics';

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
    ArcElement,
    RadialLinearScale,
    PointElement,
    LineElement,
    Filler,
);

const route = useRoute();
const assessmentId = route.params.id as string;
const store = useAssessmentStatisticsStore();

onMounted(() => {
    store.fetchStatistics(assessmentId);
});

useAutoRefresh(() => store.fetchStatistics(assessmentId));

const STATE_COLORS: Record<string, string> = {
    Pending: '#71717a', // text-muted-foreground
    'Waiting Red': '#ef4444', // text-red-500
    'Waiting Blue': '#3b82f6', // text-blue-500
    Ready: '#14b8a6', // text-teal-500
    'In Progress': '#f97316', // text-orange-500
    'In Evaluation': '#a855f7', // text-purple-500
    Completed: '#16a34a', // text-green-600
    Cancelled: '#eab308', // text-yellow-500
};

const centerTextPlugin = {
    id: 'centerText',
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    beforeDraw(chart: any) {
        if (chart.config.type !== 'doughnut') return;
        const { ctx } = chart;
        const meta = chart.getDatasetMeta(0);
        if (!meta.data?.length) return;

        const total = chart.data.datasets[0].data.reduce(
            (a: number, b: number) => a + b,
            0,
        );
        if (total === 0) return;

        const centerX = meta.data[0].x;
        const centerY = meta.data[0].y;

        ctx.save();

        const styles = getComputedStyle(document.documentElement);

        ctx.fillStyle =
            styles.getPropertyValue('--foreground').trim() || '#09090b';
        ctx.font = 'bold 36px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(total.toString(), centerX, centerY - 10);

        ctx.fillStyle =
            styles.getPropertyValue('--muted-foreground').trim() || '#71717a';
        ctx.font = '14px sans-serif';
        ctx.fillText('Total', centerX, centerY + 20);

        ctx.restore();
    },
};

const stateChartData = computed(() => {
    if (!store.statistics) return { labels: [], datasets: [] };
    const labels = store.statistics.state_distribution.map(
        (item) => item.state,
    );
    const data = store.statistics.state_distribution.map((item) => item.count);
    const backgroundColors = labels.map(
        (state) => STATE_COLORS[state] || '#9ca3af',
    );
    return {
        labels,
        datasets: [
            {
                data,
                backgroundColor: backgroundColors,
                hoverOffset: 4,
                borderWidth: 0,
            },
        ],
    };
});

const stateChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '60%',
    plugins: {
        legend: {
            position: 'right' as const,
        },
        tooltip: {
            callbacks: {
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                label: (context: any) => {
                    let label = context.label || '';
                    if (label) {
                        label += ': ';
                    }
                    if (context.parsed !== null) {
                        const total = context.dataset.data.reduce(
                            (a: number, b: number) => a + b,
                            0,
                        );
                        label +=
                            context.parsed +
                            ' (' +
                            ((context.parsed * 100) / total).toFixed(1) +
                            '%)';
                    }
                    return label;
                },
            },
        },
    },
};

// --- Chart 3: Priority Breakdown (Horizontal Bar) ---
const PRIORITY_COLORS: Record<string, string> = {
    Critical: '#dc2626',
    High: '#ea580c',
    Medium: '#ca8a04',
    Low: '#16a34a',
    None: '#9ca3af',
};

const priorityChartData = computed(() => {
    if (!store.statistics) return { labels: [], datasets: [] };
    const items = [...store.statistics.priority_breakdown];
    return {
        labels: items.map((i) => i.priority),
        datasets: [
            {
                data: items.map((i) => i.count),
                backgroundColor: items.map(
                    (i) => PRIORITY_COLORS[i.priority] ?? '#7c3aed', // Fallback to same purple
                ),
                borderRadius: 4,
                maxBarThickness: 32,
            },
        ],
    };
});

const priorityChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: 'y' as const,
    plugins: {
        legend: {
            display: false,
        },
    },
};

// --- Chart 4a: Overarching MITRE Tactic Radar Chart ---
const mitreOverallRadarChart = computed(() => {
    if (
        !store.statistics?.mitre_overall_tactic_scores ||
        store.statistics.mitre_overall_tactic_scores.length === 0
    )
        return null;

    const tactics = store.statistics.mitre_overall_tactic_scores;
    const labels = tactics.map((t) => t.tactic);

    return {
        labels,
        datasets: [
            {
                label: 'Overall Score',
                data: tactics.map((t) => t.overall_score ?? 0),
                backgroundColor: 'rgba(124, 58, 237, 0.2)', // Purple
                borderColor: '#7c3aed',
                pointBackgroundColor: '#7c3aed',
            },
            {
                label: 'Expected Logged',
                data: tactics.map((t) => t.expected_logged_score ?? 0),
                backgroundColor: 'transparent',
                borderColor: '#3b82f6',
                borderDash: [5, 5],
                pointBackgroundColor: '#3b82f6',
                hidden: true,
            },
            {
                label: 'Actual Logged',
                data: tactics.map((t) => t.logged_score ?? 0),
                backgroundColor: 'rgba(59, 130, 246, 0.4)', // Blue
                borderColor: '#3b82f6',
                pointBackgroundColor: '#3b82f6',
                hidden: true,
            },
            {
                label: 'Expected Prevented',
                data: tactics.map((t) => t.expected_prevented_score ?? 0),
                backgroundColor: 'transparent',
                borderColor: '#16a34a',
                borderDash: [5, 5],
                pointBackgroundColor: '#16a34a',
                hidden: true,
            },
            {
                label: 'Actual Prevented',
                data: tactics.map((t) => t.prevented_score ?? 0),
                backgroundColor: 'rgba(22, 163, 74, 0.4)', // Green
                borderColor: '#16a34a',
                pointBackgroundColor: '#16a34a',
                hidden: true,
            },
            {
                label: 'Expected Alerted',
                data: tactics.map((t) => t.expected_alerted_score ?? 0),
                backgroundColor: 'transparent',
                borderColor: '#ea580c',
                borderDash: [5, 5],
                pointBackgroundColor: '#ea580c',
                hidden: true,
            },
            {
                label: 'Actual Alerted',
                data: tactics.map((t) => t.alerted_score ?? 0),
                backgroundColor: 'rgba(234, 88, 12, 0.4)', // Orange
                borderColor: '#ea580c',
                pointBackgroundColor: '#ea580c',
                hidden: true,
            },
            {
                label: 'Expected Notified',
                data: tactics.map(
                    (t) => t.expected_stakeholder_notified_score ?? 0,
                ),
                backgroundColor: 'transparent',
                borderColor: '#dc2626',
                borderDash: [5, 5],
                pointBackgroundColor: '#dc2626',
                hidden: true,
            },
            {
                label: 'Actual Notified',
                data: tactics.map((t) => t.stakeholder_notified_score ?? 0),
                backgroundColor: 'rgba(220, 38, 38, 0.4)', // Red
                borderColor: '#dc2626',
                pointBackgroundColor: '#dc2626',
                hidden: true,
            },
        ],
    };
});

// --- Chart 4b: MITRE Tactic Radar Charts ---
const mitreRadarCharts = computed(() => {
    if (!store.statistics?.mitre_tactic_scores) return [];

    return store.statistics.mitre_tactic_scores.map((tacticItem) => {
        const labels = tacticItem.techniques.map((t) => t.technique);

        // Colors for 5 datasets
        return {
            tacticName: tacticItem.tactic,
            data: {
                labels,
                datasets: [
                    {
                        label: 'Overall Score',
                        data: tacticItem.techniques.map(
                            (t) => t.overall_score ?? 0,
                        ),
                        backgroundColor: 'rgba(124, 58, 237, 0.2)', // Purple
                        borderColor: '#7c3aed',
                        pointBackgroundColor: '#7c3aed',
                    },
                    {
                        label: 'Expected Logged',
                        data: tacticItem.techniques.map(
                            (t) => t.expected_logged_score ?? 0,
                        ),
                        backgroundColor: 'transparent',
                        borderColor: '#3b82f6',
                        borderDash: [5, 5],
                        pointBackgroundColor: '#3b82f6',
                        hidden: true,
                    },
                    {
                        label: 'Actual Logged',
                        data: tacticItem.techniques.map(
                            (t) => t.logged_score ?? 0,
                        ),
                        backgroundColor: 'rgba(59, 130, 246, 0.4)', // Blue
                        borderColor: '#3b82f6',
                        pointBackgroundColor: '#3b82f6',
                        hidden: true,
                    },
                    {
                        label: 'Expected Prevented',
                        data: tacticItem.techniques.map(
                            (t) => t.expected_prevented_score ?? 0,
                        ),
                        backgroundColor: 'transparent',
                        borderColor: '#16a34a',
                        borderDash: [5, 5],
                        pointBackgroundColor: '#16a34a',
                        hidden: true,
                    },
                    {
                        label: 'Actual Prevented',
                        data: tacticItem.techniques.map(
                            (t) => t.prevented_score ?? 0,
                        ),
                        backgroundColor: 'rgba(22, 163, 74, 0.4)', // Green
                        borderColor: '#16a34a',
                        pointBackgroundColor: '#16a34a',
                        hidden: true,
                    },
                    {
                        label: 'Expected Alerted',
                        data: tacticItem.techniques.map(
                            (t) => t.expected_alerted_score ?? 0,
                        ),
                        backgroundColor: 'transparent',
                        borderColor: '#ea580c',
                        borderDash: [5, 5],
                        pointBackgroundColor: '#ea580c',
                        hidden: true,
                    },
                    {
                        label: 'Actual Alerted',
                        data: tacticItem.techniques.map(
                            (t) => t.alerted_score ?? 0,
                        ),
                        backgroundColor: 'rgba(234, 88, 12, 0.4)', // Orange
                        borderColor: '#ea580c',
                        pointBackgroundColor: '#ea580c',
                        hidden: true,
                    },
                    {
                        label: 'Expected Notified',
                        data: tacticItem.techniques.map(
                            (t) => t.expected_stakeholder_notified_score ?? 0,
                        ),
                        backgroundColor: 'transparent',
                        borderColor: '#dc2626',
                        borderDash: [5, 5],
                        pointBackgroundColor: '#dc2626',
                        hidden: true,
                    },
                    {
                        label: 'Actual Notified',
                        data: tacticItem.techniques.map(
                            (t) => t.stakeholder_notified_score ?? 0,
                        ),
                        backgroundColor: 'rgba(220, 38, 38, 0.4)', // Red
                        borderColor: '#dc2626',
                        pointBackgroundColor: '#dc2626',
                        hidden: true,
                    },
                ],
            },
        };
    });
});

const radarChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
        r: {
            angleLines: {
                display: true,
                color: 'rgba(156, 163, 175, 0.2)', // Gray-400
            },
            grid: {
                color: 'rgba(156, 163, 175, 0.2)',
            },
            pointLabels: {
                font: {
                    size: 11,
                },
            },
            suggestedMin: 0,
            min: -25,
            suggestedMax: 100,
            ticks: {
                stepSize: 25,
                backdropColor: 'transparent',
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                callback: (value: any) => {
                    if (value < 0) return '';
                    return `${value}%`;
                },
            },
        },
    },
    plugins: {
        legend: {
            position: 'top' as const,
            labels: {
                usePointStyle: true,
                boxWidth: 8,
                boxHeight: 8,
                padding: 30,
            },
        },
        tooltip: {
            callbacks: {
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                label: (context: any) =>
                    `${context.dataset.label}: ${Math.round(context.raw as number)}%`,
            },
        },
    },
};
// --- Metric 4: Average Coverage Score ---
function getScoreColor(score: number | null | undefined): string {
    if (score == null) return 'text-muted-foreground';
    const num = Math.round(score);
    if (num === 100) return 'text-green-600';
    if (num >= 25) return 'text-yellow-500';
    return 'text-red-500';
}

function getScoreDisplay(score: number | null | undefined): string {
    if (score == null) return 'N/A';
    return `${Math.round(score)}`;
}

const averageCoverageColor = computed(() =>
    getScoreColor(store.statistics?.average_coverage_score),
);
const averageCoverageDisplay = computed(() =>
    getScoreDisplay(store.statistics?.average_coverage_score),
);

const priorityScores = computed(
    () => store.statistics?.average_coverage_scores_by_priority || [],
);

// Helper to format seconds into readable duration (e.g. "1h 23m")
function formatSecondsToDuration(seconds: number | null | undefined): string {
    if (seconds == null) return 'N/A';
    if (seconds < 60) return `${Math.floor(seconds)}s`;

    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);

    if (h > 0) return `${h}h ${m}m`;
    return `${m}m ${s}s`;
}

// --- Chart 5: Mean Time Metrics (MTTD / MTTR) ---
const meanTimeChartData = computed(() => {
    if (!store.statistics?.mean_time_metrics)
        return { labels: [], datasets: [] };
    const items = [...store.statistics.mean_time_metrics];

    return {
        labels: items.map((i) => i.priority),
        datasets: [
            {
                label: 'Mean Time to Detect',
                data: items.map((i) => i.mean_time_to_detect_seconds ?? 0),
                backgroundColor: '#3b82f6', // Blue
                borderRadius: 4,
            },
            {
                label: 'Mean Time to Notify Stakeholder',
                data: items.map((i) => i.mean_time_to_respond_seconds ?? 0),
                backgroundColor: '#7c3aed', // Purple
                borderRadius: 4,
            },
        ],
    };
});

const meanTimeChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: 'y' as const,
    scales: {
        x: {
            stacked: true,
            ticks: {
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                callback: (value: any) => formatSecondsToDuration(value),
            },
        },
        y: {
            stacked: true,
        },
    },
    plugins: {
        tooltip: {
            callbacks: {
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                label: (context: any) =>
                    `${context.dataset.label}: ${formatSecondsToDuration(context.raw as number)}`,
            },
        },
    },
};

// --- Chart 6: Expected vs Actual Severity Accuracy ---
const SEVERITY_ACCURACY_COLORS = {
    Informational: '#9ca3af', // gray-400
    Low: '#3b82f6', // blue-500
    Medium: '#eab308', // yellow-500
    High: '#f97316', // orange-500
    Critical: '#ef4444', // red-500
    'Missed/None': '#1f2937', // gray-800
};

const severityAccuracyChartData = computed(() => {
    if (!store.statistics?.severity_accuracy)
        return { labels: [], datasets: [] };
    const items = store.statistics.severity_accuracy;

    return {
        labels: items.map((i) => i.expected_severity),
        datasets: [
            {
                label: 'Informational',
                data: items.map((i) => i.actual_informational),
                backgroundColor: SEVERITY_ACCURACY_COLORS.Informational,
            },
            {
                label: 'Low',
                data: items.map((i) => i.actual_low),
                backgroundColor: SEVERITY_ACCURACY_COLORS.Low,
            },
            {
                label: 'Medium',
                data: items.map((i) => i.actual_medium),
                backgroundColor: SEVERITY_ACCURACY_COLORS.Medium,
            },
            {
                label: 'High',
                data: items.map((i) => i.actual_high),
                backgroundColor: SEVERITY_ACCURACY_COLORS.High,
            },
            {
                label: 'Critical',
                data: items.map((i) => i.actual_critical),
                backgroundColor: SEVERITY_ACCURACY_COLORS.Critical,
            },
            {
                label: 'Missed / None',
                data: items.map((i) => i.actual_none),
                backgroundColor: SEVERITY_ACCURACY_COLORS['Missed/None'],
            },
        ],
    };
});

const severityAccuracyChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
        x: {
            stacked: true,
        },
        y: {
            stacked: true,
            ticks: {
                stepSize: 1,
            },
        },
    },
    plugins: {
        legend: {
            position: 'top' as const,
        },
    },
};
</script>

<template>
    <div class="flex flex-col h-full">
        <!-- Content -->
        <div class="flex-1 overflow-y-auto">
            <div
                v-if="store.loading"
                class="flex items-center justify-center h-64"
            >
                <Loader2
                    class="h-8 w-8 animate-spin text-muted-foreground"
                />
            </div>

            <div
                v-else-if="store.statistics"
                class="container mx-auto px-6 py-8 grid grid-cols-1 lg:grid-cols-2 gap-6 items-stretch"
            >
                <Card class="flex flex-col h-full">
                    <CardHeader>
                        <CardTitle>Activity State Distribution</CardTitle>
                        <CardDescription>
                            Distribution of all visible activities by their current workflow
                            state.
                        </CardDescription>
                    </CardHeader>
                    <CardContent class="flex-1">
                        <div class="h-64 w-full">
                            <Doughnut
                                :data="stateChartData"
                                :options="stateChartOptions"
                                :plugins="[centerTextPlugin]"
                            />
                        </div>
                    </CardContent>
                </Card>

                <!-- 2. Average Coverage Score -->
                <Card class="flex flex-col h-full overflow-hidden">
                    <div class="flex flex-col h-full">
                        <!-- Top part: Overall Average -->
                        <div class="flex-1 flex flex-col p-6">
                            <div class="space-y-1.5 mb-4">
                                <CardTitle>Average Coverage Score</CardTitle>
                                <CardDescription>
                                    The average coverage score across all visible and completed activities. Below by activity priority.
                                </CardDescription>
                            </div>
                            <div class="flex-1 flex items-center justify-center min-h-[140px]">
                                <div :class="['text-7xl font-bold', averageCoverageColor]">
                                    {{ averageCoverageDisplay }}
                                </div>
                            </div>
                        </div>
                        
                        <!-- Bottom part: Priority Breakdown -->
                        <div class="grid grid-cols-4 border-t divide-x bg-muted/20">
                            <div 
                                v-for="item in priorityScores" 
                                :key="item.priority"
                                class="flex flex-col items-center justify-center p-4"
                            >
                                <span class="text-xs text-muted-foreground font-medium uppercase tracking-wider mb-1">{{ item.priority }}</span>
                                <span :class="['text-xl font-bold', getScoreColor(item.average_score)]">
                                    {{ getScoreDisplay(item.average_score) }}
                                </span>
                            </div>
                        </div>
                    </div>
                </Card>

                <Card class="flex flex-col h-full lg:col-span-full">
                    <CardHeader>
                        <CardTitle>Activity Priority Breakdown</CardTitle>
                        <CardDescription>
                            Number of visible and completed activities grouped by priority level.
                        </CardDescription>
                    </CardHeader>
                    <CardContent class="flex-1">
                        <div class="h-64 w-full">
                            <BarChart
                                :data="priorityChartData"
                                :options="priorityChartOptions"
                            />
                        </div>
                    </CardContent>
                </Card>

                <!-- MITRE ATT&CK Heatmap -->
                <Card 
                    v-if="store.statistics?.mitre_tactic_scores?.length"
                    class="flex flex-col h-full lg:col-span-full"
                >
                    <CardHeader>
                        <CardTitle>MITRE ATT&CK Navigator Matrix</CardTitle>
                        <CardDescription>
                            Heatmap of aggregated coverage scores per technique.
                        </CardDescription>
                    </CardHeader>
                    <CardContent class="flex-1 overflow-hidden p-4">
                        <MitreHeatmap :data="store.statistics.mitre_tactic_scores" />
                    </CardContent>
                </Card>

                <!-- Overarching MITRE Tactic Radar Chart -->
                <Card 
                    v-if="mitreOverallRadarChart"
                    class="flex flex-col h-full min-h-[500px] lg:col-span-full"
                >
                    <CardHeader>
                        <CardTitle>Overarching MITRE Tactics</CardTitle>
                        <CardDescription>
                            Average coverage scores aggregated across all techniques within each Tactic. Click legends to toggle overlays.
                        </CardDescription>
                    </CardHeader>
                    <CardContent class="flex-1 flex flex-col items-center justify-center p-4">
                        <div class="h-[600px] w-full max-w-4xl">
                            <Radar
                                :data="mitreOverallRadarChart"
                                :options="radarChartOptions"
                            />
                        </div>
                    </CardContent>
                </Card>

                <!-- MITRE Tactic Radar Charts -->
                <Card 
                    v-for="(chart, index) in mitreRadarCharts" 
                    :key="index"
                    class="flex flex-col h-full min-h-[500px] lg:col-span-full"
                >
                    <CardHeader>
                        <CardTitle>{{ chart.tacticName }}</CardTitle>
                        <CardDescription>
                            Coverage scores per technique. Click legends to toggle overlays.
                        </CardDescription>
                    </CardHeader>
                    <CardContent class="flex-1 flex flex-col items-center justify-center p-4">
                        <div class="h-[600px] w-full max-w-4xl">
                            <Radar
                                :data="chart.data"
                                :options="radarChartOptions"
                            />
                        </div>
                    </CardContent>
                </Card>

                <!-- Mean Time Metrics -->
                <Card class="flex flex-col h-full lg:col-span-full">
                    <CardHeader>
                        <CardTitle>Mean Time to Detect / Notify Stakeholder</CardTitle>
                        <CardDescription>
                            Average chronological duration taken organized by Activity Priority.
                        </CardDescription>
                    </CardHeader>
                    <CardContent class="flex-1">
                        <div class="h-96 w-full">
                            <BarChart
                                :data="meanTimeChartData"
                                :options="meanTimeChartOptions"
                            />
                        </div>
                    </CardContent>
                </Card>

                <!-- Severity Accuracy -->
                <Card class="flex flex-col h-full lg:col-span-full">
                    <CardHeader>
                        <CardTitle>Alert Severity Accuracy</CardTitle>
                        <CardDescription>
                            Comparison of the Red Team's expected severity vs the Blue Teams's triggered alert severity.
                        </CardDescription>
                    </CardHeader>
                    <CardContent class="flex-1">
                        <div class="h-96 w-full">
                            <BarChart
                                :data="severityAccuracyChartData"
                                :options="severityAccuracyChartOptions"
                            />
                        </div>
                    </CardContent>
                </Card>
            </div>

            <div
                v-else
                class="flex items-center justify-center h-64 text-muted-foreground text-sm"
            >
                No statistics available.
            </div>
        </div>
    </div>
</template>
