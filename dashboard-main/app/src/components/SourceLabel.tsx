/* Self-reported values are always labelled (plan section 11). */

const LABELS: Record<string, string> = {
  'self-reported': 'Self-reported',
  snowflake: 'Snowflake',
  nextdata: 'NextData',
  validation: 'Validation tool',
};

const TITLES: Record<string, string> = {
  'self-reported': 'Typed by the DPO in the register; replaced by Snowflake usage in Release 2',
  snowflake: 'Snowflake access history',
  nextdata: 'NextData platform export',
  validation: 'Repo validation tool: static completeness of the product specification',
};

export default function SourceLabel({ source, className = '' }: { source: string; className?: string }) {
  if (source === 'register') return null;
  return (
    <span className={`inline-flex h-5 items-center rounded-md border border-line-strong px-1.5 text-small text-ink-3 ${className}`} title={TITLES[source]}>
      {LABELS[source] ?? source}
    </span>
  );
}
