// Checks that contract/vault-schema.json is the personal vault's current
// schema: schema.json at the root of this repository, which a vault test keeps
// equal to `pvault schema --json`. Without it a vault schema change (a new
// field, a new credential word) would go unnoticed here.
// Usage: npm run check:vault-schema [-- <path to another schema.json>]
// Without a path it reads ../schema.json (the repository root). `make schema`
// writes both files.

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { VAULT_SCHEMA_PATH, type VaultSchema } from "./gen-fields.ts";
import { schemaDifferences } from "./lib/vault-schema.ts";

const ROOT_SCHEMA = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "..", "schema.json");

try {
  const current = JSON.parse(readFileSync(process.argv[2] ?? ROOT_SCHEMA, "utf8")) as VaultSchema;
  const saved = JSON.parse(readFileSync(VAULT_SCHEMA_PATH, "utf8")) as VaultSchema;
  const differences = schemaDifferences(saved, current);
  if (differences.length === 0) {
    console.log(`contract/vault-schema.json is the vault's current schema (version ${current.version})`);
  } else {
    console.error(`contract/vault-schema.json is behind the vault's schema.json:\n${differences.map((d) => `  - ${d}`).join("\n")}`);
    console.error("Run make schema (it writes schema.json and runs npm run gen:fields -- ../schema.json in library/), then check the procedures still validate.");
    process.exitCode = 1;
  }
} catch (e) {
  console.error(`can't compare with the vault's schema: ${(e as Error).message}`);
  process.exitCode = 2;
}
