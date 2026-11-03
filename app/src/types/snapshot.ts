/* Generated from schema/snapshot.schema.json by npm run gen:types. Do not edit. */

/**
 * One signed-off (or draft) weekly snapshot. The only contract between the pipeline and the app. Version 1.0.
 */
export interface Snapshot {
  schemaVersion: "1.0";
  /**
   * ISO week, e.g. 2026-W41
   */
  weekId: string;
  /**
   * Reporting date; defaults to the Friday of weekId
   */
  asOfDate: string;
  /**
   * Calendar quarter containing asOfDate
   */
  quarter: string;
  generatedAt: string;
  signOff: SignOff;
  /**
   * Domains in display order
   */
  domains: DomainInfo[];
  sources: SourceInfo[];
  registry: RegistryInfo;
  metrics: MetricValue[];
  products: ProductRow[];
  trend: TrendPoint[];
  /**
   * @maxItems 3
   */
  changes: [] | [string] | [string, string] | [string, string, string];
  dataQuality: DataQualityItem[];
  /**
   * Data coverage: how many products have the data each metric needs, per scope. Added 2026-10-07.
   */
  reporting?: ReportingItem[];
  /**
   * Whether each domain, and the organisation, is on track for its quarterly target, per trend quarter. Added 2026-10-08.
   */
  health?: HealthItem[];
  /**
   * Certified so far in the quarter at the end of each week, per trend quarter. Added 2026-10-08.
   */
  weekly?: WeeklyPoint[];
  /**
   * The closed trend quarters, each as it stood on its last day, for the quarter selector. Added 2026-10-08.
   */
  quarters?: QuarterView[];
  delivery?: Delivery;
}
export interface SignOff {
  status: "draft" | "approved";
  approvedBy?: string;
  approvedAt?: string;
}
export interface DomainInfo {
  /**
   * URL-safe id, e.g. market-access
   */
  id: string;
  /**
   * Display name, e.g. Market access
   */
  name: string;
  /**
   * The level above the domain: Commercial, TechOps, R&D, G&A (or Unassigned). Added 2026-10-08.
   */
  area: string;
}
export interface SourceInfo {
  name: string;
  file: string;
  /**
   * ISO date-time the file was last modified, or empty when missing
   */
  asOf: string;
  status: "ok" | "missing";
  rows: number;
}
export interface RegistryInfo {
  metrics: MetricDefinition[];
  flags: FlagDefinition[];
}
export interface MetricDefinition {
  id: string;
  label: string;
  shortLabel: string;
  definition: string;
  levels: ("org" | "domain")[];
  unit: "count" | "days" | "share" | "people";
  compareTo?: "target";
  minN?: number;
  execTile: boolean;
  order: number;
  /**
   * The reporting item that says how complete this metric's inputs are
   */
  coverage?: "gates" | "plans" | "reviewed" | "dpo" | "usage" | "consumers" | "validation" | "nextdata" | "github";
}
export interface FlagDefinition {
  code: string;
  label: string;
  level: "domain" | "product";
  definition: string;
  /**
   * Health signal the flag raises
   */
  signal: "red" | "orange" | "yellow";
}
export interface MetricValue {
  /**
   * Registry id, e.g. certified_qtd
   */
  id: string;
  /**
   * "org" or a domain id
   */
  scope: string;
  value: number | null;
  /**
   * Sample size for medians and shares
   */
  n?: number;
  /**
   * Raw values, present for medians when n < minN
   */
  values?: number[];
  target?: number | null;
  source: "register" | "self-reported" | "snowflake" | "nextdata" | "validation" | "github";
  flag?: "BEHIND" | null;
  /**
   * Why the value is null, or why the flag is raised
   */
  reason?: string;
  /**
   * Products behind the value; the list the number links to
   */
  urns?: string[];
}
export interface ProductRow {
  urn: string;
  name: string;
  /**
   * Domain id
   */
  domain: string;
  dpo?: string;
  stage: "Inception" | "Discovery" | "Design/Develop" | "Test/Launch" | "Operate/Support" | "Retire";
  status: "In design" | "In build" | "In certification" | "Live" | "Live · in revision" | "Retired" | "Cancelled";
  /**
   * Business stage shown on the executive views instead of gate codes. Added 2026-10-08.
   */
  lifecycle: "Ideation" | "In design" | "In development" | "In testing" | "Live" | "Failed / retired";
  /**
   * grey when Retired or Cancelled; else the most severe flag signal; unreported when active with no flags and never reviewed by its DPO; green when active, reviewed and with no flags
   */
  signal: "red" | "orange" | "yellow" | "green" | "grey" | "unreported";
  /**
   * 1 until the first G5; each G5 starts a new iteration
   */
  iteration: number;
  gates: GateRecord[];
  lastGate?: GateRecord;
  firstG4Date?: string;
  daysInStage: number;
  nextGate?: PlannedGate;
  plannedGA?: PlannedGA;
  inputProducts: string[];
  /**
   * Active products that declare this product as an input
   */
  consumedByProducts: string[];
  namedConsumers: number;
  activeUsers30d?: SourcedNumber;
  firstConsumerDate?: SourcedDate;
  validation?: ValidationSummary;
  nextdata?: NextDataSummary;
  /**
   * Domain the product is registered under in NextData, e.g. EDP/OPS
   */
  platformDomain?: string;
  github?: GithubSummary;
  flags: ProductFlag[];
  dpoComment?: string;
  reviewedOn?: string;
  cancelledOn?: string;
}
export interface GateRecord {
  gate: "G1" | "G2" | "G3" | "G4" | "G5" | "G6";
  date: string;
  iteration: number;
  g5Path?: "scope change" | "bug fix";
  evidenceUrl?: string;
}
export interface PlannedGate {
  gate: "G1" | "G2" | "G3" | "G4" | "G5" | "G6";
  plannedDate: string;
  baselineDate: string;
  slips: number;
  /**
   * Days past plannedDate at asOfDate; 0 or negative when not yet due
   */
  overdueDays: number;
}
export interface PlannedGA {
  plannedDate: string;
  baselineDate: string;
  slips: number;
}
export interface SourcedNumber {
  value: number;
  source: "self-reported" | "snowflake";
}
export interface SourcedDate {
  value: string;
  source: "self-reported" | "snowflake";
}
export interface ValidationSummary {
  lastRun: string;
  p1Findings?: number;
  /**
   * Finish-spec completeness, priority-weighted share of applicable checks
   */
  score?: number;
  components?: ComponentScore[];
  /**
   * How the repository declares the owner: Declared, Drift, Unconfirmed, Unresolved, Partial, Suspect, Missing
   */
  ownerStatus?: string;
  /**
   * Validation keyids reported for this product
   */
  keyids?: string[];
}
export interface ComponentScore {
  label: string;
  score: number;
}
export interface NextDataSummary {
  /**
   * NextData names of the product, its key first
   */
  names: string[];
  /**
   * Started if any deployment is Started, else Failed, else Unreachable; Not deployed when there is none
   */
  runtime: string;
  /**
   * Best environment among running deployments
   */
  env?: string;
  /**
   * Link to the product in NextData: the best deployment's base URL
   */
  url?: string;
  /**
   * EDP team layer from the name prefix, e.g. Source systems
   */
  team?: string;
  deployments: NextDataDeployment[];
}
export interface NextDataDeployment {
  name: string;
  env: string;
  version: string;
  state: string;
  /**
   * Base URL of this deployment in NextData
   */
  url?: string;
}
/**
 * The product's GitHub repository and its deployments as of the as-of date. Added 2026-10-30; reached, failingNow, recent and weekly added 2026-11-03.
 */
export interface GithubSummary {
  /**
   * Repository name in the GitHub org
   */
  repo: string;
  /**
   * Link to the repository
   */
  url?: string;
  /**
   * Last successful production deployment
   */
  lastProdDeploy?: string;
  /**
   * Successful production deployments in the last 30 days
   */
  prodDeploys30d: number;
  /**
   * Deployments with an outcome in the last 30 days, every environment
   */
  deploys30d: number;
  /**
   * Of those, deployments that ended in failure or error
   */
  failed30d: number;
  /**
   * Furthest environment of the promotion path with a successful deployment (a Delivery.envs id); absent when none succeeded
   */
  reached?: string;
  /**
   * Path environments whose latest deployment with an outcome failed
   */
  failingNow: string[];
  /**
   * The last 10 deployments up to the as-of date, newest first
   */
  recent: GithubDeploy[];
  /**
   * Deployments per week over the last 12 ISO weeks, oldest first
   */
  weekly: number[];
}
export interface GithubDeploy {
  env: string;
  at: string;
  outcome: "success" | "failure" | "error" | "pending";
}
export interface ProductFlag {
  code: "OVERDUE" | "SLIPPING" | "NO_DPO" | "NOT_UPDATED" | "UNUSED" | "PENDING_URN";
  reason: string;
}
export interface TrendPoint {
  quarter: string;
  /**
   * Domain id
   */
  domain: string;
  certified: number;
  target: number | null;
}
export interface DataQualityItem {
  severity: "blocker" | "warning";
  rule: string;
  message: string;
  urn?: string;
  file?: string;
  /**
   * 1-based data row in the source table (header excluded)
   */
  row?: number;
}
export interface ReportingItem {
  kind: "gates" | "plans" | "reviewed" | "dpo" | "usage" | "consumers" | "validation" | "nextdata" | "github";
  /**
   * "org" or a domain id
   */
  scope: string;
  have: number;
  of: number;
  /**
   * Products without the data; the list the item links to
   */
  missing: string[];
}
export interface HealthItem {
  quarter: string;
  /**
   * "org" or a domain id
   */
  scope: string;
  /**
   * Current quarter, by pace = certified / expected: ahead >= 110%, on-track 90-109%, at-risk (shown as Behind) 70-89%, off-track < 70% (on-track or ahead while expected is 0). Closed quarter: above-target, met-target or below-target. no-target: no target set.
   */
  status: "ahead" | "on-track" | "at-risk" | "off-track" | "above-target" | "met-target" | "below-target" | "no-target";
  certified: number;
  /**
   * target x elapsed, to the nearest whole product (halves up): what should be certified by the as-of date
   */
  expected: number | null;
  /**
   * certified / expected; null while expected is 0
   */
  pace: number | null;
  /**
   * Share of the quarter elapsed at the as-of date (1 for a closed quarter)
   */
  elapsed: number;
  /**
   * Context: on plan to go live by the quarter end (the g4_forecast metric); 0 once the quarter is closed
   */
  forecast: number;
  /**
   * Context: not yet live, go-live due by the quarter end, but not on plan (next gate overdue, or go-live date passed); 0 once the quarter is closed
   */
  late: number;
  target: number | null;
  lateUrns: string[];
}
export interface WeeklyPoint {
  quarter: string;
  week: string;
  /**
   * Last day counted: the Sunday, or the quarter end or as-of date when earlier
   */
  end: string;
  /**
   * Certified in the quarter up to and including end
   */
  certified: number;
  /**
   * The same per domain id; domains with none are left out
   */
  byDomain: {
    [k: string]: number;
  };
}
export interface QuarterView {
  quarter: string;
  /**
   * The quarter's last day
   */
  asOfDate: string;
  metrics: MetricValue[];
  /**
   * Products with a gate passed by the quarter end, from their gate history
   */
  products: QuarterProduct[];
}
export interface QuarterProduct {
  urn: string;
  lifecycle: "Ideation" | "In design" | "In development" | "In testing" | "Live" | "Failed / retired";
  status: "In design" | "In build" | "In certification" | "Live" | "Live · in revision" | "Retired" | "Cancelled";
  lastGate?: GateRecord;
  firstG4Date?: string;
}
/**
 * Every data product repository in the GitHub extract and how it deploys, whether or not it is in the register. Present when the inbox has a GitHub extract. Added 2026-11-02.
 */
export interface Delivery {
  /**
   * When dp fetch-github ran
   */
  fetchedAt: string;
  org?: string;
  /**
   * Length of the trailing window of every *30d value
   */
  windowDays: number;
  /**
   * The promotion path in order, then any other environment
   */
  envs: DeliveryEnv[];
  totals: DeliveryTotals;
  /**
   * The last 12 ISO weeks up to the as-of date, oldest first
   */
  weekly: DeliveryWeek[];
  teams: DeliveryTeam[];
  repos: DeliveryRepo[];
  /**
   * Counted repositories and path environments whose latest deployment failed, longest-failing first. Added 2026-11-03.
   */
  broken: DeliveryBroken[];
  /**
   * Successful production deployments in the window whose commit was never deployed to validation successfully before, newest first. Added 2026-11-03.
   */
  bypass: DeliveryBypass[];
}
export interface DeliveryEnv {
  /**
   * Environment name in GitHub
   */
  id: string;
  label: string;
  prod: boolean;
  /**
   * A step of the promotion path (registry/platform.yaml github.environments)
   */
  path: boolean;
  /**
   * Counted repositories with at least one successful deployment here
   */
  repos: number;
  /**
   * Deployments with an outcome in the window
   */
  deploys30d: number;
  failed30d: number;
}
export interface DeliveryTotals {
  /**
   * Counted repositories
   */
  repos: number;
  /**
   * Of those, with a deployment in the window
   */
  active30d: number;
  deploys30d: number;
  failed30d: number;
  /**
   * Production deployments with an outcome in the window
   */
  prodAttempts30d: number;
  prodFailed30d: number;
  /**
   * Counted repositories with at least one successful production deployment, ever
   */
  reachedProd: number;
  /**
   * Counted repositories that match no register product
   */
  notInRegister: number;
  lastProdDeploy?: string;
  lastProdRepo?: string;
  /**
   * Repository and path-environment pairs whose latest deployment failed
   */
  brokenNow: number;
  /**
   * Repository and path-environment pairs with at least one deployment with an outcome
   */
  pathEnvs: number;
  /**
   * Production commits in the window never deployed to validation successfully before
   */
  bypass30d: number;
  /**
   * Distinct commits deployed to production successfully in the window
   */
  prodCommits30d: number;
  /**
   * Median hours from a failed deployment in the window to the next successful one in the same repository and environment
   */
  recoveryHours30d?: number;
  /**
   * Counted repositories with at least one deployment
   */
  onboarded: number;
}
export interface DeliveryWeek {
  week: string;
  /**
   * Monday of the week
   */
  start: string;
  /**
   * Deployments started in the week, counted repositories, every environment
   */
  deploys: number;
  failed: number;
  prodSuccess: number;
  /**
   * Counted repositories whose first deployment falls in the week
   */
  firstDeploys: number;
}
export interface DeliveryTeam {
  /**
   * Team segment of the repository name (edp-<team>-dp-...)
   */
  team: string;
  label: string;
  repos: number;
  deploys30d: number;
  failed30d: number;
  reachedProd: number;
}
export interface DeliveryRepo {
  name: string;
  url?: string;
  team?: string;
  /**
   * The register product the repository belongs to; absent when it matches none
   */
  urn?: string;
  /**
   * Why the repository is not counted (tooling, template, test, crosswalk)
   */
  excluded?: string;
  /**
   * Environments it has deployed to, in the order of Delivery.envs
   */
  envs: RepoEnv[];
  lastDeploy?: string;
  lastFailure?: string;
  lastProdDeploy?: string;
  /**
   * Successful production deployments, ever
   */
  prodDeploys: number;
  deploys30d: number;
  failed30d: number;
  /**
   * Deployments per week, aligned with Delivery.weekly
   */
  weekly: number[];
  /**
   * Furthest environment of the promotion path with a successful deployment
   */
  reached?: string;
  /**
   * Path environments whose latest deployment with an outcome failed
   */
  failingNow: string[];
}
export interface RepoEnv {
  env: string;
  lastSuccess?: string;
  deploys30d: number;
  failed30d: number;
}
export interface DeliveryBroken {
  repo: string;
  urn?: string;
  env: string;
  /**
   * First failure after the last success
   */
  since: string;
  lastSuccess?: string;
}
export interface DeliveryBypass {
  repo: string;
  urn?: string;
  /**
   * Commit, first 7 characters
   */
  sha: string;
  at: string;
}
