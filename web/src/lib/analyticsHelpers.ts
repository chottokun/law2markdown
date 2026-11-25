import type { LawCatalogEntry } from './types';

/**
 * e-Gov の改正版別 law_id（例: `325AC0000000226_20250401_...`）から
 * 同一法令を表すベースキーを抽出する。
 */
export function getBaseLawKey(lawId: string, lawNum: string, lawTitle: string): string {
  const prefix = lawId.split('_')[0]?.trim();
  if (prefix) return prefix;
  return lawNum.trim() || lawTitle.trim();
}

/**
 * 同一法令の改正版・未施行版を1件の代表エントリへ集約する。
 * law_id 昇順の先頭（現行・最早施行版）を代表として残し、article_count 降順で返す。
 */
export function deduplicateLawCatalog(catalog: LawCatalogEntry[]): LawCatalogEntry[] {
  const byKey = new Map<string, LawCatalogEntry>();

  for (const entry of catalog) {
    const key = getBaseLawKey(entry.law_id, entry.law_num, entry.law_title);
    const existing = byKey.get(key);
    if (!existing || entry.law_id.localeCompare(existing.law_id) < 0) {
      byKey.set(key, entry);
    }
  }

  return Array.from(byKey.values()).sort(
    (a, b) => b.article_count - a.article_count || a.law_title.localeCompare(b.law_title, 'ja'),
  );
}

/**
 * ランキング行から同一法令（law_id プレフィックス / law_title）の重複を除外して上位 limit 件を返す。
 */
export function deduplicateLawRanking<
  T extends { law_id: string; law_title: string; count: number },
>(rows: T[], limit: number): T[] {
  const seen = new Set<string>();
  const result: T[] = [];

  for (const row of rows) {
    const key = getBaseLawKey(row.law_id, '', row.law_title);
    if (seen.has(key)) continue;
    seen.add(key);
    result.push(row);
    if (result.length >= limit) break;
  }

  return result;
}
