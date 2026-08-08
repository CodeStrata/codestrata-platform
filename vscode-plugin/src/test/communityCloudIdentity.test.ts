/**
 * Tests for Community Cloud shared installation identity (Slice 15.4).
 */

import * as assert from "node:assert";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { describe, it } from "node:test";
import {
  COMMUNITY_CLOUD_IDENTITY_POLICY,
  loadSharedAnonymousInstallationId,
  tryLoadSharedAnonymousInstallationId,
} from "../communityCloud";

describe("Community Cloud installation identity", () => {
  it("reads Engine shared UUID v4 identity and never invents one", () => {
    const home = fs.mkdtempSync(path.join(os.tmpdir(), "cs-id-"));
    const file = path.join(home, "anonymous-installation-identity.json");
    const id = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee";
    fs.writeFileSync(
      file,
      JSON.stringify({
        installation_id: id,
        schema_id: "community-anonymous-installation-identity-schema",
        schema_version: "1.0",
        policy_version: "1.0",
      }),
      "utf8"
    );
    const env = { ...process.env, CODESTRATA_HOME: home };
    const loaded = loadSharedAnonymousInstallationId(env);
    assert.ok(loaded);
    assert.equal(loaded?.installationId, id);
    assert.equal(loaded?.source, "engine_shared_file");
    assert.equal(COMMUNITY_CLOUD_IDENTITY_POLICY.transmissionEnabled, false);
    assert.equal(COMMUNITY_CLOUD_IDENTITY_POLICY.machineIdForbidden, true);
    assert.equal(COMMUNITY_CLOUD_IDENTITY_POLICY.mintSecondIdentityForbidden, true);
  });

  it("returns undefined when identity file is absent", () => {
    const home = fs.mkdtempSync(path.join(os.tmpdir(), "cs-id-missing-"));
    const env = { ...process.env, CODESTRATA_HOME: home };
    assert.equal(tryLoadSharedAnonymousInstallationId(env), undefined);
  });

  it("rejects non-uuid machine-like strings", () => {
    const home = fs.mkdtempSync(path.join(os.tmpdir(), "cs-id-bad-"));
    fs.writeFileSync(
      path.join(home, "anonymous-installation-identity.json"),
      JSON.stringify({ installation_id: "vscode-machine-id-not-allowed" }),
      "utf8"
    );
    const env = { ...process.env, CODESTRATA_HOME: home };
    assert.equal(loadSharedAnonymousInstallationId(env), undefined);
  });
});
