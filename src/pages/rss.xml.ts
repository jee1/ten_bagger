import rss from '@astrojs/rss';
import type { APIContext } from 'astro';

import { getAllDates, getDailyEntry } from '../lib/daily';
import {
  countWeekPicks,
  buildWeeklyDayRow,
  groupDatesByIsoWeek,
  isoWeekDateRange,
  listIsoWeekKeys,
  parseIsoWeekKey,
} from '../lib/weekly';
import { FEED_DISCLAIMER, buildRssItems, buildWeeklyRssItem } from '../lib/rss';

export async function GET(context: APIContext) {
  // This repo's astro `site` already includes the Pages path prefix (e.g. .../ten_bagger).
  const siteUrl = context.site ?? new URL(import.meta.env.SITE || 'https://tenbagger.finnaut.com');
  const site = siteUrl.href.replace(/\/+$/, '');

  const dates = getAllDates();
  const loaded = await Promise.all(
    dates.map(async (date) => {
      const entry = await getDailyEntry(date);
      return entry ? { entry } : null;
    }),
  );
  const inputs = loaded.filter((row): row is { entry: NonNullable<typeof row>['entry'] } => row !== null);
  const dailyItems = buildRssItems(inputs, { site });
  const weekKeys = listIsoWeekKeys(dates);
  const weeklyItems: ReturnType<typeof buildWeeklyRssItem>[] = [];
  if (weekKeys.length > 0) {
    const weekKey = weekKeys[0]!;
    const weekDates = groupDatesByIsoWeek(dates).get(weekKey) ?? [];
    const weekEntries = (
      await Promise.all(weekDates.map(async (date) => getDailyEntry(date)))
    )
      .filter((entry) => entry != null)
      .map((entry) => buildWeeklyDayRow(entry));
    const { isoYear, isoWeek } = parseIsoWeekKey(weekKey);
    const { start, end } = isoWeekDateRange(isoYear, isoWeek);
    weeklyItems.push(
      buildWeeklyRssItem(
        { weekKey, pickCount: countWeekPicks(weekEntries), rangeStart: start, rangeEnd: end },
        { site },
      ),
    );
  }
  const items = [...weeklyItems, ...dailyItems];

  return rss({
    title: 'Ten Bagger Daily',
    description: `Daily rule-based ten-bagger candidate picks (KR/US). ${FEED_DISCLAIMER}`,
    site: siteUrl,
    items: items.map((item) => ({
      title: item.title,
      description: item.description,
      // Absolute URL — @astrojs/rss resolves relative links against origin only,
      // dropping this project's path-prefixed `site` (…/ten_bagger).
      link: item.link,
      pubDate: item.pubDate,
      guid: item.guid,
    })),
    customData: `<language>en</language>`,
  });
}
