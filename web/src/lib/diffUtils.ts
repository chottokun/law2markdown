import { getBaseLawKey } from './analyticsHelpers';
import { stripHtmlTags } from './sanitize';
import type { ArticleContentRow, LawCatalogEntry } from './types';

export interface MultiVersionLawGroup {
  baseKey: string;
  lawTitle: string;
  lawNum: string;
  versions: LawCatalogEntry[];
}

export type ArticleDiffKind = 'modified' | 'added' | 'removed';

export interface ArticleDiffItem {
  article_num: string;
  kind: ArticleDiffKind;
  title: string;
  hierarchy_path: string;
  oldContent: string;
  newContent: string;
}

export interface ArticleDiffSummary {
  items: ArticleDiffItem[];
  modifiedCount: number;
  addedCount: number;
  removedCount: number;
  unchangedCount: number;
}

export interface DiffLine {
  type: 'context' | 'added' | 'removed';
  text: string;
}

/**
 * e-Gov の版別 law_id（例: `325AC0000000226_20250401_507AC0000000001`）から
 * 施行日ベースの分かりやすいラベルを生成する。
 */
export function parseLawVersionLabel(lawId: string): string {
  const match = lawId.match(/^[^_]+_(\d{4})(\d{2})(\d{2})(?:_(.+))?$/);
  if (!match) return lawId;
  const [, year, month, day, amendId] = match;
  const dateLabel = `${year}-${month}-${day} 施行版`;
  return amendId ? `${dateLabel} (${amendId.slice(0, 10)})` : dateLabel;
}

/**
 * 複数バージョン（施行日別・未施行版など）が収録されている法令をグルーピングして返す。
 */
export function findMultiVersionLaws(catalog: LawCatalogEntry[]): MultiVersionLawGroup[] {
  const groups = new Map<string, LawCatalogEntry[]>();

  for (const entry of catalog) {
    const key = getBaseLawKey(entry.law_id, entry.law_num, entry.law_title);
    const list = groups.get(key) ?? [];
    list.push(entry);
    groups.set(key, list);
  }

  const multi: MultiVersionLawGroup[] = [];
  for (const [baseKey, versions] of groups.entries()) {
    if (versions.length < 2) continue;
    const sorted = [...versions].sort((a, b) => a.law_id.localeCompare(b.law_id));
    multi.push({
      baseKey,
      lawTitle: sorted[0].law_title,
      lawNum: sorted[0].law_num,
      versions: sorted,
    });
  }

  multi.sort(
    (a, b) =>
      b.versions.length - a.versions.length ||
      b.versions[0].article_count - a.versions[0].article_count ||
      a.lawTitle.localeCompare(b.lawTitle, 'ja'),
  );
  return multi;
}

function normalizeForDiff(raw: string): string {
  return stripHtmlTags(raw).replace(/\r\n/g, '\n').trim();
}

function compareArticleNums(a: string, b: string): number {
  const partsA = a.split('_').map((p) => Number.parseInt(p, 10));
  const partsB = b.split('_').map((p) => Number.parseInt(p, 10));
  const len = Math.max(partsA.length, partsB.length);
  for (let i = 0; i < len; i++) {
    const va = partsA[i] ?? 0;
    const vb = partsB[i] ?? 0;
    if (Number.isNaN(va) || Number.isNaN(vb)) {
      return a.localeCompare(b, 'ja');
    }
    if (va !== vb) return va - vb;
  }
  return 0;
}

/**
 * 旧版と新版の条文一覧を比較し、変更・新設・削除された条文リストを生成する。
 */
export function computeArticleDiffList(
  oldArticles: ArticleContentRow[],
  newArticles: ArticleContentRow[],
): ArticleDiffSummary {
  const oldMap = new Map<string, ArticleContentRow>();
  for (const art of oldArticles) {
    oldMap.set(art.article_num, art);
  }

  const newMap = new Map<string, ArticleContentRow>();
  for (const art of newArticles) {
    newMap.set(art.article_num, art);
  }

  const allKeys = Array.from(new Set([...oldMap.keys(), ...newMap.keys()])).sort(compareArticleNums);

  const items: ArticleDiffItem[] = [];
  let modifiedCount = 0;
  let addedCount = 0;
  let removedCount = 0;
  let unchangedCount = 0;

  for (const key of allKeys) {
    const oldArt = oldMap.get(key);
    const newArt = newMap.get(key);

    if (!oldArt && newArt) {
      addedCount++;
      items.push({
        article_num: key,
        kind: 'added',
        title: newArt.title,
        hierarchy_path: newArt.hierarchy_path,
        oldContent: '',
        newContent: normalizeForDiff(newArt.content),
      });
    } else if (oldArt && !newArt) {
      removedCount++;
      items.push({
        article_num: key,
        kind: 'removed',
        title: oldArt.title,
        hierarchy_path: oldArt.hierarchy_path,
        oldContent: normalizeForDiff(oldArt.content),
        newContent: '',
      });
    } else if (oldArt && newArt) {
      const oldNorm = normalizeForDiff(oldArt.content);
      const newNorm = normalizeForDiff(newArt.content);
      if (oldNorm !== newNorm) {
        modifiedCount++;
        items.push({
          article_num: key,
          kind: 'modified',
          title: newArt.title,
          hierarchy_path: newArt.hierarchy_path,
          oldContent: oldNorm,
          newContent: newNorm,
        });
      } else {
        unchangedCount++;
      }
    }
  }

  return {
    items,
    modifiedCount,
    addedCount,
    removedCount,
    unchangedCount,
  };
}

/**
 * 2つのテキストを行単位の LCS で比較し、追加・削除・一致行を返す。
 */
export function computeLineDiff(oldText: string, newText: string): DiffLine[] {
  const oldLines = oldText ? oldText.split('\n') : [];
  const newLines = newText ? newText.split('\n') : [];

  if (oldLines.length === 0 && newLines.length === 0) return [];
  if (oldLines.length === 0) return newLines.map((text) => ({ type: 'added', text }));
  if (newLines.length === 0) return oldLines.map((text) => ({ type: 'removed', text }));

  // 極めて巨大な条文でのメモリ過多を防ぐためのフォールバック
  if (oldLines.length * newLines.length > 250_000) {
    return [
      ...oldLines.map((text) => ({ type: 'removed' as const, text })),
      ...newLines.map((text) => ({ type: 'added' as const, text })),
    ];
  }

  const m = oldLines.length;
  const n = newLines.length;
  const dp: Uint32Array[] = Array.from({ length: m + 1 }, () => new Uint32Array(n + 1));

  for (let i = m - 1; i >= 0; i--) {
    for (let j = n - 1; j >= 0; j--) {
      if (oldLines[i] === newLines[j]) {
        dp[i][j] = dp[i + 1][j + 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i + 1][j], dp[i][j + 1]);
      }
    }
  }

  const diff: DiffLine[] = [];
  let i = 0;
  let j = 0;
  while (i < m && j < n) {
    if (oldLines[i] === newLines[j]) {
      diff.push({ type: 'context', text: oldLines[i] });
      i++;
      j++;
    } else if (dp[i + 1][j] >= dp[i][j + 1]) {
      diff.push({ type: 'removed', text: oldLines[i] });
      i++;
    } else {
      diff.push({ type: 'added', text: newLines[j] });
      j++;
    }
  }
  while (i < m) {
    diff.push({ type: 'removed', text: oldLines[i++] });
  }
  while (j < n) {
    diff.push({ type: 'added', text: newLines[j++] });
  }

  return diff;
}
