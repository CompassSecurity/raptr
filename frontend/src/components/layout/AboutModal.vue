<script setup lang="ts">
import { ExternalLink } from '@lucide/vue';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';

defineProps<{
    open: boolean;
}>();

defineEmits<(e: 'update:open', value: boolean) => void>();

const appVersion = __APP_VERSION__ || 'Unknown';
</script>

<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent class="sm:max-w-md">
      <DialogHeader>
        <DialogTitle>About RAPTR</DialogTitle>
      </DialogHeader>
      
      <div class="space-y-6 py-4">
        <!-- Version Info -->
        <div class="flex items-center justify-between border-b pb-4">
          <span class="text-sm font-medium">Version</span>
          <span class="text-sm text-muted-foreground font-mono bg-muted px-2 py-1 rounded-md">{{ appVersion }}</span>
        </div>

        <!-- Credits -->
        <div class="space-y-4">
          <h4 class="text-sm font-medium leading-none">Credits & Acknowledgements</h4>
          
          <div class="rounded-lg border p-4 space-y-4 bg-muted/30">

            <!-- Compass Security -->
            <div class="space-y-2">
              <div class="flex items-center gap-2">
                <span class="text-sm font-medium">Compass Security</span>
                <a href="https://www.compass-security.com/" target="_blank" rel="noopener noreferrer" class="text-muted-foreground hover:text-foreground transition-colors">
                  <ExternalLink class="h-3 w-3" />
                  <span class="sr-only">Visit Compass Security Website</span>
                </a>
              </div>
              <p class="text-xs text-muted-foreground leading-relaxed">
                RAPTR is a tool developed by Compass Security.
              </p>
            </div>

            <div class="h-px bg-border"></div>
            <!-- MITRE -->
            <div class="space-y-2">
              <div class="flex items-center gap-2">
                <span class="text-sm font-medium">MITRE ATT&CK®</span>
                <a href="https://attack.mitre.org/" target="_blank" rel="noopener noreferrer" class="text-muted-foreground hover:text-foreground transition-colors">
                  <ExternalLink class="h-3 w-3" />
                  <span class="sr-only">Visit MITRE ATT&CK Website</span>
                </a>
              </div>
              <p class="text-xs text-muted-foreground leading-relaxed">
                This project uses the MITRE ATT&CK® framework. MITRE ATT&CK and ATT&CK are registered trademarks of The MITRE Corporation.
              </p>
            </div>

            <div class="h-px bg-border"></div>

            <!-- Atomic Red Team -->
            <div class="space-y-2">
              <div class="flex items-center gap-2">
                <span class="text-sm font-medium">Atomic Red Team™</span>
                <a href="https://atomicredteam.io/" target="_blank" rel="noopener noreferrer" class="text-muted-foreground hover:text-foreground transition-colors">
                  <ExternalLink class="h-3 w-3" />
                  <span class="sr-only">Visit Atomic Red Team Website</span>
                </a>
              </div>
              <p class="text-xs text-muted-foreground leading-relaxed">
                This project includes execution templates and logic inspired by Atomic Red Team, an open-source library maintained by Red Canary.
              </p>
            </div>
          </div>
        </div>
      </div>
    </DialogContent>
  </Dialog>
</template>
