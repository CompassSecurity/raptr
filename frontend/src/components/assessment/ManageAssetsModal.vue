<script setup lang="ts">
import {
    Check,
    ChevronsUpDown,
    Cloud,
    Computer,
    Database,
    Globe,
    Hammer,
    Info,
    Loader2,
    Network,
    Pencil,
    Plus,
    Search,
    SearchCode,
    Shield,
    ShieldCheck,
    Trash,
    Trash2,
    Undo2,
    User,
    Users,
} from 'lucide-vue-next';
import { computed, nextTick, ref, watch } from 'vue';
import { toast } from 'vue-sonner';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
    Command,
    CommandEmpty,
    CommandGroup,
    CommandInput,
    CommandItem,
    CommandList,
} from '@/components/ui/command';
import {
    Dialog,
    DialogContent,
    DialogDescription,
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
import { useConfirmDialog } from '@/composables/useConfirmDialog';
import { cn } from '@/lib/utils';
import { assetService } from '@/services/assetService';
import { useAuthStore } from '@/stores/auth';
import CreatableCombobox from '@/components/ui/CreatableCombobox.vue';
import type { AssetBase, AssetRead } from '@/types/utils';

const props = defineProps<{
    open: boolean;
    assessmentId: string;
    initialView?: 'list' | 'create';
}>();

const emit = defineEmits<{
    (e: 'update:open', value: boolean): void;
    (e: 'success', asset?: AssetRead): void;
}>();

const authStore = useAuthStore();

// Icon configuration
const AVAILABLE_ICONS = [
    'Cloud',
    'Computer',
    'Database',
    'Shield',
    'ShieldCheck',
    'Users',
    'Network',
    'SearchCode',
    'Hammer',
    'User',
    'Globe',
] as const;

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

function getIconComponent(iconName: string) {
    return iconMap[iconName] || Computer;
}

// Toggle properties popover
function togglePropertiesPopover(assetId: string) {
    propertiesPopoverOpen.value[assetId] =
        !propertiesPopoverOpen.value[assetId];
}

// View state management
type ViewMode = 'list' | 'create' | 'edit';
const currentView = ref<ViewMode>('list');
const editingAsset = ref<AssetRead | null>(null);
const nameInput = ref<InstanceType<typeof Input> | null>(null);

// Data state
const localAssets = ref<AssetRead[]>([]);
const loading = ref(false);

// Form state
const formData = ref<{
    name: string;
    icon: string;
    properties: Array<{ key: string; value: string }>;
}>({
    name: '',
    icon: 'Computer',
    properties: [],
});

// UI state
const searchQuery = ref('');
const iconPickerOpen = ref(false);
const formErrors = ref<{ name?: string }>({});
const propertiesPopoverOpen = ref<Record<string, boolean>>({});
const showDeleted = ref(false);

// Delete confirmation dialog
const deleteDialog = useConfirmDialog<AssetRead>();

// Permission checks
const canEdit = computed(() => {
    // Admin always has access
    if (authStore.user?.role === 'admin') return true;

    // Check for red, blue team access
    return (
        authStore.user?.acl?.some(
            (acl) =>
                acl.assessment_id === props.assessmentId &&
                (acl.assessment_role === 'red' ||
                    acl.assessment_role === 'blue'),
        ) ?? false
    );
});

// Dynamic dialog title
const dialogTitle = computed(() => {
    if (currentView.value === 'create') return 'New Asset';
    if (currentView.value === 'edit') return 'Edit Asset';
    return 'Manage Assets';
});

// Filtered assets for search and deleted status
const filteredAssets = computed(() => {
    let assets = localAssets.value;

    // Filter by search query
    if (searchQuery.value.trim()) {
        const query = searchQuery.value.toLowerCase();
        assets = assets.filter((asset) => {
            // Search in name
            if (asset.name.toLowerCase().includes(query)) return true;

            // Search in property keys/values
            if (asset.properties) {
                const propsString = JSON.stringify(
                    asset.properties,
                ).toLowerCase();
                if (propsString.includes(query)) return true;
            }

            return false;
        });
    }

    return assets;
});

// All unique property keys for autocomplete
const availablePropertyKeys = computed(() => {
    const keys = new Set<string>();
    for (const asset of localAssets.value) {
        if (asset.properties) {
            for (const key of Object.keys(asset.properties)) {
                keys.add(key);
            }
        }
    }
    return Array.from(keys).sort();
});

// All unique property values for autocomplete
const availablePropertyValues = computed(() => {
    const vals = new Set<string>();
    for (const asset of localAssets.value) {
        if (asset.properties) {
            for (const val of Object.values(asset.properties)) {
                if (val) vals.add(String(val));
            }
        }
    }
    return Array.from(vals).sort();
});

// Helper functions for properties
function hasProperties(asset: AssetRead): boolean {
    return !!(asset.properties && Object.keys(asset.properties).length > 0);
}

function getPropertiesCount(asset: AssetRead): number {
    return asset.properties ? Object.keys(asset.properties).length : 0;
}

function addProperty() {
    formData.value.properties.push({ key: '', value: '' });
}

function removeProperty(index: number) {
    formData.value.properties.splice(index, 1);
}

function propertiesToObject(
    props: Array<{ key: string; value: string }>,
): Record<string, string> | undefined {
    const filtered = props.filter(
        (p) => p.key.trim() !== '' && p.value.trim() !== '',
    );
    if (filtered.length === 0) return undefined;

    const obj: Record<string, string> = {};
    filtered.forEach((p) => {
        obj[p.key.trim()] = p.value.trim();
    });
    return obj;
}

function objectToProperties(
    obj: Record<string, any> | null | undefined,
): Array<{ key: string; value: string }> {
    if (!obj) return [];
    return Object.entries(obj).map(([key, value]) => ({
        key,
        value: String(value),
    }));
}

// View navigation
function showCreateView() {
    currentView.value = 'create';
    resetForm();
    nextTick(() => {
        nameInput.value?.$el?.focus();
    });
}

function showEditView(asset: AssetRead) {
    currentView.value = 'edit';
    editingAsset.value = asset;
    loadFormData(asset);
}

function showListView() {
    currentView.value = 'list';
    editingAsset.value = null;
    resetForm();
}

function handleCancel() {
    if (props.initialView === 'create') {
        emit('update:open', false);
    } else {
        showListView();
    }
}

function resetForm() {
    formData.value = {
        name: '',
        icon: 'Computer',
        properties: [],
    };
    formErrors.value = {};
}

function loadFormData(asset: AssetRead) {
    formData.value = {
        name: asset.name,
        icon: asset.icon || 'Computer',
        properties: objectToProperties(asset.properties),
    };
    formErrors.value = {};
}

// Form validation
function validateForm(): boolean {
    formErrors.value = {};

    if (!formData.value.name.trim()) {
        formErrors.value.name = 'Name is required';
        return false;
    }

    if (formData.value.name.length > 100) {
        formErrors.value.name = 'Name must be 100 characters or less';
        return false;
    }

    // Check for duplicate property keys
    const keys = formData.value.properties
        .map((p) => p.key.trim())
        .filter((k) => k !== '');
    const uniqueKeys = new Set(keys);
    if (keys.length !== uniqueKeys.size) {
        toast.error('Duplicate property keys are not allowed');
        return false;
    }

    return true;
}

// Icon selection
function selectIcon(iconName: string) {
    formData.value.icon = iconName;
    iconPickerOpen.value = false;
}

// Fetch assets from API
async function fetchAssets() {
    loading.value = true;
    try {
        const data = await assetService.getAssets(props.assessmentId, {
            limit: 1000,
        });
        // Filter deleted assets based on showDeleted toggle
        if (showDeleted.value) {
            localAssets.value = data.items;
        } else {
            localAssets.value = data.items.filter((asset) => !asset.deleted);
        }
        // Reset popover state when assets are refreshed
        propertiesPopoverOpen.value = {};
    } catch (error) {
        // Error handled globally
    } finally {
        loading.value = false;
    }
}

// Watch showDeleted toggle and refetch
watch(showDeleted, () => {
    fetchAssets();
});

// CRUD operations
async function handleCreate() {
    if (!validateForm()) return;

    loading.value = true;
    try {
        const payload: AssetBase = {
            name: formData.value.name.trim(),
            icon: formData.value.icon,
            properties: propertiesToObject(formData.value.properties),
        };

        const createdAsset = await assetService.createAsset(
            props.assessmentId,
            payload,
        );
        toast.success(`Asset "${payload.name}" created`);

        await fetchAssets();
        if (props.initialView === 'create') {
            emit('update:open', false);
        } else {
            showListView();
        }
        emit('success', createdAsset);
    } catch (error) {
        // Error handled globally
    } finally {
        loading.value = false;
    }
}

async function handleUpdate() {
    if (!validateForm() || !editingAsset.value) return;

    loading.value = true;
    try {
        const payload: AssetBase = {
            name: formData.value.name.trim(),
            icon: formData.value.icon,
            properties: propertiesToObject(formData.value.properties),
        };

        await assetService.updateAsset(
            props.assessmentId,
            editingAsset.value.id,
            payload,
        );
        toast.success(`Asset "${payload.name}" updated`);

        await fetchAssets();
        if (props.initialView === 'create') {
            emit('update:open', false);
        } else {
            showListView();
        }
        emit('success');
    } catch (error) {
        // Error handled globally
    } finally {
        loading.value = false;
    }
}

function handleDelete(asset: AssetRead) {
    deleteDialog.open(asset);
}

async function confirmDelete(asset: AssetRead) {
    loading.value = true;
    try {
        await assetService.toggleDeleteAsset(props.assessmentId, asset.id);
        const message = asset.deleted
            ? `Asset "${asset.name}" restored`
            : `Asset "${asset.name}" deleted`;
        toast.success(message);
        await fetchAssets();
    } catch (error) {
        // Error handled globally
    } finally {
        loading.value = false;
    }
}

function handleSave() {
    if (currentView.value === 'create') {
        handleCreate();
    } else if (currentView.value === 'edit') {
        handleUpdate();
    }
}

// Watch for modal open/close
watch(
    () => props.open,
    async (isOpen) => {
        if (isOpen) {
            if (props.initialView === 'create' && canEdit.value) {
                showCreateView();
            } else {
                showListView();
            }
            await fetchAssets();
        } else {
            // Reset to list view after closing animation finishes
            setTimeout(() => {
                if (!props.open) showListView();
            }, 300);
        }
    },
);
</script>

<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <DialogContent class="sm:max-w-[700px] max-h-[85vh] flex flex-col">
      <DialogHeader>
        <DialogTitle>{{ dialogTitle }}</DialogTitle>
        <DialogDescription v-if="currentView === 'list'">
          View and manage assets for this assessment.
        </DialogDescription>
      </DialogHeader>

      <div class="py-4 flex-1 overflow-hidden flex flex-col gap-4">
        <!-- LIST VIEW -->
        <template v-if="currentView === 'list'">
          <!-- Search and Show Deleted Toggle -->
          <div class="flex gap-3 items-center">
            <div class="relative flex-1">
              <Search class="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                v-model="searchQuery"
                placeholder="Search assets..."
                class="pl-10"
                :disabled="loading"
              />
            </div>

            <!-- Show Deleted Toggle (Admin/Red Team only) -->
            <Button
              v-if="canEdit"
              :variant="showDeleted ? 'default' : 'outline'"
              size="sm"
              @click="showDeleted = !showDeleted"
              :disabled="loading"
              class="h-9"
            >
              <Trash class="h-4 w-4" />
            </Button>
          </div>

          <!-- Asset List -->
          <div class="flex-1 border rounded-md overflow-y-auto min-h-0">
            <!-- Loading State -->
            <div v-if="loading" class="flex items-center justify-center h-64">
              <Loader2 class="h-8 w-8 animate-spin text-muted-foreground" />
            </div>

            <!-- Empty State -->
            <div v-else-if="filteredAssets.length === 0" class="flex flex-col items-center justify-center h-64 text-center p-6">
              <Computer class="h-12 w-12 text-muted-foreground mb-4" />
              <p class="text-lg font-medium">No assets found</p>
              <p class="text-sm text-muted-foreground mt-1">
                {{ searchQuery ? 'Try adjusting your search' : 'Get started by creating an asset' }}
              </p>
            </div>

            <!-- Asset Cards -->
            <div v-else class="divide-y">
              <div
                v-for="asset in filteredAssets"
                :key="asset.id"
                :class="[
                  'flex items-center justify-between p-3 hover:bg-muted/50 transition-colors',
                  { 'opacity-50': asset.deleted }
                ]"
              >
                <!-- Left: Icon + Name + Badge -->
                <div class="flex items-center gap-3 flex-1 min-w-0">
                  <component
                    :is="getIconComponent(asset.icon || 'Computer')"
                    class="h-5 w-5 text-muted-foreground flex-shrink-0"
                  />
                  <div
                    :class="[
                      'font-medium truncate',
                      { 'line-through text-muted-foreground': asset.deleted }
                    ]"
                  >
                    {{ asset.name }}
                  </div>
                  <Badge v-if="asset.deleted" variant="destructive" class="text-xs flex-shrink-0">
                    Deleted
                  </Badge>

                  <!-- Properties Badge with Popover -->
                  <Popover v-if="hasProperties(asset)" v-model:open="propertiesPopoverOpen[asset.id]">
                    <PopoverTrigger as-child>
                      <Badge
                        variant="secondary"
                        class="text-xs flex-shrink-0 cursor-pointer hover:bg-secondary/80"
                        @click="togglePropertiesPopover(asset.id)"
                      >
                        <Info class="h-3 w-3 mr-1" />
                        {{ getPropertiesCount(asset) }}
                      </Badge>
                    </PopoverTrigger>
                    <PopoverContent class="w-80" align="start">
                      <div class="space-y-2">
                        <h4 class="font-medium text-sm">Properties</h4>
                        <div class="space-y-1.5">
                          <div
                            v-for="[key, value] in Object.entries(asset.properties || {})"
                            :key="key"
                            class="grid grid-cols-2 gap-2 text-sm"
                          >
                            <div class="font-medium text-muted-foreground truncate">{{ key }}:</div>
                            <div class="truncate" :title="String(value)">{{ value }}</div>
                          </div>
                        </div>
                      </div>
                    </PopoverContent>
                  </Popover>
                </div>

                <!-- Right: Actions (only for admin/red/blue) -->
                <div v-if="canEdit" class="flex items-center gap-1 flex-shrink-0">
                  <!-- Show restore button for deleted assets -->
                  <Button v-if="asset.deleted" variant="ghost" size="sm" @click="handleDelete(asset)" :disabled="loading" title="Restore asset">
                    <Undo2 class="h-4 w-4" />
                  </Button>
                  <!-- Show edit and delete buttons for active assets -->
                  <template v-else>
                    <Button variant="ghost" size="sm" @click="showEditView(asset)" :disabled="loading">
                      <Pencil class="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="sm" @click="handleDelete(asset)" :disabled="loading">
                      <Trash2 class="h-4 w-4 text-destructive" />
                    </Button>
                  </template>
                </div>
              </div>
            </div>
          </div>

          <!-- View-only message for spectators -->
          <div v-if="!canEdit" class="text-sm text-muted-foreground text-center">
            You have view-only access to assets
          </div>
        </template>

        <!-- CREATE/EDIT VIEW -->
        <template v-else>
          <form @submit.prevent="handleSave" class="space-y-4">
            <!-- Name Input -->
            <div class="space-y-2">
              <Label for="asset-name">Name <span class="text-destructive">*</span></Label>
              <Input
                id="asset-name"
                ref="nameInput"
                v-model="formData.name"
                placeholder="Enter asset name"
                maxlength="100"
                :disabled="loading"
                :class="{ 'border-destructive': formErrors.name }"
              />
              <p v-if="formErrors.name" class="text-sm text-destructive">{{ formErrors.name }}</p>
            </div>

            <!-- Icon Picker -->
            <div class="space-y-2">
              <Label>Icon</Label>
              <Popover v-model:open="iconPickerOpen">
                <PopoverTrigger as-child>
                  <Button
                    type="button"
                    variant="outline"
                    role="combobox"
                    :aria-expanded="iconPickerOpen"
                    class="w-full justify-between"
                    :disabled="loading"
                  >
                    <div class="flex items-center gap-2">
                      <component :is="getIconComponent(formData.icon)" class="h-4 w-4" />
                      <span>{{ formData.icon }}</span>
                    </div>
                    <ChevronsUpDown class="ml-2 h-4 w-4 shrink-0 opacity-50" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent class="w-[300px] p-0">
                  <Command>
                    <CommandInput placeholder="Search icon..." />
                    <CommandEmpty>No icon found.</CommandEmpty>
                    <CommandList>
                      <CommandGroup>
                        <CommandItem
                          v-for="iconName in AVAILABLE_ICONS"
                          :key="iconName"
                          :value="iconName"
                          @select="selectIcon(iconName)"
                        >
                          <Check
                            :class="cn('mr-2 h-4 w-4', iconName === formData.icon ? 'opacity-100' : 'opacity-0')"
                          />
                          <component :is="getIconComponent(iconName)" class="h-4 w-4 mr-2" />
                          {{ iconName }}
                        </CommandItem>
                      </CommandGroup>
                    </CommandList>
                  </Command>
                </PopoverContent>
              </Popover>
            </div>

            <!-- Properties Editor -->
            <div class="space-y-3">
              <div class="flex items-center justify-between">
                <Label>Properties</Label>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  @click="addProperty"
                  :disabled="loading"
                >
                  <Plus class="h-4 w-4 mr-1" />
                  Add Property
                </Button>
              </div>

              <div v-if="formData.properties.length > 0" class="max-h-[200px] overflow-y-auto min-h-0 space-y-2">
                <div
                  v-for="(prop, index) in formData.properties"
                  :key="index"
                  class="flex gap-2"
                >
                  <CreatableCombobox
                    v-model="prop.key"
                    :options="availablePropertyKeys"
                    placeholder="Key"
                    searchPlaceholder="Search or create key..."
                    class="flex-1"
                    :disabled="loading"
                  />
                  <CreatableCombobox
                    v-model="prop.value"
                    :options="availablePropertyValues"
                    placeholder="Value"
                    searchPlaceholder="Search or create value..."
                    class="flex-1"
                    :disabled="loading"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    @click="removeProperty(index)"
                    :disabled="loading"
                  >
                    <Trash2 class="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              </div>

              <p v-else class="text-sm text-muted-foreground">
                No properties added yet.
              </p>
            </div>
          </form>
        </template>
      </div>

      <DialogFooter>
        <!-- LIST VIEW Footer -->
        <template v-if="currentView === 'list'">
          <Button variant="outline" @click="emit('update:open', false)">Close</Button>
          <Button v-if="canEdit" @click="showCreateView" :disabled="loading">
            <Plus class="mr-2 h-4 w-4" />
            New Asset
          </Button>
        </template>

        <!-- CREATE/EDIT VIEW Footer -->
        <template v-else>
          <Button variant="outline" @click="handleCancel" :disabled="loading">Cancel</Button>
          <Button @click="handleSave" :disabled="loading">
            {{ loading ? 'Saving...' : 'Save' }}
          </Button>
        </template>
      </DialogFooter>
    </DialogContent>
  </Dialog>

  <!-- Delete/Restore Confirmation Dialog -->
  <Dialog :open="deleteDialog.isOpen.value" @update:open="deleteDialog.close">
    <DialogContent class="sm:max-w-[425px]">
      <DialogHeader>
        <DialogTitle>{{ deleteDialog.pendingItem.value?.deleted ? 'Restore Asset' : 'Delete Asset' }}</DialogTitle>
        <DialogDescription>
          {{ deleteDialog.pendingItem.value?.deleted
            ? `Are you sure you want to restore "${deleteDialog.pendingItem.value?.name}"?`
            : `Are you sure you want to delete "${deleteDialog.pendingItem.value?.name}"? This action cannot be undone.`
          }}
        </DialogDescription>
      </DialogHeader>
      <DialogFooter>
        <Button variant="outline" @click="deleteDialog.close" :disabled="deleteDialog.isProcessing.value">
          Cancel
        </Button>
        <Button
          :variant="deleteDialog.pendingItem.value?.deleted ? 'default' : 'destructive'"
          @click="deleteDialog.confirm(confirmDelete)"
          :disabled="deleteDialog.isProcessing.value"
        >
          {{ deleteDialog.isProcessing.value
            ? (deleteDialog.pendingItem.value?.deleted ? 'Restoring...' : 'Deleting...')
            : (deleteDialog.pendingItem.value?.deleted ? 'Restore' : 'Delete')
          }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
