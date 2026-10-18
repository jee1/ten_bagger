import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

import type { DailyEntry } from './lib/types';

const daily = defineCollection({
  loader: glob({
    pattern: '*.json',
    base: './content/daily',
  }),
  schema: z
    .looseObject({
      date: z.string(),
      market: z.enum(['KR', 'US']),
      status: z.enum(['pick', 'no_pick']),
    })
    .transform((data): DailyEntry => data as DailyEntry),
});

export const collections = { daily };
