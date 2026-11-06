import { describe, expect, it } from 'vitest';
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { SnapshotContext } from '@/lib/context';
import { FocusProvider } from '@/lib/focus';
import QuarterSummary from '@/components/QuarterSummary';
import FlagBadge from '@/components/FlagBadge';
import DomainSummaryTable from '@/components/DomainSummaryTable';
import ProductTable from '@/components/ProductTable';
import ClusterMap from '@/components/ClusterMap';
import StageMark from '@/components/StageMark';
import TrendChart from '@/components/TrendChart';
import AttentionList from '@/components/AttentionList';
import { QuarterContext, quarterSnapshot } from '@/lib/quarter';
import { fitName, textWidth } from '@/lib/cluster';
import golden from '../../../tests/fixtures/golden/2026-W41.json';
import platformGolden from '../../../tests/fixtures/golden/platform-2026-W41.json';
import githubGolden from '../../../tests/fixtures/golden/github-2026-W41.json';
import showcase from '../../../tests/fixtures/showcase/2026-W47.json';
import ReportingStrip, { CoverageNote } from '@/components/Coverage';
import StatStrip, { TechnicalReadiness } from '@/components/StatStrip';
import ProductView from '@/views/ProductView';
import ExecView from '@/views/ExecView';
import DefinitionsView from '@/views/DefinitionsView';
import { DeliveryHealth } from '@/views/DeliveryView';
import { PlatformMark } from '@/components/StageMark';
import { failingProducts, hasGates, platformStage, platformStages } from '@/lib/platform';
import type { Snapshot } from '@/types/snapshot';

const s = golden as unknown as Snapshot;
const wrap = (ui: React.ReactElement, snap: Snapshot = s) =>
  render(
    <SnapshotContext.Provider value={snap}>
      <FocusProvider>{ui}</FocusProvider>
    </SnapshotContext.Provider>,
  );

const sc = showcase as unknown as Snapshot;

describe('QuarterSummary', () => {
  it('leads with one sentence: health, live against expected, the target', () => {
    wrap(<QuarterSummary />, sc);
    const link = screen.getByTestId('tile-link-certified_qtd-org');
    expect(link).toHaveAttribute('href', '#/products?metric=certified_qtd&scope=org');
    expect(screen.getByText('of 23 data products')).toBeInTheDocument();
    const lead = screen.getByTestId('quarter-verdict');
    expect(lead).toHaveAttribute('data-health', 'at-risk');
    expect(lead).toHaveTextContent('Behind. 11 data products live.');
    expect(screen.getByTestId('quarter-expected')).toHaveTextContent('13 expected by today.');
    expect(screen.getByTestId('quarter-target')).toHaveTextContent('Quarter target: 23 by 31 December.');
    expect(screen.queryByTestId('quarter-key')).toBeNull(); // the ring names its parts on hover instead
    const hit = screen.getAllByTestId('ring-hit')[0];
    const at = (turn: number) => {
      const r = (168 - 15) / 2 - 1;
      const a = turn * 2 * Math.PI - Math.PI / 2;
      return { clientX: 84 + r * Math.cos(a), clientY: 84 + r * Math.sin(a) };
    };
    fireEvent.mouseMove(hit, at(0.2)); // 0.2 of the circle: inside the 11 of 23 live
    expect(screen.getByTestId('ring-tip')).toHaveTextContent('11 live');
    fireEvent.mouseMove(hit, at(13 / 23)); // the tick
    expect(screen.getByTestId('ring-tip')).toHaveTextContent('13 expected by today');
    fireEvent.mouseMove(hit, at(0.95)); // the red part
    expect(screen.getByTestId('ring-tip')).toHaveTextContent(/\d+ not planned, 3 of them late/);
    fireEvent.mouseLeave(hit);
    expect(screen.queryByTestId('ring-tip')).toBeNull();
    expect(screen.queryByText(/Is the quarter on track/)).toBeNull();
  });
  it('puts every domain as a certified/target pill in the column of its health', () => {
    wrap(<QuarterSummary />, sc);
    const expected: Record<string, [string, string, number]> = {
      'market-access': ['off-track', '0/3', 0],
      'g-and-a': ['off-track', '1/4', 0.25],
      techops: ['at-risk', '3/7', 0.43],
      patient: ['on-track', '1/2', 0.5],
      'revenue-vials': ['on-track', '1/1', 1],
      'medical-affairs': ['on-track', '1/2', 0.5],
      hcp: ['ahead', '2/2', 1],
      'r-and-d': ['ahead', '2/2', 1],
    };
    for (const [id, [status, frac, done]] of Object.entries(expected)) {
      const pill = within(screen.getByTestId(`board-${status}`)).getByTestId(`domain-health-${id}`);
      expect(pill).toHaveTextContent(frac);
      expect(Number(pill.getAttribute('data-done'))).toBeCloseTo(done, 2);
      expect(parseFloat(within(pill).getByTestId('pill-fill').style.width)).toBeCloseTo(done * 100, 0);
    }
    expect(screen.getAllByText('live / target')).toHaveLength(4); // one visible, three keep the columns aligned
    expect(within(screen.getByTestId('board-off-track')).getByRole('heading').querySelector('[data-icon=stop]')).not.toBeNull();
    expect(within(screen.getByTestId('board-ahead')).getByRole('heading').querySelector('[data-icon=trend-up]')).not.toBeNull();
    expect(screen.getByTestId('no-target')).toHaveTextContent('No target: Channel partner');
    expect(screen.queryByTestId('domain-health-logistics')).toBeNull(); // no products, no target
    expect(screen.queryByText(/TechOps · R&D/)).toBeNull();
    expect(within(screen.getByTestId('board-at-risk')).getByRole('heading')).toHaveTextContent('Behind');
  });
  it('reports a closed quarter as above, met or below target', () => {
    render(
      <QuarterContext.Provider value={{ quarter: '2026-Q3', current: '2026-Q4', closed: true, options: ['2026-Q1', '2026-Q2', '2026-Q3', '2026-Q4'] }}>
        <SnapshotContext.Provider value={quarterSnapshot(s, '2026-Q3')}>
          <QuarterSummary />
        </SnapshotContext.Provider>
      </QuarterContext.Provider>,
    );
    expect(screen.getByTestId('quarter-verdict')).toHaveTextContent('Below target. 4 of 6 data products went live in Q3 2026.');
    expect(within(screen.getByTestId('board-below-target')).getByRole('heading').querySelector('[data-icon=trend-down]')).not.toBeNull();
    expect(screen.getByTestId('board-below-target')).toBeInTheDocument();
    expect(screen.queryByTestId('board-at-risk')).toBeNull();
  });
});

describe('StatStrip', () => {
  it('links each figure to the products behind it, labels self-reported values and lists values when n is small', () => {
    wrap(<StatStrip scope="r-and-d" />);
    expect(screen.getByTestId('tile-link-cycle_time_g1_g4-r-and-d')).toHaveAttribute('data-count', '2');
    expect(screen.getAllByText('Self-reported').length).toBeGreaterThan(0);
    expect(screen.getByText(/n = 2 · 142, 176/)).toBeInTheDocument();
  });
  it('shows a dash with a reason instead of a null', () => {
    wrap(<StatStrip scope="techops" />);
    expect(screen.getByText(/No first consumer recorded/)).toBeInTheDocument();
  });
});

describe('FlagBadge', () => {
  it('always carries a text label and an icon, in sentence case', () => {
    wrap(<FlagBadge code="NOT_UPDATED" reason="38 days" />);
    const badge = screen.getByText('Not updated');
    expect(badge.querySelector('svg')).not.toBeNull();
    expect(badge).toHaveAttribute('title', '38 days');
  });
});

describe('DomainSummaryTable', () => {
  it('shows no health (it belongs to the quarter), links every number and starts collapsed', () => {
    wrap(<DomainSummaryTable />);
    expect(document.querySelector('[data-health]')).toBeNull();
    expect(screen.getByTestId('dh-certified_qtd-hcp')).toHaveAttribute('data-count', '1');
    expect(screen.getByTestId('dh-live_count-r-and-d')).toHaveTextContent('2');
    expect(screen.getByTestId('dh-products-hcp')).toHaveAttribute('data-count', '5');
    expect(screen.queryByTestId('domain-rows-hcp')).toBeNull();
  });
  it('counts every product of a domain under exactly one stage, each count a link', () => {
    wrap(<DomainSummaryTable />);
    for (const d of s.domains.filter((x) => s.products.some((p) => p.domain === x.id))) {
      const links = document.querySelectorAll(`[data-testid^="dh-stage-"][data-testid$="-${d.id}"]`);
      const total = [...links].reduce((n, a) => n + Number(a.getAttribute('data-count')), 0);
      expect(total).toBe(s.products.filter((p) => p.domain === d.id).length);
    }
    expect(screen.getByTestId('dh-stage-in-testing-market-access')).toHaveAttribute('href', '#/products?domain=market-access&stage=In+testing');
  });
  it('opens a domain with its triangle and shows exactly its products', () => {
    wrap(<DomainSummaryTable />);
    const toggle = screen.getByTestId('domain-toggle-techops');
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
    expect(screen.getByTestId('dh-products-techops')).toBeInTheDocument();
    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute('aria-expanded', 'true');
    expect(screen.queryByTestId('dh-products-techops')).toBeNull(); // the rows speak; the figures hide while open
    expect(within(screen.getByTestId('domain-rows-techops')).getAllByTestId('product-row-link')).toHaveLength(4);
    expect(within(screen.getByTestId('domain-rows-techops')).getByText('Data product owner')).toBeInTheDocument();
  });
});

describe('ProductTable grouped by domain', () => {
  it('shows a summary row per domain and collapses a group with its triangle', () => {
    wrap(<ProductTable products={s.products} groupByDomain />);
    expect(screen.queryByTestId('domain-total-hcp')).toBeNull(); // groups start open: no count while open
    expect(screen.getAllByTestId('product-row-link')).toHaveLength(25);
    fireEvent.click(screen.getByTestId('domain-toggle-hcp'));
    expect(screen.getAllByTestId('product-row-link')).toHaveLength(20);
    expect(screen.getByTestId('domain-total-hcp')).toHaveTextContent('5 products');
    expect(screen.getByText('Data product owner')).toBeInTheDocument();
  });
  it('says how many of a domain are shown when the list is filtered', () => {
    wrap(<ProductTable products={s.products.filter((p) => p.lifecycle === 'In testing')} groupByDomain />);
    fireEvent.click(screen.getByText('Collapse all'));
    const shown = screen.getAllByTestId(/^domain-shown-/);
    expect(shown.length).toBeGreaterThan(0);
    expect(shown[0]).toHaveTextContent(/^\d+ of \d+ products$/);
  });
});

describe('ClusterMap', () => {
  it('draws one bubble per product, each a link carrying its stage and its name', () => {
    const groups = s.domains.map((d) => ({ id: d.id, label: d.name, items: s.products.filter((p) => p.domain === d.id) }));
    wrap(<ClusterMap groups={groups} ariaLabel="map" />);
    const bubbles = screen.getAllByTestId('cluster-bubble');
    expect(bubbles).toHaveLength(25);
    expect(bubbles.filter((b) => b.getAttribute('data-stage') === 'Live')).toHaveLength(11);
    expect(bubbles.every((b) => !/\bG[1-6]\b/.test(b.textContent ?? ''))).toBe(true);
    const hcp = bubbles.find((b) => b.getAttribute('data-urn') === 'urn:dp:com:hcp-engagement-mart')!;
    expect(hcp.textContent?.replace(/-/g, '')).toContain('HCP');
    expect(within(screen.getByRole('group', { name: 'map' })).getAllByRole('link')).toHaveLength(25);
    expect(screen.getAllByTestId('attention-dot')).toHaveLength(s.products.filter((p) => p.flags.length > 0).length);
  });
  it('fits names inside the bubble, breaking long words only with a hyphen', () => {
    const inner = 36 - 3 - 3;
    for (const name of ['Manufacturing Batch Genealogy', 'Pharmacovigilance Signals', 'Patient Journey 360', 'IQVIA LAAD MG Weekly']) {
      const { lines, size } = fitName(name, inner);
      expect(lines.length).toBeLessThanOrEqual(3);
      expect(lines.join(' ').replace(/- /g, '')).toBe(name);
      for (const l of lines) expect(textWidth(l, size)).toBeLessThanOrEqual(2 * inner);
    }
  });
});

describe('StageMark', () => {
  it('fills one quarter of the circle per stage, on one green ramp', () => {
    const fills = { 'In design': ['#52A077', '1'], 'In development': ['#5DB884', '2'], 'In testing': ['#79D49B', '3'], Live: ['#A8F0BC', '4'] } as const;
    for (const [stage, [color, quarters]] of Object.entries(fills)) {
      wrap(<StageMark stage={stage as 'Live'} title={stage} />);
      const fill = screen.getByRole('img', { name: stage }).querySelector('[data-quarters]')!;
      expect(fill.getAttribute('data-quarters')).toBe(quarters);
      expect(fill.getAttribute('fill')).toBe(color);
      cleanup();
    }
  });
  it('keeps a dotted ring for Ideation and a red double ring for Failed / retired', () => {
    wrap(<StageMark stage="Ideation" title="Ideation" />);
    expect(screen.getByRole('img', { name: 'Ideation' }).querySelector('[data-quarters]')).toBeNull();
    expect(screen.getByRole('img', { name: 'Ideation' }).querySelector('circle')?.getAttribute('stroke-dasharray')).toMatch(/^0.1 /);
    cleanup();
    wrap(<StageMark stage="Failed / retired" title="Failed / retired" />);
    expect(screen.getByRole('img', { name: 'Failed / retired' }).querySelectorAll('circle')).toHaveLength(2);
  });
});

describe('TrendChart', () => {
  it('switches from quarters to the selected quarter week by week', () => {
    wrap(<TrendChart />);
    expect(screen.getByTestId('trend-chart')).toHaveAttribute('data-unit', 'quarters');
    expect(screen.getByTestId('trend-quarter-2026-Q3')).toBeInTheDocument();
    fireEvent.click(screen.getByTestId('trend-unit-weeks'));
    expect(screen.getByTestId('trend-chart')).toHaveAttribute('data-unit', 'weeks');
    expect(screen.getByRole('heading', { name: 'Q4 2026, week by week' })).toBeInTheDocument();
    expect(screen.getByTestId('trend-week-2026-W41')).toHaveAttribute('data-value', '3');
    expect(screen.getByTestId('trend-week-2026-W52')).toHaveAttribute('data-value', ''); // still ahead
    expect(screen.getAllByText('Target pace').length).toBeGreaterThan(0);
  });
});


const ps = platformGolden as unknown as Snapshot;
const wrapP = (ui: React.ReactElement) =>
  render(
    <SnapshotContext.Provider value={ps}>
      <FocusProvider>{ui}</FocusProvider>
    </SnapshotContext.Provider>,
  );

describe('Data coverage', () => {
  it('says under a number how complete its input is, and links to the products missing it', () => {
    wrap(<CoverageNote id="certified_qtd" scope="org" />);
    const note = screen.getByTestId('coverage-note-certified_qtd-org');
    expect(note).toHaveTextContent('Gate dates for 22 of 23 active products');
    expect(note).toHaveAttribute('href', '#/products?missing=gates');
    expect(note).toHaveAttribute('data-count', '1');
  });
  it('stays silent when the input is complete', () => {
    const { container } = wrap(<CoverageNote id="g4_forecast" scope="org" />);
    expect(container).toBeEmptyDOMElement();
  });
  it('shows the strip while inputs are incomplete, and steps aside once they are not', () => {
    wrapP(<ReportingStrip />);
    expect(screen.getByTestId('coverage-reviewed')).toHaveTextContent('4');
    expect(screen.getByTestId('coverage-reviewed')).toHaveAttribute('data-count', '2');
    expect(screen.getByTestId('coverage-nextdata')).toHaveAttribute('href', '#/products?missing=nextdata');
    cleanup();
    const { container } = wrap(<ReportingStrip />);
    expect(container).toBeEmptyDOMElement(); // golden inbox: every input at 80% or more
  });
});

describe('Technical readiness', () => {
  it('shows the spec score and failing deployments with their sources and links', () => {
    wrapP(<TechnicalReadiness />);
    expect(screen.getByRole('heading', { name: 'Technical readiness' })).toBeInTheDocument();
    expect(screen.getByTestId('tile-link-spec_score_median-org')).toHaveTextContent('74%');
    expect(screen.getByTestId('tile-link-runtime_failing-org')).toHaveAttribute('data-count', '1');
    expect(screen.getByText('of 5 deployed')).toBeInTheDocument();
    expect(screen.getAllByText('Validation tool').length).toBeGreaterThan(0);
  });
  it('steps aside when no platform files are in the inbox', () => {
    const { container } = wrap(<TechnicalReadiness />);
    expect(container).toBeEmptyDOMElement();
  });
});

describe('ProductView platform facts', () => {
  it('lists the NextData deployments and the validation components', () => {
    wrapP(<ProductView urn="nxd:dp-ops-crmsys" />);
    const section = screen.getByTestId('platform-section');
    expect(within(section).getByTestId('platform-runtime')).toHaveTextContent('Started · dev');
    expect(within(section).getByText(/also deployed as crmsys/)).toBeInTheDocument();
    expect(within(section).getAllByRole('row')).toHaveLength(4); // header + 3 deployments
    expect(within(section).getByTestId('platform-spec-score')).toHaveTextContent('73%');
    expect(within(section).getByRole('list', { name: 'Component scores' }).children).toHaveLength(3);
  });
  it('is absent for a product the platform files do not know', () => {
    wrapP(<ProductView urn="urn:dp:com:legacy-cube" />);
    expect(screen.queryByTestId('platform-section')).toBeNull();
  });
});

describe('AttentionList', () => {
  it('names each flag with its reason, the stage in its colour, and counts the rest in the footer', () => {
    wrap(<AttentionList />, sc);
    const items = screen.getAllByTestId('needs-attention-item');
    const flagged = sc.products.filter((p) => p.flags.length > 0).length;
    expect(items.length).toBe(Math.min(6, flagged)); // stacked layout (no panel beside it in jsdom)
    expect(Number(screen.getByTestId('needs-attention-more').getAttribute('data-count'))).toBe(flagged - items.length);
    expect(screen.getByText('G4 Certify is 31 days late. Due 20 Oct.')).toBeInTheDocument();
    const stage = screen.getAllByText('In testing').find((el) => el.tagName === 'STRONG')!;
    expect(stage.getAttribute('style')).toContain('rgb(121, 212, 155)'); // the In testing ring colour
  });
});

const gs = githubGolden as unknown as Snapshot;

describe('GitHub', () => {
  it('adds the deployment tiles to Technical readiness, each linked to its products', () => {
    wrap(<TechnicalReadiness />, gs);
    expect(screen.getByText('From the validation tool, NextData and GitHub.')).toBeInTheDocument();
    expect(screen.getByTestId('tile-link-no_prod_deploy-org')).toHaveAttribute('data-count', '4');
    expect(screen.getByText('of 6 with a repository')).toBeInTheDocument();
    expect(screen.getByTestId('tile-link-deploy_failure_rate-org')).toHaveTextContent('29%');
    expect(screen.getByText('of 7 deployments')).toBeInTheDocument();
    expect(screen.getAllByText('GitHub').length).toBe(3);
  });
  it('leaves the GitHub tiles out when there is no extract', () => {
    wrapP(<TechnicalReadiness />);
    expect(screen.queryByTestId('tile-link-no_prod_deploy-org')).toBeNull();
    expect(screen.getByText('From the validation tool and NextData.')).toBeInTheDocument();
  });
  it('shows the repository and its deployments on the product page', () => {
    wrap(<ProductView urn="nxd:dp-ops-crmsys" />, gs);
    const block = screen.getByTestId('platform-github');
    expect(within(block).getByTestId('github-last-prod')).toHaveTextContent('Last production deploy');
    expect(within(block).getByTestId('github-delivery')).toHaveTextContent('Last 30 days: 4 deployments, 1 failed (25%), 2 in production');
    expect(within(block).getByTestId('delivery-recent').querySelectorAll('tbody tr').length).toBe(6);
    expect(within(block).getByTestId('github-link')).toHaveAttribute('href', 'https://github.example/example-org/edp-ops-dp-crmsys');
    cleanup();
    wrap(<ProductView urn="nxd:dp-hcp-hcp-master" />, gs);
    expect(screen.getByTestId('github-last-prod')).toHaveTextContent('Never deployed to production');
    cleanup();
    wrap(<ProductView urn="urn:dp:com:legacy-cube" />, gs); // not on NextData, but it has a repository
    expect(screen.getByTestId('platform-github')).toBeInTheDocument();
    expect(screen.queryByText('Runtime')).toBeNull();
  });
});

/* The real register has no gate dates yet: the same GitHub week with every gate removed. */
const ng = { ...gs, products: gs.products.map((p) => ({ ...p, gates: [] })) } as Snapshot;

describe('Platform mode (no gate dates)', () => {
  it('switches on only when no product has a gate', () => {
    expect(hasGates(gs)).toBe(true);
    expect(hasGates(ng)).toBe(false);
  });
  it('gives each product its furthest step on the promotion path, and what is failing now', () => {
    const stage = (urn: string) => platformStage(ng, ng.products.find((p) => p.urn === urn)!);
    expect(platformStages(ng).map((st) => st.label)).toEqual(['Not on GitHub', 'Repository', 'Dev', 'Validation', 'Production']);
    expect(stage('nxd:dp-ops-crmsys').label).toBe('Production');
    expect(stage('nxd:dp-hcp-hcp-master')).toMatchObject({ label: 'Validation', step: 2, steps: 3 });
    expect(stage('nxd:dp-claims-rx-claims').label).toBe('Repository'); // a repository with no deployment
    // the furthest along first: hcp_master's dev deploys fail; Rx claims is Failed in NextData
    expect(failingProducts(ng).map((p) => p.name)).toEqual(['HCP master', 'Rx claims']);
  });
  it('draws one ring segment per step of the path', () => {
    const { container } = render(<PlatformMark stage={platformStages(ng)[3]} />);
    expect(container.querySelector('[data-quarters]')?.getAttribute('data-quarters')).toBe('2');
  });
  it('builds the overview from the platform: no quarter, trend or speed and adoption', () => {
    wrap(<ExecView params={new URLSearchParams()} />, ng);
    expect(screen.getByTestId('exec-view')).toHaveAttribute('data-mode', 'platform');
    expect(screen.queryByTestId('quarter-verdict')).toBeNull();
    expect(screen.queryByTestId('attention')).toBeNull();
    expect(screen.getByTestId('delivery-summary')).toBeInTheDocument();
    expect(screen.getAllByTestId('failing-item').map((a) => a.textContent)).toEqual(['HCP master', 'Rx claims']);
    expect(screen.getByTestId('legend-count-iac-apply-p')).toHaveAttribute('data-count', '2');
    expect(screen.getByTestId('legend-count-failing')).toHaveAttribute('data-count', '2');
    expect(screen.getAllByTestId('cluster-bubble').every((b) => !['Ideation', 'Live'].includes(b.getAttribute('data-stage') ?? ''))).toBe(true);
  });
  it('shows delivery health from the extract', () => {
    wrap(<DeliveryHealth detail />, ng);
    expect(screen.getByTestId('del-broken-now')).toHaveTextContent('2');
    expect(screen.getByTestId('del-broken-now')).toHaveTextContent('of 8 repository steps');
    expect(screen.getByTestId('del-bypass-30d')).toHaveTextContent('3 of 3');
    expect(screen.getByTestId('del-recovery')).toHaveTextContent('24 h');
    expect(screen.getByTestId('del-onboarded')).toHaveTextContent('6');
    expect(screen.getByTestId('del-broken-table')).toHaveAttribute('data-count', '2');
  });
  it('leads the product page with delivery, and drops the gates', () => {
    wrap(<ProductView urn="nxd:dp-hcp-hcp-master" />, ng);
    expect(screen.queryByText(/Stage history/)).toBeNull();
    expect(screen.queryByText('Facts')).toBeNull();
    expect(screen.getByTestId('delivery-failing')).toHaveTextContent('Failing now: Dev deploys failing');
    expect(screen.getByRole('heading', { name: /Delivery/ })).toBeInTheDocument();
    expect(screen.getByText('failing since 6 Oct')).toBeInTheDocument();
    expect(screen.getByText(/^last success 20 Sep/)).toBeInTheDocument();
  });
  it('drops the gate columns from the product table and adds delivery', () => {
    wrap(<ProductTable products={ng.products} />, ng);
    const headers = screen.getAllByRole('columnheader').map((h) => h.textContent);
    expect(headers.some((h) => h?.startsWith('Delivery'))).toBe(true);
    for (const gone of ['Stage', 'Next gate', 'Data product owner', 'Flags']) expect(headers).not.toContain(gone);
  });
  it('defines the platform stages and delivery health instead of the gates', () => {
    wrap(<DefinitionsView />, ng);
    expect(screen.queryByText('Domain health')).toBeNull();
    expect(screen.queryByText('Stages and the gates between them')).toBeNull();
    expect(screen.getByTestId('pstage-def-iac-apply-v')).toHaveTextContent('Validation');
    expect(screen.getByText('Delivery health')).toBeInTheDocument();
  });
});
