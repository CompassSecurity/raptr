<template>
  <div class="container mx-auto px-6 py-8">
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-3xl font-bold flex items-center gap-3">
          <Settings class="w-8 h-8" />
          System Configuration
        </h1>
        <p class="text-muted-foreground mt-2">View system-wide configuration settings.</p>
      </div>
    </div>

    <div v-if="error" class="text-destructive mb-4">
        Error loading configuration: {{ error }}
    </div>
    <div v-else-if="!configuration" class="text-muted-foreground">
        Loading configuration...
    </div>
    
    <div v-else class="grid gap-6 md:grid-cols-2">
      <!-- General Settings -->
      <Card>
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <AppWindow class="h-5 w-5" />
            General
          </CardTitle>
          <CardDescription>Basic application settings.</CardDescription>
        </CardHeader>
        <CardContent class="grid gap-4">
          <div class="grid grid-cols-2 items-center gap-4">
            <span class="text-sm font-medium">Application Name</span>
            <span class="text-sm font-mono text-muted-foreground">{{ configuration.APPLICATION_NAME }}</span>
          </div>
          <div class="grid grid-cols-2 items-center gap-4">
            <span class="text-sm font-medium">Log Level</span>
            <span class="text-sm font-mono text-muted-foreground">{{ configuration.LOG_LEVEL }}</span>
          </div>
          <div class="grid grid-cols-2 items-center gap-4">
            <span class="text-sm font-medium">FastAPI Documentation</span>
            <span class="text-sm font-mono text-muted-foreground">{{ configuration.FASTAPI_DOCUMENTATION }}</span>
          </div>
          <div class="grid grid-cols-2 items-center gap-4">
            <span class="text-sm font-medium">Admin User</span>
            <span class="text-sm font-mono text-muted-foreground">{{ configuration.ADMIN_EMAIL }}</span>
          </div>
          <div class="grid grid-cols-2 items-center gap-4">
            <span class="text-sm font-medium">Welcome Message</span>
            <span class="text-sm font-mono text-muted-foreground whitespace-pre-wrap">{{ configuration.WELCOME_MESSAGE || 'None' }}</span>
          </div>
        </CardContent>
      </Card>

      <!-- CORS Settings -->
      <Card>
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <Globe class="h-5 w-5" />
            CORS
          </CardTitle>
          <CardDescription>Cross-Origin Resource Sharing settings.</CardDescription>
        </CardHeader>
        <CardContent class="grid gap-4">
          <div class="grid grid-cols-2 items-center gap-4">
            <span class="text-sm font-medium">Enabled</span>
            <span class="text-sm font-mono text-muted-foreground">{{ configuration.CORS_ENABLED }}</span>
          </div>
          <div class="grid grid-cols-2 items-center gap-4">
            <span class="text-sm font-medium">Origins</span>
            <span class="text-sm font-mono text-muted-foreground">{{ configuration.CORS_ORIGINS.join(', ') || 'None' }}</span>
          </div>
          <div class="grid grid-cols-2 items-center gap-4">
            <span class="text-sm font-medium">Methods</span>
            <span class="text-sm font-mono text-muted-foreground">{{ configuration.CORS_METHODS.join(', ') }}</span>
          </div>
          <div class="grid grid-cols-2 items-center gap-4">
            <span class="text-sm font-medium">Headers</span>
            <span class="text-sm font-mono text-muted-foreground">{{ configuration.CORS_HEADERS.join(', ') }}</span>
          </div>
          <div class="grid grid-cols-2 items-center gap-4">
            <span class="text-sm font-medium">Credentials</span>
            <span class="text-sm font-mono text-muted-foreground">{{ configuration.CORS_CREDENTIALS }}</span>
          </div>
          <div class="grid grid-cols-2 items-center gap-4">
            <span class="text-sm font-medium">Max Age</span>
            <span class="text-sm font-mono text-muted-foreground">{{ configuration.CORS_MAX_AGE }}</span>
          </div>
        </CardContent>
      </Card>

      <!-- Security Settings -->
      <Card>
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <Shield class="h-5 w-5" />
            Security
          </CardTitle>
          <CardDescription>Authentication and security protocols.</CardDescription>
        </CardHeader>
        <CardContent class="grid gap-4">
          <div class="grid grid-cols-2 items-center gap-4">
            <span class="text-sm font-medium">Min Password Length</span>
            <span class="text-sm font-mono text-muted-foreground">{{ configuration.MIN_PASSWORD_LENGTH }} chars</span>
          </div>
          <div class="grid grid-cols-2 items-center gap-4">
            <span class="text-sm font-medium">OTP Local Users</span>
            <span class="text-sm font-mono text-muted-foreground">{{ configuration.OTP_LOCAL_ENABLED }}</span>
          </div>
          <div class="grid grid-cols-2 items-center gap-4">
            <span class="text-sm font-medium">OTP External Users</span>
            <span class="text-sm font-mono text-muted-foreground">{{ configuration.OTP_EXTERNAL_ENABLED }}</span>
          </div>
          <div class="grid grid-cols-2 items-center gap-4">
            <span class="text-sm font-medium">JWT Algorithm</span>
            <span class="text-sm font-mono text-muted-foreground">{{ configuration.ALGORITHM }}</span>
          </div>
           <div class="grid grid-cols-2 items-center gap-4">
            <span class="text-sm font-medium">JWT Token Expiry</span>
            <span class="text-sm font-mono text-muted-foreground">{{ configuration.ACCESS_TOKEN_EXPIRE_MINUTES }} mins</span>
          </div>
        </CardContent>
      </Card>

      <!-- Database Settings -->
      <Card>
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <Database class="h-5 w-5" />
            Database
          </CardTitle>
          <CardDescription>Connection details for the configured database engine.</CardDescription>
        </CardHeader>
        <CardContent class="grid gap-4">
          <div class="grid grid-cols-2 items-center gap-4 border-b pb-4">
            <span class="text-sm font-medium">Engine</span>
            <span class="text-sm font-mono font-bold">{{ configuration.DB_ENGINE }}</span>
          </div>
          
          <template v-if="configuration.DB_ENGINE === 'postgres'">
            <div class="grid grid-cols-2 items-center gap-4 mt-2">
              <span class="text-sm font-medium">Host</span>
              <span class="text-sm font-mono text-muted-foreground">{{ configuration.POSTGRES_HOST }}</span>
            </div>
            <div class="grid grid-cols-2 items-center gap-4">
              <span class="text-sm font-medium">Port</span>
              <span class="text-sm font-mono text-muted-foreground">{{ configuration.POSTGRES_PORT }}</span>
            </div>
            <div class="grid grid-cols-2 items-center gap-4">
              <span class="text-sm font-medium">Database Name</span>
              <span class="text-sm font-mono text-muted-foreground">{{ configuration.POSTGRES_DB }}</span>
            </div>
            <div class="grid grid-cols-2 items-center gap-4">
              <span class="text-sm font-medium">User</span>
              <span class="text-sm font-mono text-muted-foreground">{{ configuration.POSTGRES_USER }}</span>
            </div>
          </template>

          <template v-if="configuration.DB_ENGINE === 'sqlite'">
            <div class="grid grid-cols-2 items-center gap-4 mt-2">
              <span class="text-sm font-medium">Database Path</span>
              <span class="text-sm font-mono text-muted-foreground">{{ configuration.SQLITE_DB_PATH }}</span>
            </div>
          </template>
        </CardContent>
      </Card>

       <!-- External Resources -->
      <Card>
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <Globe class="h-5 w-5" />
            External Resources
          </CardTitle>
          <CardDescription>URLs for external data sources.</CardDescription>
        </CardHeader>
        <CardContent class="grid gap-4">
          <div class="flex flex-col gap-2">
            <span class="text-sm font-medium">MITRE DATA</span>
            <span class="text-xs font-mono text-muted-foreground break-all">{{ configuration.MITRE_JSON_URL }}</span>
          </div>
          <div class="flex flex-col gap-2">
            <span class="text-sm font-medium">Atomic Red Team</span>
            <span class="text-xs font-mono text-muted-foreground break-all">{{ configuration.ATOMIC_RED_TEAM_URL }}</span>
          </div>
          <div class="flex flex-col gap-2">
             <span class="text-sm font-medium">Custom Templates</span>
             <span class="text-xs font-mono text-muted-foreground break-all">{{ configuration.CUSTOM_DATA_URL || 'Not Configured' }}</span>
          </div>
        </CardContent>
      </Card>

      <!-- External Authentication -->
      <Card>
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <KeyRound class="h-5 w-5" />
            External Authentication
          </CardTitle>
          <CardDescription>OAuth/OIDC provider configurations.</CardDescription>
        </CardHeader>
        <CardContent>
          <div v-if="!configuration.EXTERNAL_AUTH_CONFIGS || configuration.EXTERNAL_AUTH_CONFIGS.length === 0" class="text-sm text-muted-foreground">
            No external authentication providers configured
          </div>
          <div v-else class="grid gap-6">
            <div v-for="(config, index) in configuration.EXTERNAL_AUTH_CONFIGS" :key="index">
              <div class="font-semibold text-sm mb-3">{{ config.name }}</div>
              <div class="grid gap-4">
                <div class="grid grid-cols-2 items-center gap-4">
                  <span class="text-sm font-medium">Configuration</span>
                  <span class="text-sm font-mono text-muted-foreground">{{ config.configuration }}</span>
                </div>
                <div class="flex flex-col gap-2">
                  <span class="text-sm font-medium">Issuer</span>
                  <span class="text-xs font-mono text-muted-foreground break-all">{{ config.issuer }}</span>
                </div>
                <div class="flex flex-col gap-2">
                  <span class="text-sm font-medium">JWKS URL</span>
                  <span class="text-xs font-mono text-muted-foreground break-all">{{ config.jwks_url }}</span>
                </div>
                <div class="grid grid-cols-2 items-center gap-4">
                  <span class="text-sm font-medium">Audience</span>
                  <span class="text-sm font-mono text-muted-foreground">{{ config.audience }}</span>
                </div>
                <div class="grid grid-cols-2 items-center gap-4">
                  <span class="text-sm font-medium">Username Claim</span>
                  <span class="text-sm font-mono text-muted-foreground">{{ config.username_claim }}</span>
                </div>
                <div class="grid grid-cols-2 items-center gap-4">
                  <span class="text-sm font-medium">Client ID</span>
                  <span class="text-sm font-mono text-muted-foreground">{{ config.client_id }}</span>
                </div>
                <div class="flex flex-col gap-2">
                  <span class="text-sm font-medium">Trusted Email Domains</span>
                  <div v-if="config.trusted_email_domains && config.trusted_email_domains.length > 0" class="flex flex-wrap gap-2">
                    <span v-for="(domain, idx) in config.trusted_email_domains" :key="idx" class="text-xs font-mono bg-muted px-2 py-1 rounded">
                      {{ domain }}
                    </span>
                  </div>
                  <span v-else class="text-xs text-muted-foreground italic">No trusted domains configured</span>
                </div>
                 <div class="grid grid-cols-2 items-center gap-4">
                  <span class="text-sm font-medium">Scope</span>
                  <span class="text-sm font-mono text-muted-foreground">{{ config.scope }}</span>
                </div>
              </div>
              <Separator v-if="index < configuration.EXTERNAL_AUTH_CONFIGS.length - 1" class="mt-6" />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, ref } from 'vue';
import type { components } from '@/types/schema';

type Configuration = components['schemas']['Configuration'];

import {
    AppWindow,
    Database,
    Globe,
    KeyRound,
    Settings,
    Shield,
} from 'lucide-vue-next';
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { api } from '@/services/api';

const configuration = ref<Configuration | null>(null);
const error = ref<string | null>(null);

onMounted(async () => {
    try {
        const response = await api.get<Configuration>('/admin/configuration');
        configuration.value = response.data;
    } catch (e: any) {
        error.value = e.message || 'Failed to load configuration';
    }
});
</script>
