<script setup lang="ts">
import { Loader2, Search } from '@lucide/vue';
import { computed, ref, watch } from 'vue';
import { toast } from 'vue-sonner';
import { Button } from '@/components/ui/button';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import { useAdminStore } from '@/stores/admin';
import { useAssessmentListStore } from '@/stores/assessmentList';
import type { components } from '@/types/schema';

type AssessmentRead = components['schemas']['AssessmentRead'];
type AclRead = components['schemas']['AclRead'];

const props = defineProps<{
    open: boolean;
    assessment: AssessmentRead;
}>();

const emit = defineEmits<{
    (e: 'update:open', value: boolean): void;
    (e: 'success'): void;
}>();

const adminStore = useAdminStore();
const assessmentStore = useAssessmentListStore();

const localAcls = ref<AclRead[]>([]);
const loading = ref(false);
const searchQuery = ref('');

// Fetch data when modal opens
watch(
    () => props.open,
    async (isOpen) => {
        if (isOpen && props.assessment) {
            loading.value = true;
            try {
                // Fetch all users (limit to 1000 for now to get a good list)
                // Note: In a real large-scale app, we'd want server-side searching/pagination for this picker,
                // but for now we fetch list and filter client-side as requested.
                await adminStore.fetchUsers({ limit: 1000 });

                // Fetch current ACLs for this assessment
                localAcls.value = await assessmentStore.fetchAssessmentAcls(
                    props.assessment.id,
                );
            } catch (error) {
                toast.error('Failed to load data');
            } finally {
                loading.value = false;
            }
        }
    },
    { immediate: true },
);

const usersWithRoles = computed(() => {
    if (!adminStore.users) return [];

    const term = searchQuery.value.toLowerCase();

    return adminStore.users
        .filter((user) => user.role !== 'admin') // Exclude admins
        .filter((user) => user.email.toLowerCase().includes(term)) // Client-side search
        .map((user) => {
            const acl = localAcls.value.find((a) => a.user_id === user.id);
            return {
                user,
                acl,
                currentRole: acl ? acl.assessment_role : 'none',
            };
        });
});

const handleRoleChange = async (
    userId: string,
    newRole: string,
    currentAcl: AclRead | undefined,
) => {
    const user = adminStore.users.find((u) => u.id === userId);
    if (!user) return;

    loading.value = true;
    try {
        if (newRole === 'none') {
            // Delete if exists
            if (currentAcl) {
                await assessmentStore.deleteAcl(currentAcl.id);
                toast.success(`Removed access for ${user.email}`);
            }
        } else {
            if (currentAcl) {
                // Update
                if (currentAcl.assessment_role !== newRole) {
                    await assessmentStore.updateAcl(currentAcl.id, {
                        user_id: userId,
                        assessment_id: props.assessment.id,
                        assessment_role: newRole as
                            | 'red'
                            | 'blue'
                            | 'spectator',
                    });
                    toast.success(
                        `Updated role for ${user.email} to ${newRole}`,
                    );
                }
            } else {
                // Create
                await assessmentStore.createAcl({
                    user_id: userId,
                    assessment_id: props.assessment.id,
                    assessment_role: newRole as 'red' | 'blue' | 'spectator',
                });
                toast.success(`assigned ${newRole} to ${user.email}`);
            }
        }

        // Refresh ACLs to update UI state properly
        localAcls.value = await assessmentStore.fetchAssessmentAcls(
            props.assessment.id,
        );
    } catch (error) {
        // Error handled by interceptor/store typically, but we catch to stop loading
        console.error(error);
    } finally {
        loading.value = false;
    }
};

const handleClose = () => {
    emit('update:open', false);
};
</script>

<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent class="sm:max-w-[600px] max-h-[80vh] flex flex-col">
      <DialogHeader>
        <DialogTitle>Manage Access Control</DialogTitle>
        <DialogDescription>
          Manage user access and roles for <strong>{{ assessment.name }}</strong>.
        </DialogDescription>
      </DialogHeader>

      <div class="py-4 flex-1 overflow-hidden flex flex-col gap-4">
        <!-- Search -->
        <div class="relative">
          <Search class="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Search users..." v-model="searchQuery" class="pl-8" />
        </div>

        <!-- User List -->
        <div class="flex-1 overflow-y-auto min-h-0 border rounded-md">
            <div v-if="loading && !usersWithRoles.length" class="p-8 flex justify-center">
                <Loader2 class="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
            
            <Table v-else>
                <TableHeader class="bg-muted/50 sticky top-0">
                    <TableRow class="text-left">
                        <TableHead>User</TableHead>
                        <TableHead class="w-[150px]">Role</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    <TableRow v-for="item in usersWithRoles" :key="item.user.id">
                        <TableCell>
                            <div class="font-medium">{{ item.user.email }}</div>
                             <div class="text-xs text-muted-foreground" v-if="item.acl">
                                Has access
                            </div>
                        </TableCell>
                        <TableCell>
                            <Select
                                :model-value="item.currentRole || undefined"
                                @update:model-value="(val) => handleRoleChange(item.user.id, val as string, item.acl)"
                                :disabled="loading"
                            >
                                <SelectTrigger class="h-8">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="none">None</SelectItem>
                                    <SelectItem value="spectator">Spectator</SelectItem>
                                    <SelectItem value="blue">Blue Team</SelectItem>
                                    <SelectItem value="red">Red Team</SelectItem>
                                </SelectContent>
                            </Select>
                        </TableCell>
                    </TableRow>
                    <TableRow v-if="usersWithRoles.length === 0 && !loading">
                        <TableCell colspan="2" class="p-8 text-center text-muted-foreground">
                            No users found.
                        </TableCell>
                    </TableRow>
                </TableBody>
            </Table>
        </div>
      </div>

      <DialogFooter>
        <Button variant="outline" @click="handleClose">Close</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
