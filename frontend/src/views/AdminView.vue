<script setup lang="ts">
import {
    Database,
    Download,
    GitBranch,
    Settings,
    Shield,
    TestTube,
    Users,
} from '@lucide/vue';
import { ref } from 'vue';
import { toast } from 'vue-sonner';
import { Button } from '@/components/ui/button';
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from '@/components/ui/card';
import { useAdminStore } from '@/stores/admin';

const adminStore = useAdminStore();
const isSeedingMitre = ref(false);
const isSeedingArt = ref(false);
const isSeedingCustom = ref(false);

const handleSeedMitre = async () => {
    isSeedingMitre.value = true;
    try {
        const result = await adminStore.importMitre();
        toast.success(result.message || 'MITRE data seeded successfully');
    } catch (error) {
        // Error handled globally
    } finally {
        isSeedingMitre.value = false;
    }
};

const handleSeedArt = async () => {
    isSeedingArt.value = true;
    try {
        const result = await adminStore.importARTActivityTemplates();
        toast.success(
            result.message || 'Atomic Red Team templates seeded successfully',
        );
    } catch (error) {
        // Error handled globally
    } finally {
        isSeedingArt.value = false;
    }
};

const handleSeedCustom = async () => {
    isSeedingCustom.value = true;
    try {
        const result = await adminStore.importCustomerActivityTemplates();
        toast.success(result.message || 'Custom data seeded successfully');
    } catch (error) {
        // Error handled globally
    } finally {
        isSeedingCustom.value = false;
    }
};
</script>

<template>
  <div class="container mx-auto px-6 py-8">
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-3xl font-bold flex items-center gap-3">
          <Settings class="w-8 h-8" />
          Admin Dashboard
        </h1>
        <p class="text-muted-foreground mt-2">Manage system settings and data.</p>
      </div>
    </div>

    <div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      <!-- Access Control Panel -->
      <Card class="hover:shadow-md transition-shadow">
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <Users class="h-5 w-5" />
            Access Control
          </CardTitle>
          <CardDescription>
            Manage user accounts and permissions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p class="text-sm text-muted-foreground mb-4">
            Create new user accounts and manage access to the platform.
          </p>
          <RouterLink to="/admin/users">
            <Button class="w-full">
              Open User Management Panel
            </Button>
          </RouterLink>
        </CardContent>
      </Card>

      <!-- Logs (Placeholder) -->
      <Card class="hover:shadow-md transition-shadow opacity-60">
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <Shield class="h-5 w-5" />
            Logs
          </CardTitle>
          <CardDescription>
            Audit logs
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p class="text-sm text-muted-foreground mb-4">
            Review and monitor audit logs.
          </p>
          <Button variant="outline" class="w-full" disabled>
            Coming Soon
          </Button>
        </CardContent>
      </Card>

      <!-- Configuration -->
      <Card class="hover:shadow-md transition-shadow">
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <Settings class="h-5 w-5" />
            Configuration
          </CardTitle>
          <CardDescription>
            Configuration and settings
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p class="text-sm text-muted-foreground mb-4">
            View platform settings and configuration
          </p>
          <RouterLink to="/admin/configuration">
            <Button class="w-full">
              View Configuration
            </Button>
          </RouterLink>
        </CardContent>
      </Card>

      <!-- MITRE ATT&CK Data -->
      <Card class="hover:shadow-md transition-shadow">
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <Database class="h-5 w-5" />
            MITRE ATT&CK Data
          </CardTitle>
          <CardDescription>
            Seed tactics and techniques from MITRE
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p class="text-sm text-muted-foreground mb-4">
            Download and populate the database with the latest MITRE ATT&CK tactics and techniques.
          </p>
          <Button 
            class="w-full" 
            :disabled="isSeedingMitre"
            @click="handleSeedMitre"
          >
            <Download class="mr-2 h-4 w-4" />
            {{ isSeedingMitre ? "Seeding Data..." : "Seed MITRE Data" }}
          </Button>
        </CardContent>
      </Card>

      <!-- Custom Data -->
      <Card class="hover:shadow-md transition-shadow">
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <GitBranch class="h-5 w-5" />
            Custom Data Import
          </CardTitle>
          <CardDescription>
            Import data from your custom repository
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p class="text-sm text-muted-foreground mb-4">
            Import activity templates and Knowledge Base articles from your custom git repository.
          </p>
          <Button 
            class="w-full" 
            :disabled="isSeedingCustom"
            @click="handleSeedCustom"
          >
            <Download class="mr-2 h-4 w-4" />
            {{ isSeedingCustom ? "Seeding Data..." : "Seed Custom Data" }}
          </Button>
        </CardContent>
      </Card>

      <!-- Atomic Red Team Templates -->
      <Card class="hover:shadow-md transition-shadow">
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <TestTube class="h-5 w-5" />
            Atomic Red Team Templates
          </CardTitle>
          <CardDescription>
            Seed activity templates from Atomic Red Team
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p class="text-sm text-muted-foreground mb-4">
            Download and populate the database with activity templates from the Atomic Red Team project.
          </p>
          <Button 
            class="w-full" 
            :disabled="isSeedingArt"
            @click="handleSeedArt"
          >
            <Download class="mr-2 h-4 w-4" />
            {{ isSeedingArt ? "Seeding Templates..." : "Seed ART Templates" }}
          </Button>
        </CardContent>
      </Card>

    </div>
  </div>
</template>