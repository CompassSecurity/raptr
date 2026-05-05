<script setup lang="ts">
import { Check, ChevronsUpDown } from '@lucide/vue';
import { computed, nextTick, ref, watch } from 'vue';
import { toast } from 'vue-sonner';
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
import { cn } from '@/lib/utils';
import { activityService } from '@/services/activityService';
import { mitreService } from '@/services/mitreService';
import type { TacticWithTechniques, TechniqueBase } from '@/types/utils';

const props = defineProps<{
    open: boolean;
    assessmentId: string;
}>();

const emit = defineEmits<{
    (e: 'update:open', value: boolean): void;
    (e: 'created'): void;
}>();

// Form state
const name = ref('');
const nameInput = ref<InstanceType<typeof Input> | null>(null);
const selectedTactic = ref<TacticWithTechniques | null>(null);
const selectedTechnique = ref<TechniqueBase | null>(null);

// Loading and data state
const loading = ref(false);
const submitting = ref(false);
const tactics = ref<TacticWithTechniques[]>([]);

// Tactic dropdown state
const tacticDropdownOpen = ref(false);

// Technique dropdown state
const techniqueDropdownOpen = ref(false);

// Fetch tactics when modal opens
watch(
    () => props.open,
    async (isOpen) => {
        if (isOpen && tactics.value.length === 0) {
            await fetchTactics();
        }
        if (isOpen) {
            await nextTick();
            nameInput.value?.$el?.focus();
        }
        // Reset form when modal closes
        if (!isOpen) {
            resetForm();
        }
    },
);

const fetchTactics = async () => {
    loading.value = true;
    try {
        tactics.value = await mitreService.getTacticsWithTechniques({
            sort_by: 'mitre_id',
            sort_order: 'asc',
        });
    } catch (error) {
        toast.error('Failed to load tactics');
    } finally {
        loading.value = false;
    }
};

// Get techniques for the selected tactic
const availableTechniques = computed<TechniqueBase[]>(() => {
    if (!selectedTactic.value) return [];
    return selectedTactic.value.techniques;
});

// When tactic changes, reset technique selection
watch(selectedTactic, () => {
    selectedTechnique.value = null;
});

const selectTactic = (tactic: TacticWithTechniques) => {
    selectedTactic.value = tactic;
    tacticDropdownOpen.value = false;
};

const selectTechnique = (technique: TechniqueBase) => {
    selectedTechnique.value = technique;
    techniqueDropdownOpen.value = false;
};

const resetForm = () => {
    name.value = '';
    selectedTactic.value = null;
    selectedTechnique.value = null;
};

const handleSubmit = async () => {
    if (!name.value || !selectedTactic.value || !selectedTechnique.value) {
        toast.error('Please fill in all fields');
        return;
    }

    submitting.value = true;
    try {
        await activityService.createActivity(props.assessmentId, {
            name: name.value,
            mitre_tactic: selectedTactic.value.mitre_id,
            mitre_technique: selectedTechnique.value.mitre_id,
        });
        toast.success('Activity created successfully');
        emit('created');
        emit('update:open', false);
    } catch (error) {
        // Error handled globally
    } finally {
        submitting.value = false;
    }
};

const isFormValid = computed(() => {
    return name.value && selectedTactic.value && selectedTechnique.value;
});
</script>

<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <DialogContent class="sm:max-w-[500px]">
      <DialogHeader>
        <DialogTitle>Create Activity</DialogTitle>
      </DialogHeader>

      <div class="grid gap-4 py-4">
        <!-- Activity Name -->
        <div class="grid gap-2">
          <Label for="name">Activity Name</Label>
          <Input
            id="name"
            ref="nameInput"
            v-model="name"
            placeholder="Enter activity name"
            :disabled="submitting"
          />
        </div>

        <!-- Tactic Dropdown -->
        <div class="grid gap-2">
          <Label>MITRE Tactic</Label>
          <Popover v-model:open="tacticDropdownOpen">
            <PopoverTrigger as-child>
              <Button
                variant="outline"
                role="combobox"
                :aria-expanded="tacticDropdownOpen"
                class="w-full justify-between"
                :disabled="loading || submitting"
              >
                {{ selectedTactic
                  ? `${selectedTactic.mitre_id} - ${selectedTactic.name}`
                  : "Select tactic..." }}
                <ChevronsUpDown class="ml-2 h-4 w-4 shrink-0 opacity-50" />
              </Button>
            </PopoverTrigger>
            <PopoverContent class="w-[465px] p-0">
              <Command>
                <CommandInput class="h-9" placeholder="Search tactic..." />
                <CommandEmpty>No tactic found.</CommandEmpty>
                <CommandList>
                  <CommandGroup>
                    <CommandItem
                      v-for="tactic in tactics"
                      :key="tactic.id"
                      :value="tactic.name"
                      @select="() => selectTactic(tactic)"
                    >
                      <Check
                        :class="cn(
                          'mr-2 h-4 w-4',
                          selectedTactic?.id === tactic.id ? 'opacity-100' : 'opacity-0'
                        )"
                      />
                      {{ tactic.mitre_id }} - {{ tactic.name }}
                    </CommandItem>
                  </CommandGroup>
                </CommandList>
              </Command>
            </PopoverContent>
          </Popover>
        </div>

        <!-- Technique Dropdown -->
        <div class="grid gap-2">
          <Label>MITRE Technique</Label>
          <Popover v-model:open="techniqueDropdownOpen">
            <PopoverTrigger as-child>
              <Button
                variant="outline"
                role="combobox"
                :aria-expanded="techniqueDropdownOpen"
                class="w-full justify-between"
                :disabled="!selectedTactic || submitting"
              >
                {{ selectedTechnique
                  ? `${selectedTechnique.mitre_id} - ${selectedTechnique.name}`
                  : "Select technique..." }}
                <ChevronsUpDown class="ml-2 h-4 w-4 shrink-0 opacity-50" />
              </Button>
            </PopoverTrigger>
            <PopoverContent class="w-[465px] p-0">
              <Command>
                <CommandInput class="h-9" placeholder="Search technique..." />
                <CommandEmpty>No technique found.</CommandEmpty>
                <CommandList>
                  <CommandGroup>
                    <CommandItem
                      v-for="technique in availableTechniques"
                      :key="technique.id"
                      :value="technique.name"
                      @select="() => selectTechnique(technique)"
                    >
                      <Check
                        :class="cn(
                          'mr-2 h-4 w-4',
                          selectedTechnique?.id === technique.id ? 'opacity-100' : 'opacity-0'
                        )"
                      />
                      {{ technique.mitre_id }} - {{ technique.name }}
                    </CommandItem>
                  </CommandGroup>
                </CommandList>
              </Command>
            </PopoverContent>
          </Popover>
        </div>
      </div>

      <DialogFooter>
        <Button
          variant="outline"
          @click="emit('update:open', false)"
          :disabled="submitting"
        >
          Cancel
        </Button>
        <Button
          @click="handleSubmit"
          :disabled="!isFormValid || submitting"
        >
          {{ submitting ? 'Creating...' : 'Create Activity' }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
