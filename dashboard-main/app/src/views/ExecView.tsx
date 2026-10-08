/* #/  Executive overview, for the quarter chosen in the bar at the top (#/?q=2026-Q3; the current quarter by
   default). Row one answers "is the quarter on track, which domain is not"; then every product by domain and
   lifecycle stage beside what needs attention; technical readiness (current week, when the platform files are in
   the inbox); speed and adoption; the trend by quarter or by week; and how complete the inputs are. */

import { useMemo } from 'react';
import QuarterSummary from '@/components/QuarterSummary';
import ReportingStrip from '@/components/Coverage';
import DomainClusters from '@/components/DomainClusters';
import AttentionList, { DeliveredList } from '@/components/AttentionList';
import StatStrip, { TechnicalReadiness } from '@/components/StatStrip';
import TrendChart from '@/components/TrendChart';
import { SnapshotContext, useSnapshot } from '@/lib/context';
import { QuarterContext, pickQuarter, quarterOptions, quarterSnapshot, type QuarterState } from '@/lib/quarter';

export default function ExecView({ params }: { params: URLSearchParams }) {
  const s = useSnapshot();
  const quarter = pickQuarter(s, params.get('q'));
  const view = useMemo(() => quarterSnapshot(s, quarter), [s, quarter]);
  const state = useMemo<QuarterState>(() => ({ quarter, current: s.quarter, closed: quarter !== s.quarter, options: quarterOptions(s) }), [quarter, s]);
  return (
    <QuarterContext.Provider value={state}>
      <SnapshotContext.Provider value={view}>
        <div className="space-y-6" data-testid="exec-view" data-quarter={quarter}>
          <QuarterSummary />
          <div className="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1fr)_380px]">
            <DomainClusters />
            {state.closed ? <DeliveredList /> : <AttentionList />}
          </div>
          <TechnicalReadiness />
          <StatStrip />
          <TrendChart />
          <ReportingStrip />
        </div>
      </SnapshotContext.Provider>
    </QuarterContext.Provider>
  );
}
