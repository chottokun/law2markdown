import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { ArticleSummary, LawCatalogEntry } from '../lib/types';

const { cytoscapeMock, cyInstanceMock, fetchLawArticlesMock } = vi.hoisted(() => {
  const instance = {
    on: vi.fn(),
    one: vi.fn(),
    resize: vi.fn(),
    fit: vi.fn(),
    zoom: vi.fn(() => 1),
    width: vi.fn(() => 800),
    height: vi.fn(() => 600),
    animate: vi.fn(),
    destroy: vi.fn(),
    elements: vi.fn(() => ({
      removeClass: vi.fn(),
      difference: vi.fn(() => ({ addClass: vi.fn() })),
    })),
    getElementById: vi.fn(() => ({ nonempty: () => false })),
  };
  return {
    cyInstanceMock: instance,
    cytoscapeMock: vi.fn(() => instance),
    fetchLawArticlesMock: vi.fn(),
  };
});

vi.mock('cytoscape', () => ({
  default: cytoscapeMock,
}));

vi.mock('../lib/queries', () => ({
  fetchLawArticles: fetchLawArticlesMock,
}));

import { GraphTab } from './GraphTab';

const sampleArticles: ArticleSummary[] = [
  {
    law_id: '321CONSTITUTION',
    article_num: '1',
    hierarchy_path: '日本国憲法 > 第一章　天皇 > 第一条',
    title: '日本国憲法 第一条',
    outbound_references: ['art_002_第二条'],
    inbound_references: [],
    defined_terms: [],
  },
  {
    law_id: '321CONSTITUTION',
    article_num: '2',
    hierarchy_path: '日本国憲法 > 第一章　天皇 > 第二条',
    title: '日本国憲法 第二条',
    outbound_references: [],
    inbound_references: ['art_001_第一条'],
    defined_terms: [],
  },
];

const catalog: LawCatalogEntry[] = [
  {
    law_id: '321CONSTITUTION',
    law_num: '昭和二十一年憲法',
    law_title: '日本国憲法',
    article_count: 2,
  },
];

describe('GraphTab', () => {
  beforeEach(() => {
    cytoscapeMock.mockClear();
    cyInstanceMock.resize.mockClear();
    cyInstanceMock.animate.mockClear();
    cyInstanceMock.zoom.mockReturnValue(1);
    fetchLawArticlesMock.mockReset();
  });

  it('keeps the canvas container mounted while loading and initializes Cytoscape after resolve', async () => {
    let resolveFetch!: (value: ArticleSummary[]) => void;
    fetchLawArticlesMock.mockImplementation(
      () =>
        new Promise<ArticleSummary[]>((resolve) => {
          resolveFetch = resolve;
        }),
    );

    const { container } = render(
      <GraphTab
        catalog={catalog}
        selectedLawId="321CONSTITUTION"
        selectedArticleNum={null}
        onSelectLaw={vi.fn()}
        onOpenInViewer={vi.fn()}
      />,
    );

    expect(screen.getByText('ネットワークデータを構築中...')).toBeInTheDocument();
    expect(container.querySelector('.graph-canvas')).not.toBeNull();

    resolveFetch(sampleArticles);

    await waitFor(() => {
      expect(cytoscapeMock).toHaveBeenCalledTimes(1);
    });

    const firstCallArg = (cytoscapeMock.mock.calls as unknown[][])[0][0] as {
      container: HTMLElement | null;
      elements: unknown[];
      wheelSensitivity: number;
      minZoom: number;
      maxZoom: number;
      textureOnViewport: boolean;
      motionBlur: boolean;
    };
    expect(firstCallArg.container).toBeInstanceOf(HTMLElement);
    expect(firstCallArg.elements.length).toBe(3);
    expect(firstCallArg.wheelSensitivity).toBe(0.2);
    expect(firstCallArg.minZoom).toBe(0.1);
    expect(firstCallArg.maxZoom).toBe(4);
    expect(firstCallArg.textureOnViewport).toBe(true);
    expect(firstCallArg.motionBlur).toBe(false);
    expect(cyInstanceMock.resize).toHaveBeenCalled();
    expect(screen.getByText('条文ノード: 2')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: '拡大' }));
    expect(cyInstanceMock.animate).toHaveBeenCalledWith(
      expect.objectContaining({
        zoom: expect.objectContaining({ level: 1.25 }),
      }),
    );

    fireEvent.click(screen.getByRole('button', { name: '縮小' }));
    expect(cyInstanceMock.animate).toHaveBeenCalledWith(
      expect.objectContaining({
        zoom: expect.objectContaining({ level: 0.8 }),
      }),
    );
  });

  it('displays an error overlay if fetching articles fails', async () => {
    fetchLawArticlesMock.mockRejectedValue(new Error('DuckDB query failed'));

    render(
      <GraphTab
        catalog={catalog}
        selectedLawId="321CONSTITUTION"
        selectedArticleNum={null}
        onSelectLaw={vi.fn()}
        onOpenInViewer={vi.fn()}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText('DuckDB query failed')).toBeInTheDocument();
    });
    expect(cytoscapeMock).not.toHaveBeenCalled();
  });
});
