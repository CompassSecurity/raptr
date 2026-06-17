<script setup lang="ts">
import {
    Check,
    Cloud,
    Computer,
    Database,
    Globe,
    Hammer,
    Info,
    Network,
    Plus,
    Search,
    SearchCode,
    Settings2,
    Shield,
    ShieldCheck,
    User,
    Users,
    X,
} from '@lucide/vue';
import { computed, onMounted, ref, watch } from 'vue';
import ManageAssetsModal from '@/components/assessment/ManageAssetsModal.vue';
import { Button } from '@/components/ui/button';
import {
    Dialog,
    DialogContent,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from '@/components/ui/popover';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { assetService } from '@/services/assetService';
import type { AssetRead } from '@/types/utils';

const props = defineProps<{
    sources: AssetRead[];
    targets: AssetRead[];
    tools: AssetRead[];
    assessmentId: string;
    showOnlySources?: boolean;
    sourcesLabel?: string;
    compact?: boolean;
    readonly?: boolean;
    availableAssets?: AssetRead[];
    accentColor?: 'green' | 'orange' | 'purple' | 'blue';
}>();

const emit = defineEmits<{
    (e: 'update:sources', value: AssetRead[]): void;
    (e: 'update:targets', value: AssetRead[]): void;
    (e: 'update:tools', value: AssetRead[]): void;
    (e: 'assets-changed'): void;
}>();

const modalOpen = ref(false);
const localAssets = ref<AssetRead[]>([]);
const loading = ref(false);

const resolvedAssets = computed(
    () => props.availableAssets ?? localAssets.value,
);

// Sync prop to local when provided
watch(
    () => props.availableAssets,
    (val) => {
        if (val) localAssets.value = val;
    },
);
const searchQuery = ref('');
const activeTab = ref<'sources' | 'targets' | 'tools'>('sources');
const modalTab = ref<'select' | 'manage'>('select');
const manageAssetsModalOpen = ref(false);
const manageAssetsInitialView = ref<'list' | 'create'>('list');

const iconMap: Record<string, any> = {
    Cloud,
    Computer,
    Database,
    Shield,
    ShieldCheck,
    Users,
    Network,
    SearchCode,
    Hammer,
    User,
    Globe,
};

function getIconComponent(iconName: string | null | undefined) {
    return (iconName && iconMap[iconName]) || Computer;
}

const ACCENT_LABEL_CLASS: Record<string, string> = {
    green: 'text-green-600 dark:text-green-400',
    orange: 'text-orange-600 dark:text-orange-400',
    purple: 'text-purple-600 dark:text-purple-400',
    blue: 'text-blue-600 dark:text-blue-400',
};
const ACCENT_BORDER_CLASS: Record<string, string> = {
    green: 'border-l-green-500',
    orange: 'border-l-orange-500',
    purple: 'border-l-purple-500',
    blue: 'border-l-blue-700',
};
const DEFAULT_SECTION_ACCENT: Record<string, string> = {
    sources: 'green',
    targets: 'orange',
    tools: 'purple',
};
function accentFor(key: string): string {
    return props.accentColor ?? DEFAULT_SECTION_ACCENT[key] ?? 'green';
}

// Global asset fetch
async function fetchAssets() {
    loading.value = true;
    try {
        const data = await assetService.getAssets(props.assessmentId, {
            limit: 1000,
        });
        localAssets.value = data.items;
    } catch (e) {
        // Handle error
    } finally {
        loading.value = false;
    }
}

// Filter available assets for the modal list
const filteredAssets = computed(() => {
    let assets = resolvedAssets.value.filter((a) => !a.deleted);
    if (searchQuery.value.trim()) {
        const query = searchQuery.value.toLowerCase();
        assets = assets.filter((a) => {
            if (a.name.toLowerCase().includes(query)) return true;
            if (a.properties) {
                const propsString = JSON.stringify(a.properties).toLowerCase();
                if (propsString.includes(query)) return true;
            }
            return false;
        });
    }

    return assets.sort((a, b) => {
        const aSelected = isSelected(a.id, activeTab.value);
        const bSelected = isSelected(b.id, activeTab.value);
        if (aSelected && !bSelected) return -1;
        if (!aSelected && bSelected) return 1;
        return a.name.localeCompare(b.name);
    });
});

// Sections for display
const sections = computed(() => {
    if (props.showOnlySources) {
        return [
            {
                key: 'sources' as const,
                label: props.sourcesLabel || 'Sources',
                items: props.sources,
            },
        ];
    }
    return [
        { key: 'sources' as const, label: 'Sources', items: props.sources },
        { key: 'targets' as const, label: 'Targets', items: props.targets },
        { key: 'tools' as const, label: 'Tools', items: props.tools },
    ];
});

// Selection helpers
function getListForTab(tab: typeof activeTab.value) {
    if (tab === 'sources') return props.sources;
    if (tab === 'targets') return props.targets;
    return props.tools;
}

function updateListForTab(tab: typeof activeTab.value, list: AssetRead[]) {
    if (tab === 'sources') emit('update:sources', list);
    else if (tab === 'targets') emit('update:targets', list);
    else emit('update:tools', list);
}

function isSelected(assetId: string, tab: typeof activeTab.value) {
    return getListForTab(tab).some((a) => a.id === assetId);
}

function toggleSelection(asset: AssetRead) {
    const list = getListForTab(activeTab.value);
    const exists = list.some((a) => a.id === asset.id);

    let newList;
    if (exists) {
        newList = list.filter((a) => a.id !== asset.id);
    } else {
        newList = [...list, asset];
    }
    updateListForTab(activeTab.value, newList);
}

function removeAsset(assetId: string, type: 'sources' | 'targets' | 'tools') {
    let list;
    if (type === 'sources') list = props.sources;
    else if (type === 'targets') list = props.targets;
    else list = props.tools;

    const newList = list.filter((a) => a.id !== assetId);

    if (type === 'sources') emit('update:sources', newList);
    else if (type === 'targets') emit('update:targets', newList);
    else emit('update:tools', newList);
}

function openModal(tab?: 'sources' | 'targets' | 'tools' | Event) {
    modalOpen.value = true;
    modalTab.value = 'select'; // Reset to select tab
    activeTab.value = typeof tab === 'string' ? tab : 'sources';
    searchQuery.value = '';
    if (resolvedAssets.value.length === 0) {
        fetchAssets();
    }
}

function openManageAssets() {
    manageAssetsInitialView.value = 'list';
    manageAssetsModalOpen.value = true;
}

function openNewAsset() {
    manageAssetsInitialView.value = 'create';
    manageAssetsModalOpen.value = true;
}

async function handleAssetManagementSuccess(createdAsset?: AssetRead) {
    // Refresh assets after creating/editing
    await fetchAssets();

    if (createdAsset) {
        const list = getListForTab(activeTab.value);
        const assetToSelect =
            localAssets.value.find((a) => a.id === createdAsset.id) ||
            createdAsset;

        if (!list.some((a) => a.id === assetToSelect.id)) {
            updateListForTab(activeTab.value, [...list, assetToSelect]);
        }
    }

    emit('assets-changed');
}

onMounted(() => {
    if (!props.availableAssets) {
        fetchAssets();
    }
});
</script>

<template>
    <div :class="compact ? 'space-y-2' : 'space-y-4'">
        <!-- Main Header with Manage Button (non-compact only) -->
        <div v-if="!compact && !readonly" class="flex items-center gap-2">
            <Button
                variant="ghost"
                size="sm"
                @click="openModal"
            >
                <Settings2 class="mr-2 h-3.5 w-3.5" />
                Manage Assets
            </Button>
        </div>

        <!-- Grid Display -->
        <div :class="[
            'grid gap-4',
            showOnlySources ? 'grid-cols-1' : 'grid-cols-3'
        ]">
            <div v-for="section in sections" :key="section.key" :class="compact ? 'space-y-2' : 'space-y-3'">
                <div class="flex items-center gap-2">
                    <Label 
                        :class="[
                            'text-sm font-medium',
                            !compact && !showOnlySources ? ACCENT_LABEL_CLASS[accentFor(section.key)] : ''
                        ]"
                    >
                        {{ showOnlySources ? sourcesLabel : section.label }}
                    </Label>
                    <span v-if="section.items.length > 0" class="text-xs bg-muted px-2 py-0.5 rounded-full">{{ section.items.length }}</span>
                    <!-- Manage button in compact mode - same line as title -->
                    <Button
                        v-if="compact && !readonly"
                        variant="ghost"
                        size="sm"
                        @click="openModal"
                        class="text-xs h-6 px-2"
                    >
                        <Settings2 class="mr-1 h-3 w-3" />
                        Manage
                    </Button>
                </div>
                
                <!-- Assets Grid -->
                <div v-if="section.items.length > 0" :class="compact || showOnlySources ? 'flex flex-wrap gap-2' : 'grid grid-cols-2 gap-2'">
                    <Popover v-for="asset in section.items" :key="asset.id">
                        <PopoverTrigger as-child>
                            <div 
                                :class="[
                                    'group relative flex items-center transition-colors cursor-pointer',
                                    compact
                                        ? 'gap-2 px-2 py-1.5 rounded-md border bg-card hover:bg-accent/20'
                                        : 'flex-col justify-center p-3 rounded-lg border-2 bg-card hover:bg-accent/20 min-h-[120px]',
                                    !compact && showOnlySources ? 'w-[150px]' : '',
                                    !compact ? ACCENT_BORDER_CLASS[accentFor(section.key)] : '',
                                    asset.deleted ? 'opacity-60 border-dashed border-muted-foreground/30' : ''
                                ]"
                            >
                                <!-- Remove Button (Top Right for normal, inline for compact) -->
                                <Button
                                    v-if="!compact && !readonly"
                                    variant="ghost"
                                    size="icon"
                                    class="absolute top-1 right-1 h-5 w-5 rounded-full text-muted-foreground hover:text-destructive z-10"
                                    @click.stop="removeAsset(asset.id, section.key)"
                                >
                                    <X class="h-3 w-3" />
                                </Button>
                                
                                <!-- Icon -->
                                <component :is="getIconComponent(asset.icon)" :class="compact ? 'h-4 w-4 text-muted-foreground shrink-0' : 'h-6 w-6 text-muted-foreground mb-2'" />
                                
                                <!-- Name -->
                                <span :class="[
                                    compact ? 'text-xs font-medium truncate max-w-[100px]' : 'text-sm font-medium text-center line-clamp-2 leading-tight',
                                    asset.deleted ? 'line-through text-muted-foreground' : ''
                                ]">{{ asset.name }}</span>
                                
                                <!-- Info Icon (if has properties) - after name -->
                                <Info 
                                    v-if="asset.properties && Object.keys(asset.properties).length > 0"
                                    :class="compact ? 'h-3 w-3 text-muted-foreground opacity-60 shrink-0' : 'absolute bottom-1 right-1 h-3 w-3 text-muted-foreground opacity-60'"
                                />
                                
                                <!-- Remove Button for compact mode -->
                                <Button
                                    v-if="compact && !readonly"
                                    variant="ghost"
                                    size="icon"
                                    class="ml-auto h-5 w-5 rounded-full text-muted-foreground hover:text-destructive shrink-0"
                                    @click.stop="removeAsset(asset.id, section.key)"
                                >
                                    <X class="h-3 w-3" />
                                </Button>
                            </div>
                        </PopoverTrigger>
                        <PopoverContent v-if="asset.properties && Object.keys(asset.properties).length > 0" class="w-80" align="center">
                            <div class="space-y-2">
                                <h4 class="font-medium text-sm border-b pb-1">Properties</h4>
                                <div class="grid gap-1">
                                    <div 
                                        v-for="(val, key) in asset.properties" 
                                        :key="key" 
                                        class="grid grid-cols-[100px_1fr] gap-2 text-sm"
                                    >
                                        <span class="text-muted-foreground truncate">{{ key }}:</span>
                                        <span class="break-all">{{ val }}</span>
                                    </div>
                                </div>
                            </div>
                        </PopoverContent>
                    </Popover>
                </div>
                <div v-else 
                    :class="['text-xs text-muted-foreground italic text-center py-8 border rounded-lg bg-muted/30 transition-colors', !readonly ? 'cursor-pointer hover:bg-muted/50 hover:text-foreground' : '']"
                    @click="!readonly && openModal(section.key)"
                >
                    <div class="flex flex-col items-center gap-1.5 p-2">
                        <Plus v-if="!readonly" class="h-4 w-4 opacity-50" />
                        <span>No {{ section.key }} selected</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Modal -->
        <Dialog v-model:open="modalOpen">
            <DialogContent class="!max-w-4xl flex flex-col max-h-[85vh]">
                <DialogHeader>
                    <DialogTitle>Manage Assets</DialogTitle>
                </DialogHeader>
                
                <!-- Tab Switcher -->
                <Tabs v-if="!showOnlySources" :model-value="activeTab" @update:model-value="activeTab = $event as typeof activeTab" class="w-full">
                    <TabsList class="w-full">
                        <TabsTrigger v-for="tab in ['sources', 'targets', 'tools'] as const" :key="tab" :value="tab" class="flex-1 capitalize">
                            {{ tab }}
                        </TabsTrigger>
                    </TabsList>
                </Tabs>
                <div v-else class="text-sm font-medium text-muted-foreground">Select {{ sourcesLabel || 'sources' }}</div>

                <!-- Search -->
                <div class="relative mt-2 flex-shrink-0">
                    <Search class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                        v-model="searchQuery"
                        placeholder="Search assets..."
                        class="pl-9"
                    />
                </div>

                <!-- List -->
                <div class="flex-1 overflow-y-auto min-h-0 -mx-6 px-6 mt-4">
                    <div class="space-y-1 pb-2">
                        <div v-if="filteredAssets.length === 0" class="text-center py-8 text-muted-foreground text-sm">
                            No assets found.
                        </div>
                        <div
                            v-for="asset in filteredAssets"
                            :key="asset.id"
                            class="flex items-center justify-between p-2 rounded-md hover:bg-accent cursor-pointer border border-transparent"
                            :class="{ 'bg-accent/50 border-accent': isSelected(asset.id, activeTab) }"
                            @click="toggleSelection(asset)"
                        >
                            <div class="flex items-center gap-3 min-w-0">
                                <div 
                                    class="h-4 w-4 rounded border border-primary flex items-center justify-center shrink-0 transition-colors"
                                    :class="isSelected(asset.id, activeTab) ? 'bg-primary text-primary-foreground' : 'bg-transparent'"
                                >
                                    <Check v-if="isSelected(asset.id, activeTab)" class="h-3 w-3" />
                                </div>
                                <component :is="getIconComponent(asset.icon)" class="h-4 w-4 text-muted-foreground shrink-0" />
                                <div class="flex flex-col min-w-0 text-left">
                                    <span class="text-sm font-medium truncate">{{ asset.name }}</span>
                                    <span class="text-xs text-muted-foreground truncate" v-if="asset.properties && Object.keys(asset.properties).length > 0">
                                        {{ Object.keys(asset.properties).length }} properties
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <DialogFooter class="pt-2 border-t mt-auto">
                    <Button variant="outline" @click="openManageAssets">Manage Assets</Button>
                    <Button variant="outline" @click="openNewAsset">
                        <Plus class="mr-2 h-4 w-4" />
                        New Asset
                    </Button>
                    <Button @click="modalOpen = false">Done</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
        
        <!-- Manage Assets Modal -->
        <ManageAssetsModal 
            :open="manageAssetsModalOpen" 
            @update:open="manageAssetsModalOpen = $event"
            :assessment-id="assessmentId"
            :initial-view="manageAssetsInitialView"
            @success="handleAssetManagementSuccess"
        />
    </div>
</template>

