import { useSnapshot } from '@/lib/context';
import { fmtDateTime, fmtDateTimeZone, plural } from '@/lib/format';
import { href } from '@/lib/router';

export default function Footer() {
  const s = useSnapshot();
  const warnings = s.dataQuality.filter((d) => d.severity === 'warning').length;
  const latest = s.sources.filter((x) => x.status !== 'missing').map((x) => x.asOf).sort().at(-1);
  return (
    <footer className="mt-12 border-t border-line pt-5 pb-8 text-small text-ink-3">
      <div className="flex flex-wrap items-center gap-x-5 gap-y-1.5">
        <span>
          Last updated <time dateTime={s.generatedAt} className="text-ink-2">{fmtDateTimeZone(s.generatedAt)}</time> · view only
        </span>
        <span>
          Sources: {s.sources.map((x) => `${x.name} (${x.rows})`).join(', ')}
          {latest && latest !== '<mtime>' ? `, updated ${fmtDateTime(latest)}` : ''}
        </span>
        <span>
          {s.signOff.status === 'approved' ? (
            <>
              Signed off by <span className="text-ink-2">{s.signOff.approvedBy}</span>, {fmtDateTime(s.signOff.approvedAt)}
            </>
          ) : (
            'Draft, not yet signed off'
          )}
        </span>
        <span>{plural(warnings, 'data-quality warning')}</span>
        <a href={href.definitions()}>How each number is defined</a>
      </div>
    </footer>
  );
}
