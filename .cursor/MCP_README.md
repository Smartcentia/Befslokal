# MCP-servere (Cursor)

## GitHub MCP

For at Cursor-agenten skal kunne pushe til GitHub (f.eks. `git push`) via MCP:

1. **Opprett en Personal Access Token (PAT)** på GitHub:
   - GitHub → Settings → Developer settings → Personal access tokens → Classic
   - "Generate new token (classic)", velg minst **repo**-scope
   - Kopier tokenet (vises bare én gang)

2. **Sett token i** `.cursor/mcp.json`:
   - Erstatt `LEGG_INN_DIN_GITHUB_PAT_HER` i `mcpServers.github.env.GITHUB_PERSONAL_ACCESS_TOKEN` med din PAT.

3. **Docker må være installert og kjøre** – GitHub MCP kjører som container.

4. **Start Cursor på nytt** (eller last MCP på nytt) slik at GitHub-serveren kobles til.

Da kan agenten bruke GitHub-verktøy (push, create PR, issues, osv.) når du ber om det.
