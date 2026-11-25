import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { ArticleContentRow, LawCatalogEntry } from '../lib/types';

const { fetchLawArticlesWithContentMock } = vi.hoisted(() => ({
  fetchLawArticlesWithContentMock: vi.fn(),
}));

vi.mock('../lib/queries', () => ({
  fetchLawArticlesWithContent: fetchLawArticlesWithContentMock,
}));

import { DiffTab } from './DiffTab';

const catalog: LawCatalogEntry[] = [
  {
    law_id: '325AC0000000226_20250401_001',
    law_num: '昭和二十五年法律第二百二十六号',
    law_title: '地方税法',
    article_count: 2,
  },
  {
    law_id: '325AC0000000226_20260401_002',
    law_num: '昭和二十五年法律第二百二十六号',
    law_title: '地方税法',
    article_count: 2,
  },
];

const oldRows: ArticleContentRow[] = [
  { article_num: '1', hierarchy_path: '地方税法 > 第一条', title: '地方税法 第一条', content: '旧規定' },
  { article_num: '2', hierarchy_path: '地方税法 > 第二条', title: '地方税法 第二条', content: '不変' },
];

const newRows: ArticleContentRow[] = [
  { article_num: '1', hierarchy_path: '地方税法 > 第一条', title: '地方税法 第一条', content: '新規定' },
  { article_num: '2', hierarchy_path: '地方税法 > 第二条', title: '地方税法 第二条', content: '不変' },
];

describe('DiffTab', () => {
  beforeEach(() => {
    fetchLawArticlesWithContentMock.mockReset();
  });

  it('loads two versions of a law and renders line diff for modified articles', async () => {
    fetchLawArticlesWithContentMock.mockImplementation(async (lawId: string) =>
      lawId.includes('20250401') ? oldRows : newRows,
    );

    const onOpenInViewer = vi.fn();
    render(
      <DiffTab catalog={catalog} onOpenInViewer={onOpenInViewer} onNotify={vi.fn()} />,
    );

    await waitFor(() => {
      expect(screen.getByText('変更 1')).toBeInTheDocument();
    });

    expect(screen.getByText('旧規定')).toBeInTheDocument();
    expect(screen.getByText('新規定')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: '新版を開く' }));
    expect(onOpenInViewer).toHaveBeenCalledWith('325AC0000000226_20260401_002', '1');
  });
});
