import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';

const daily = defineCollection({
  loader: glob({
    pattern: '*.json',
    base: './content/daily',
  }),
});

export const collections = { daily };
