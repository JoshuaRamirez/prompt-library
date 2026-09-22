/**
 * The demo's library: seven rows of the kind a real prompts.csv holds. Only the columns search
 * reads are here; the plugin also stores model, source, version and timestamps.
 */
export interface SamplePrompt {
  id: string;
  title: string;
  prompt: string;
  tags: readonly string[];
  category: string;
  notes: string;
}

export const samplePrompts: readonly SamplePrompt[] = [
  {
    id: 'code-review-checklist',
    title: 'Code review checklist',
    prompt: 'Review the {{language}} change in {{file}}. Check error handling, naming and tests. List problems by severity, then say what you would merge as it is.',
    tags: ['review', 'code'],
    category: 'engineering',
    notes: 'Works best on one file at a time.',
  },
  {
    id: 'commit-message',
    title: 'Commit message from a diff',
    prompt: 'Write a commit message for the staged diff in the {{style}} format. Keep the subject under {{max_length}} characters and say why in the body.',
    tags: ['git', 'commit'],
    category: 'engineering',
    notes: '',
  },
  {
    id: 'explain-for-newcomer',
    title: 'Explain code to a newcomer',
    prompt: 'Explain what {{file}} does to someone who joined the team this week. Start with its job, then walk through it in reading order.',
    tags: ['explain', 'onboarding'],
    category: 'teaching',
    notes: '',
  },
  {
    id: 'bug-report-triage',
    title: 'Triage a bug report',
    prompt: 'Read this bug report and say whether it reproduces, which component is at fault and how severe it is: {{report}}',
    tags: ['bugs', 'triage'],
    category: 'support',
    notes: 'Paste the report as it came in, logs included.',
  },
  {
    id: 'release-notes',
    title: 'Release notes from commits',
    prompt: 'Turn the commits since {{last_tag}} into release notes for {{audience}}. Group them into added, changed and fixed.',
    tags: ['release', 'changelog', 'git'],
    category: 'writing',
    notes: '',
  },
  {
    id: 'test-plan',
    title: 'Test plan for a change',
    prompt: 'Write a test plan for {{feature}}: the cases that must pass, the edge cases, and what you would not test and why.',
    tags: ['testing', 'review'],
    category: 'engineering',
    notes: '',
  },
  {
    id: 'sql-query-review',
    title: 'SQL query review',
    prompt: 'Review this {{dialect}} query for correctness and speed. Suggest an index only if it pays for itself: {{query}}',
    tags: ['sql', 'review', 'performance'],
    category: 'database',
    notes: '',
  },
];
