
  # Add marketplace (once)
  claude plugin marketplace add https://sliples.agantis.in/api/v1/claude-marketplace.json

  # Install plugin
  claude plugin install sliples-recorder@sliples

  Then in any Claude Code session: "analyse sliples" or "/sliples" → Claude authenticates via browser, lists sessions, fetches events, analyses.