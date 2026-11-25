const ALLOWED_START_KEYWORDS = [
  'SELECT',
  'WITH',
  'DESCRIBE',
  'SUMMARIZE',
  'SHOW',
  'EXPLAIN',
] as const;

const FORBIDDEN_KEYWORDS = [
  'ATTACH',
  'DETACH',
  'COPY',
  'CREATE',
  'DROP',
  'ALTER',
  'INSERT',
  'UPDATE',
  'DELETE',
  'MERGE',
  'REPLACE',
  'TRUNCATE',
  'INSTALL',
  'LOAD',
  'PRAGMA',
  'SET',
  'EXPORT',
  'IMPORT',
  'CALL',
  'EXECUTE',
] as const;

export interface SqlValidationResult {
  ok: boolean;
  error?: string;
}

/**
 * SQL 文字列から文字列リテラルおよびコメントを除去し、複数文チェック等に使える正規化済みテキストを返す。
 */
function stripCommentsAndStrings(sql: string): string {
  let out = '';
  let i = 0;
  while (i < sql.length) {
    const ch = sql[i];
    const next = sql[i + 1];

    // 行コメント
    if (ch === '-' && next === '-') {
      while (i < sql.length && sql[i] !== '\n') i++;
      out += ' ';
      continue;
    }
    // ブロックコメント
    if (ch === '/' && next === '*') {
      i += 2;
      while (i < sql.length && !(sql[i] === '*' && sql[i + 1] === '/')) i++;
      i += 2;
      out += ' ';
      continue;
    }
    // シングルクォート文字列
    if (ch === "'") {
      i++;
      while (i < sql.length) {
        if (sql[i] === "'" && sql[i + 1] === "'") {
          i += 2;
        } else if (sql[i] === "'") {
          i++;
          break;
        } else {
          i++;
        }
      }
      out += ' ';
      continue;
    }
    // ダブルクォート識別子
    if (ch === '"') {
      i++;
      while (i < sql.length) {
        if (sql[i] === '"' && sql[i + 1] === '"') {
          i += 2;
        } else if (sql[i] === '"') {
          i++;
          break;
        } else {
          i++;
        }
      }
      out += ' ';
      continue;
    }
    out += ch;
    i++;
  }
  return out;
}

/**
 * SQL Sandbox で実行可能な読み取り専用単一クエリかを検証する。
 */
export function validateReadOnlySql(sql: string): SqlValidationResult {
  const trimmed = sql.trim();
  if (!trimmed) {
    return { ok: false, error: 'SQL クエリが空です。' };
  }

  const stripped = stripCommentsAndStrings(trimmed).trim();
  if (!stripped) {
    return { ok: false, error: '実行可能な SQL ステートメントが見つかりません。' };
  }

  // 末尾以外のセミコロンを拒否（複数ステートメント防止）
  const withoutTrailingSemicolon = stripped.replace(/;+\s*$/, '');
  if (withoutTrailingSemicolon.includes(';')) {
    return { ok: false, error: '複数の SQL ステートメントを同時に実行することはできません。' };
  }

  const upperTokens = withoutTrailingSemicolon
    .toUpperCase()
    .split(/[^A-Z0-9_]+/)
    .filter(Boolean);

  const firstToken = upperTokens[0];
  if (
    !firstToken ||
    !ALLOWED_START_KEYWORDS.includes(firstToken as (typeof ALLOWED_START_KEYWORDS)[number])
  ) {
    return {
      ok: false,
      error: `読み取り専用クエリ (${ALLOWED_START_KEYWORDS.join(', ')}) のみ実行できます。`,
    };
  }

  for (const token of upperTokens) {
    if (FORBIDDEN_KEYWORDS.includes(token as (typeof FORBIDDEN_KEYWORDS)[number])) {
      return {
        ok: false,
        error: `安全のためキーワード "${token}" の実行は禁止されています。`,
      };
    }
  }

  return { ok: true };
}

function escapeCsvCell(value: unknown): string {
  if (value === null || value === undefined) return '';
  const text = Array.isArray(value) ? JSON.stringify(value) : String(value);
  if (/[",\r\n]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

/**
 * SQL 結果セットを UTF-8 BOM 付き RFC 4180 CSV 文字列に変換する。
 */
export function rowsToCsv(columns: string[], rows: Record<string, unknown>[]): string {
  const header = columns.map(escapeCsvCell).join(',');
  const lines = rows.map((row) => columns.map((col) => escapeCsvCell(row[col])).join(','));
  return `\uFEFF${[header, ...lines].join('\r\n')}`;
}
