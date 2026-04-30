<script setup lang="ts">
import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-vue-next';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

const PAGE_SIZE_OPTIONS = [10, 20, 50, 100, 1000];

interface PaginationMeta {
  total: number;
  page: number;
  size: number;
  pages: number;
}

const props = defineProps<{
  pagination: PaginationMeta;
  pageSize?: number;
}>();

const emit = defineEmits<{
  (e: 'page-change', page: number): void;
  (e: 'page-size-change', size: number): void;
}>();

const goToPage = (page: number) => {
  if (page >= 1 && page <= props.pagination.pages) {
    emit('page-change', page);
  }
};

const handlePageSizeChange = (value: unknown) => {
  if (value !== null && value !== undefined) {
    emit('page-size-change', parseInt(String(value), 10));
  }
};

const getPageNumbers = () => {
  const { page, pages } = props.pagination;
  const pageNumbers: number[] = [];
  const maxVisible = 5;
  
  if (pages <= maxVisible) {
    for (let i = 1; i <= pages; i++) {
      pageNumbers.push(i);
    }
  } else {
    if (page <= 3) {
      for (let i = 1; i <= 4; i++) pageNumbers.push(i);
      pageNumbers.push(-1); // Ellipsis
      pageNumbers.push(pages);
    } else if (page >= pages - 2) {
      pageNumbers.push(1);
      pageNumbers.push(-1);
      for (let i = pages - 3; i <= pages; i++) pageNumbers.push(i);
    } else {
      pageNumbers.push(1);
      pageNumbers.push(-1);
      for (let i = page - 1; i <= page + 1; i++) pageNumbers.push(i);
      pageNumbers.push(-1);
      pageNumbers.push(pages);
    }
  }
  
  return pageNumbers;
};
</script>

<template>
  <div class="flex items-center justify-between">
    <div class="flex items-center gap-4">
      <div class="text-sm text-muted-foreground">
        Showing {{ Math.min((pagination.page - 1) * pagination.size + 1, pagination.total) }}-{{ Math.min(pagination.page * pagination.size, pagination.total) }} of {{ pagination.total }} results
      </div>
      
      <!-- Page Size Selector -->
      <div class="flex items-center gap-2">
        <span class="text-sm text-muted-foreground">Show</span>
        <Select :model-value="String(pageSize ?? pagination.size)" @update:model-value="handlePageSizeChange">
          <SelectTrigger class="h-8 w-[80px]">
            <SelectValue :placeholder="String(pageSize ?? pagination.size)" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem 
              v-for="size in PAGE_SIZE_OPTIONS" 
              :key="size" 
              :value="String(size)"
            >
              {{ size }}
            </SelectItem>
          </SelectContent>
        </Select>
        <span class="text-sm text-muted-foreground">per page</span>
      </div>
    </div>
    
    <div class="flex items-center gap-2">
      <Button
        variant="outline"
        size="sm"
        :disabled="pagination.page === 1"
        @click="goToPage(1)"
      >
        <ChevronsLeft class="h-4 w-4" />
      </Button>
      <Button
        variant="outline"
        size="sm"
        :disabled="pagination.page === 1"
        @click="goToPage(pagination.page - 1)"
      >
        <ChevronLeft class="h-4 w-4" />
      </Button>
      
      <template v-for="(pageNum, index) in getPageNumbers()" :key="index">
        <Button
          v-if="pageNum === -1"
          variant="ghost"
          size="sm"
          disabled
        >
          ...
        </Button>
        <Button
          v-else
          :variant="pageNum === pagination.page ? 'default' : 'outline'"
          size="sm"
          @click="goToPage(pageNum)"
        >
          {{ pageNum }}
        </Button>
      </template>
      
      <Button
        variant="outline"
        size="sm"
        :disabled="pagination.page === pagination.pages || pagination.pages === 0"
        @click="goToPage(pagination.page + 1)"
      >
        <ChevronRight class="h-4 w-4" />
      </Button>
      <Button
        variant="outline"
        size="sm"
        :disabled="pagination.page === pagination.pages || pagination.pages === 0"
        @click="goToPage(pagination.pages)"
      >
        <ChevronsRight class="h-4 w-4" />
      </Button>
    </div>
  </div>
</template>
