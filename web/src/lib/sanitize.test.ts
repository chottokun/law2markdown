import { describe, expect, it } from 'vitest';
import { renderSafeMarkdown, stripHtmlTags } from './sanitize';

describe('renderSafeMarkdown', () => {
  it('renders headings, paragraphs, and preserves anchor id attributes and tables', () => {
    const md = [
      '# 第一条',
      '',
      '<a id="p1"></a>**（１）** 本文テキスト',
      '',
      '| 項目 | 内容 |',
      '| --- | --- |',
      '| A | B |',
    ].join('\n');

    const html = renderSafeMarkdown(md);
    expect(html).toContain('<h1>第一条</h1>');
    expect(html).toContain('<a id="p1"></a>');
    expect(html).toContain('<strong>（１）</strong>');
    expect(html).toContain('<table>');
    expect(html).toContain('<td>A</td>');
  });

  it('strips dangerous script tags, event handlers, and javascript: URLs', () => {
    const malicious = [
      '<script>alert(1)</script>',
      '',
      '<img src="x" onerror="alert(2)">',
      '',
      '[click](javascript:alert(3))',
      '',
      '<iframe src="https://evil.example"></iframe>',
    ].join('\n');

    const html = renderSafeMarkdown(malicious);
    expect(html).not.toContain('<script');
    expect(html).not.toContain('onerror');
    expect(html).not.toContain('javascript:');
    expect(html).not.toContain('<iframe');
  });
});

describe('stripHtmlTags', () => {
  it('removes anchor and formatting tags while keeping readable text', () => {
    const raw = '<a id="p1"></a>**（１）** 労働者は、事業場で作業する。';
    expect(stripHtmlTags(raw)).toBe('**（１）** 労働者は、事業場で作業する。');
  });
});
