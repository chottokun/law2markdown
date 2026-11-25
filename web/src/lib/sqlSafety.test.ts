import { describe, expect, it } from 'vitest';
import { rowsToCsv, validateReadOnlySql } from './sqlSafety';

describe('validateReadOnlySql', () => {
  it('allows valid SELECT, WITH, DESCRIBE, SUMMARIZE, SHOW, and EXPLAIN queries', () => {
    expect(validateReadOnlySql('SELECT * FROM laws_articles LIMIT 10').ok).toBe(true);
    expect(
      validateReadOnlySql('WITH c AS (SELECT law_id FROM laws_articles) SELECT * FROM c;').ok,
    ).toBe(true);
    expect(validateReadOnlySql('  describe laws_articles ').ok).toBe(true);
    expect(validateReadOnlySql('SUMMARIZE laws_articles').ok).toBe(true);
    expect(validateReadOnlySql('SHOW TABLES').ok).toBe(true);
    expect(validateReadOnlySql('EXPLAIN SELECT 1').ok).toBe(true);
  });

  it('rejects empty queries, multiple statements, and mutating/system commands', () => {
    expect(validateReadOnlySql('   ').ok).toBe(false);
    expect(validateReadOnlySql('DROP TABLE laws_articles').ok).toBe(false);
    expect(validateReadOnlySql('CREATE TABLE t (x INT)').ok).toBe(false);
    expect(validateReadOnlySql('ATTACH \'foo.db\' AS f').ok).toBe(false);
    expect(validateReadOnlySql('COPY laws_articles TO \'out.csv\'').ok).toBe(false);
    expect(validateReadOnlySql('INSTALL httpfs').ok).toBe(false);
    expect(validateReadOnlySql('SELECT 1; SELECT 2').ok).toBe(false);
    expect(validateReadOnlySql("SELECT * FROM laws_articles; DROP VIEW laws_articles").ok).toBe(
      false,
    );
  });

  it('allows semicolons inside string literals', () => {
    expect(validateReadOnlySql("SELECT ';' AS sep FROM laws_articles LIMIT 1").ok).toBe(true);
  });
});

describe('rowsToCsv', () => {
  it('formats columns and rows with UTF-8 BOM and RFC 4180 escaping', () => {
    const csv = rowsToCsv(
      ['law_title', 'note'],
      [
        { law_title: '民法', note: 'hello, "world"' },
        { law_title: '刑法', note: 'line1\nline2' },
      ],
    );
    expect(csv.startsWith('\uFEFF')).toBe(true);
    expect(csv).toContain('law_title,note\r\n');
    expect(csv).toContain('民法,"hello, ""world"""\r\n');
    expect(csv).toContain('刑法,"line1\nline2"');
  });
});
