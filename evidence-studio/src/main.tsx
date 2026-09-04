import React, { lazy, Suspense, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import type { RJSFSchema } from "@rjsf/utils";
import "./styles.css";

type Json = Record<string, any>;

const token = new URLSearchParams(window.location.search).get("token") ?? "";
const AdvancedPlanEditor = lazy(() => import("./AdvancedPlanEditor"));

async function api(path: string, options: RequestInit = {}) {
  const separator = path.includes("?") ? "&" : "?";
  const response = await fetch(`${path}${separator}token=${encodeURIComponent(token)}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-CodeStrata-Studio-Token": token,
      ...(options.headers ?? {}),
    },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(payload.error ?? `Request failed: ${response.status}`);
  }
  return response;
}

function App() {
  const [bootstrap, setBootstrap] = useState<Json | null>(null);
  const [plan, setPlan] = useState<Json | null>(null);
  const [preview, setPreview] = useState<Json | null>(null);
  const [step, setStep] = useState(0);
  const [job, setJob] = useState<Json | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [advanced, setAdvanced] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const [patternId, setPatternId] = useState("");
  const [patternRegex, setPatternRegex] = useState("");
  const [patternGlobs, setPatternGlobs] = useState("**/*");
  const [sarifPath, setSarifPath] = useState("");
  const [githubUrl, setGithubUrl] = useState("");
  const [gitRef, setGitRef] = useState("");
  const [acquiring, setAcquiring] = useState(false);
  const [familyFilter, setFamilyFilter] = useState("all");
  const [showAllCollectors, setShowAllCollectors] = useState(false);

  useEffect(() => {
    api("/api/bootstrap")
      .then((response) => response.json())
      .then((data) => {
        setBootstrap(data);
        setPlan(data.plan);
        setPreview(data.preview);
      })
      .catch((reason) => setError(String(reason)));
  }, []);

  useEffect(() => {
    if (!job?.job_id || ["completed", "partial", "failed", "cancelled"].includes(job.status)) {
      return;
    }
    const timer = window.setInterval(async () => {
      try {
        const response = await api(`/api/runs/${job.job_id}`);
        setJob(await response.json());
      } catch (reason) {
        setError(String(reason));
      }
    }, 650);
    return () => window.clearInterval(timer);
  }, [job?.job_id, job?.status]);

  const collectors = useMemo(() => bootstrap?.catalog?.collectors ?? bootstrap?.collectors ?? [], [bootstrap]);
  if (!bootstrap || !plan) {
    return <main className="loading"><p>{error || "Preparing your local evidence workspace…"}</p></main>;
  }

  const activePlan: Json = plan;
  const detectedLanguages: string[] = bootstrap.catalog?.detected_languages ?? [];
  const packRecommendations: Json[] = bootstrap.catalog?.packs ?? [];
  const selectedPacks = new Set<string>(plan.packs ?? []);
  const updatePlan = (patch: Json) => {
    setPlan({ ...plan, ...patch });
    setConfirmed(false);
  };
  const selected = new Set(plan.activities.filter((item: Json) => item.enabled).map((item: Json) => item.collector_id));

  async function refreshPreview() {
    setBusy(true);
    setError("");
    try {
      const response = await api("/api/preview", { method: "POST", body: JSON.stringify(plan) });
      setPreview(await response.json());
      setConfirmed(false);
      setStep(2);
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function acquireGithubRepository() {
    if (!githubUrl.trim()) {
      setError("Enter a public GitHub repository URL.");
      return;
    }
    setAcquiring(true);
    setError("");
    try {
      const response = await api("/api/repositories/github", {
        method: "POST",
        body: JSON.stringify({ url: githubUrl.trim(), ref: gitRef.trim() || null }),
      });
      const data = await response.json();
      setBootstrap(data);
      setPlan(data.plan);
      setPreview(data.preview);
      setJob(null);
      setConfirmed(false);
      setAdvanced(false);
      setPatternId("");
      setPatternRegex("");
      setSarifPath("");
      setStep(0);
    } catch (reason) {
      setError(String(reason));
    } finally {
      setAcquiring(false);
    }
  }

  function toggleCollector(collectorId: string) {
    const existing = activePlan.activities.find(
      (item: Json) => item.collector_id === collectorId,
    );
    const activities = existing
      ? activePlan.activities.map((item: Json) =>
          item.collector_id === collectorId ? { ...item, enabled: !item.enabled } : item,
        )
      : [
          ...activePlan.activities,
          {
            activity_id: collectorId.replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, ""),
            collector_id: collectorId,
            enabled: true,
            configuration: {},
          },
        ];
    updatePlan({ activities });
  }

  async function togglePack(packKey: string) {
    setBusy(true);
    setError("");
    try {
      const nextPacks = selectedPacks.has(packKey)
        ? [...selectedPacks].filter((item) => item !== packKey)
        : [...selectedPacks, packKey];
      const response = await api("/api/plan/packs", {
        method: "POST",
        body: JSON.stringify({ plan, packs: nextPacks }),
      });
      const nextPlan = await response.json();
      if (nextPacks.some((item) => item.startsWith("code-health") || item.startsWith("decision-ready-review"))) {
        nextPlan.assessment_profile = "engineering-health-review@1.0";
      }
      setPlan(nextPlan);
      setConfirmed(false);
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  function updateCollectorSelection(collectorId: string, property: string, option: string, checked: boolean) {
    const manifest = collectors.find((item: Json) => item.collector_id === collectorId);
    const defaults: string[] = manifest?.configuration_schema?.properties?.[property]?.default ?? [];
    const activities = activePlan.activities.map((activity: Json) => {
      if (activity.collector_id !== collectorId) return activity;
      const current: string[] = activity.configuration?.[property] ?? defaults;
      const next = checked
        ? [...new Set([...current, option])]
        : current.filter((item) => item !== option);
      return { ...activity, configuration: { ...activity.configuration, [property]: next } };
    });
    updatePlan({ activities });
  }

  function updateStructuralThreshold(biomarkerId: string, value: string) {
    const parsed = Number.parseInt(value, 10);
    if (!Number.isFinite(parsed) || parsed < 1) return;
    const activities = activePlan.activities.map((activity: Json) => activity.collector_id === "codestrata.structural-health"
      ? { ...activity, configuration: { ...activity.configuration, thresholds: { ...(activity.configuration.thresholds ?? {}), [biomarkerId]: parsed } } }
      : activity);
    updatePlan({ activities });
  }

  function addPatternObservation() {
    const id = patternId.trim();
    const regex = patternRegex.trim();
    if (!id || !regex) {
      setError("Give the observation an ID and regular expression.");
      return;
    }
    const patterns = [{ id, regex, globs: patternGlobs.split(",").map((item) => item.trim()).filter(Boolean) }];
    const existing = activePlan.activities.find((item: Json) => item.collector_id === "codestrata.file-pattern");
    const activities = existing
      ? activePlan.activities.map((item: Json) => item.collector_id === "codestrata.file-pattern"
        ? { ...item, enabled: true, configuration: { ...item.configuration, patterns: [...(item.configuration.patterns ?? []), ...patterns] } }
        : item)
      : [...activePlan.activities, { activity_id: "custom-patterns", collector_id: "codestrata.file-pattern", enabled: true, configuration: { patterns } }];
    updatePlan({ activities });
    setPatternId("");
    setPatternRegex("");
    setError("");
  }

  function removePattern(id: string) {
    const activities = activePlan.activities.flatMap((item: Json) => {
      if (item.collector_id !== "codestrata.file-pattern") return [item];
      const patterns = (item.configuration.patterns ?? []).filter((pattern: Json) => pattern.id !== id);
      return patterns.length ? [{ ...item, configuration: { ...item.configuration, patterns } }] : [];
    });
    updatePlan({ activities });
  }

  function addSarifImport() {
    const path = sarifPath.trim();
    if (!path) {
      setError("Enter a repository-relative SARIF path.");
      return;
    }
    const stem = path.split("/").pop()?.replace(/\.sarif(?:\.json)?$/i, "") || "analysis";
    const importId = `${stem.replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "") || "analysis"}-${activePlan.imports.length + 1}`;
    updatePlan({ imports: [...activePlan.imports, { import_id: importId, format: "sarif-2.1", path }] });
    setSarifPath("");
    setError("");
  }

  async function startRun() {
    setBusy(true);
    setError("");
    try {
      const response = await api("/api/runs", { method: "POST", body: JSON.stringify(plan) });
      setJob(await response.json());
      setStep(3);
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function downloadPlan() {
    const response = await api("/api/plan/yaml", { method: "POST", body: JSON.stringify(plan) });
    const blob = await response.blob();
    const href = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = href;
    anchor.download = "codestrata-evidence-plan.yaml";
    anchor.click();
    URL.revokeObjectURL(href);
  }

  async function loadPlan(file: File) {
    setError("");
    try {
      const response = await api("/api/plan/parse", {
        method: "POST",
        body: await file.text(),
        headers: { "Content-Type": "application/yaml" },
      });
      setPlan(await response.json());
      setConfirmed(false);
      setStep(0);
    } catch (reason) {
      setError(String(reason));
    }
  }

  const families = [...new Set(collectors.map((item: Json) => item.family))].sort();
  const visibleCollectors = collectors
    .filter((item: Json) => familyFilter === "all" || item.family === familyFilter)
    .filter((item: Json) => {
      if (showAllCollectors || selected.has(item.collector_id) || !item.languages?.length) return true;
      return item.languages.some((language: string) => detectedLanguages.includes(language));
    })
    .sort((left: Json, right: Json) => right.recommendation_weight - left.recommendation_weight || left.label.localeCompare(right.label));

  function configurationPanel(item: Json) {
    const activity = activePlan.activities.find((candidate: Json) => candidate.collector_id === item.collector_id);
    if (!activity?.enabled) return null;
    const properties = item.configuration_schema?.properties ?? {};
    const property = properties.biomarkers ? "biomarkers" : properties.capabilities ? "capabilities" : null;
    if (!property) return null;
    const definition = properties[property];
    const options: string[] = definition.items?.enum ?? [];
    const current: string[] = activity.configuration?.[property] ?? definition.default ?? options;
    const thresholdDefaults: Json = {
      large_file: 500,
      large_type: 300,
      long_callable: 60,
      complex_callable: 10,
      deep_nesting: 4,
      parameter_bloat: 7,
    };
    return (
      <details className="collector-config" open>
        <summary>Choose {property}</summary>
        <div className="option-list">
          {options.map((option) => (
            <div className="option-row" key={option}>
              <label>
                <input
                  type="checkbox"
                  checked={current.includes(option)}
                  onChange={(event) => updateCollectorSelection(item.collector_id, property, option, event.target.checked)}
                />
                <span>{option.replaceAll(".", " · ").replaceAll("_", " ")}</span>
              </label>
              {item.collector_id === "codestrata.structural-health" && current.includes(option) && (
                <label className="threshold-field">
                  threshold
                  <input
                    type="number"
                    min="1"
                    value={activity.configuration?.thresholds?.[option] ?? thresholdDefaults[option]}
                    onChange={(event) => updateStructuralThreshold(option, event.target.value)}
                  />
                </label>
              )}
            </div>
          ))}
        </div>
        <small>{current.length} of {options.length} selected. These exact choices and thresholds will appear in the report.</small>
      </details>
    );
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href={`/?token=${token}`} aria-label="CodeStrata Evidence Studio home">
          <span className="brand-mark">CS</span><span>Evidence Studio</span>
        </a>
        <div className="local-pill">On this machine · {bootstrap.repository_source.display_name}</div>
      </header>
      <main>
        <section className="hero">
          <p className="eyebrow">Define → observe → assess → act</p>
          <h1>Ask the repository a better question.</h1>
          <p>Paste a public GitHub repository or use a local folder. Then choose the evidence you trust and inspect every boundary before collection begins.</p>
        </section>

        <nav className="steps" aria-label="Evidence workflow">
          {["Repository & intent", "Evidence", "Review", "Run & report"].map((label, index) => (
            <button key={label} className={step === index ? "active" : ""} onClick={() => setStep(index)}>
              <span>{index + 1}</span>{label}
            </button>
          ))}
        </nav>

        {error && <div className="error" role="alert">{error}</div>}

        {step === 0 && (
          <section className="workspace" aria-labelledby="intent-heading">
            <div className="section-lead"><p className="eyebrow">Start with the subject</p><h2 id="intent-heading">Which repository should CodeStrata observe?</h2><p>Use the folder supplied at launch, or acquire an immutable snapshot from a public GitHub repository.</p></div>
            <section className="repository-card" aria-labelledby="repository-source-heading">
              <div className="repository-current">
                <div><span className="source-kind">{bootstrap.repository_source.kind === "github" ? "GitHub snapshot" : "Local folder"}</span><h3 id="repository-source-heading">{bootstrap.repository_source.display_name}</h3></div>
                <span className="revision">{String(bootstrap.repository_source.revision).slice(0, 12)}</span>
              </div>
              <code>{bootstrap.repository}</code>
              {bootstrap.repository_source.source_url && <p className="source-detail">Acquired from {bootstrap.repository_source.source_url}{bootstrap.repository_source.requested_ref ? ` at ${bootstrap.repository_source.requested_ref}` : " at its default branch"}. {bootstrap.repository_source.cached ? "Reused a verified local snapshot." : "Stored as a new local snapshot."}</p>}
              <div className="language-row" aria-label="Detected repository languages">
                <strong>Detected:</strong>
                {detectedLanguages.length ? detectedLanguages.map((language) => <span className="language-chip" key={language}>{language}</span>) : <span>No supported source language detected yet</span>}
              </div>
            </section>
            <div className="github-acquisition">
              <div><p className="eyebrow">Acquire from GitHub</p><h3>Paste a repository URL</h3><p>CodeStrata makes a shallow, non-interactive clone in its managed local cache. It does not initialize submodules, run hooks, Git LFS, or repository code.</p></div>
              <label className="field">Public GitHub URL<input type="url" inputMode="url" autoComplete="url" placeholder="https://github.com/owner/repository" value={githubUrl} onChange={(event) => setGithubUrl(event.target.value)} /></label>
              <label className="field">Branch or tag <span className="optional">Optional</span><input placeholder="main or v1.2.0" value={gitRef} onChange={(event) => setGitRef(event.target.value)} /></label>
              <div className="button-row compact"><button className="primary" disabled={acquiring || !githubUrl.trim()} onClick={acquireGithubRepository}>{acquiring ? "Cloning safely…" : "Clone and use repository"}</button></div>
              <small>Only credential-free <code>https://github.com/owner/repository</code> URLs are accepted. Selecting a new repository starts a fresh evidence plan.</small>
              {acquiring && <p className="acquisition-status" role="status">Contacting GitHub and creating a bounded local snapshot. Larger repositories may take a moment.</p>}
            </div>
            <div className="section-lead decision-lead"><p className="eyebrow">Then define the decision</p><h2>What are you trying to understand?</h2></div>
            <label className="field">Goal<textarea rows={3} value={plan.goal} onChange={(event) => updatePlan({ goal: event.target.value })} /></label>
            <label className="field">Questions, one per line<textarea rows={5} value={plan.questions.join("\n")} onChange={(event) => updatePlan({ questions: event.target.value.split("\n").filter(Boolean) })} /></label>
            <div className="two-column">
              <label className="field">Audience<input value={plan.audience.join(", ")} onChange={(event) => updatePlan({ audience: event.target.value.split(",").map((item) => item.trim()).filter(Boolean) })} /></label>
              <label className="field">Assessment head<select value={plan.assessment_profile} onChange={(event) => updatePlan({ assessment_profile: event.target.value })}>{bootstrap.profiles.map((profile: Json) => <option key={`${profile.profile_id}@${profile.version}`} value={`${profile.profile_id}@${profile.version}`}>{profile.title} · {profile.version}</option>)}</select><small>Collection choices remain separate from interpretation. The engineering head turns health and imported findings into traceable actions without inventing a universal score.</small></label>
            </div>
            <div className="button-row"><button className="primary" onClick={() => setStep(1)}>Choose evidence</button><label className="file-button">Load YAML<input type="file" accept=".yaml,.yml" onChange={(event) => event.target.files?.[0] && loadPlan(event.target.files[0])} /></label></div>
          </section>
        )}

        {step === 1 && (
          <section className="workspace" aria-labelledby="evidence-heading">
            <div className="section-lead"><p className="eyebrow">Evidence catalog</p><h2 id="evidence-heading">Choose the evidence—not just a generic scan.</h2><p>Start with a goal-shaped pack, then tune individual language capabilities, structural biomarkers, thresholds, scopes, and imported tool output. The report retains the selected pack and records every override.</p></div>
            <div className="detected-strip"><strong>Repository fit</strong><span>{detectedLanguages.length ? detectedLanguages.join(" · ") : "No language match detected"}</span><span>{collectors.length} registered collectors</span></div>
            <div className="pack-grid" aria-label="Evidence packs">
              {packRecommendations.map((recommendation: Json) => {
                const pack = recommendation.pack;
                const packKey = `${pack.pack_id}@${pack.version}`;
                const isSelected = selectedPacks.has(packKey);
                return (
                  <article className={`pack-card ${isSelected ? "selected" : ""}`} key={packKey}>
                    <div className="collector-top"><span className={`pack-status ${recommendation.status}`}>{recommendation.status}</span><span>{pack.families.length} families</span></div>
                    <h3>{pack.title}</h3><p>{pack.description}</p><small>{recommendation.reason}</small>
                    <button className={isSelected ? "secondary" : "primary"} disabled={busy} onClick={() => togglePack(packKey)}>{isSelected ? "Remove pack" : "Use this pack"}</button>
                  </article>
                );
              })}
            </div>
            <div className="catalog-heading"><div><p className="eyebrow">Fine-grained control</p><h3>Collector catalog</h3></div><div className="catalog-controls"><label>Evidence family<select value={familyFilter} onChange={(event) => setFamilyFilter(event.target.value)}><option value="all">All families</option>{families.map((family) => <option value={family} key={family}>{family.replace("_", " ")}</option>)}</select></label><label className="show-all"><input type="checkbox" checked={showAllCollectors} onChange={(event) => setShowAllCollectors(event.target.checked)} /> Show collectors unrelated to detected languages</label></div></div>
            <div className="collector-grid">
              {visibleCollectors.map((item: Json) => {
                const status = bootstrap.collector_status?.[item.collector_id];
                return (
                  <article className={`collector-card ${selected.has(item.collector_id) ? "selected" : ""}`} key={item.collector_id}>
                    <div className="collector-top"><span className="family">{item.family.replace("_", " ")}</span><span className={`availability ${status?.available ? "available" : "unavailable"}`}>{status?.available ? item.maturity : "not installed"}</span></div>
                    <h3>{item.label}</h3><p>{item.description}</p>
                    {!!item.languages?.length && <div className="language-row compact">{item.languages.map((language: string) => <span className="language-chip" key={language}>{language}</span>)}</div>}
                    <ul className="facts"><li>{item.external_access === "none" ? "No network" : "May use network"}</li><li>{item.runs_code ? "Executes a local tool" : "Read-only observation"}</li><li>{item.capability_ids.length} selectable capabilities</li></ul>
                    {!status?.available && <p className="availability-note">{status?.reason}</p>}
                    <button className={selected.has(item.collector_id) ? "secondary" : "primary"} onClick={() => item.collector_id === "codestrata.file-pattern" ? document.getElementById("pattern-builder")?.scrollIntoView({ behavior: "smooth" }) : toggleCollector(item.collector_id)}>{item.collector_id === "codestrata.file-pattern" ? (selected.has(item.collector_id) ? "Configured below" : "Configure below") : (selected.has(item.collector_id) ? "Remove from plan" : "Add to plan")}</button>
                    {configurationPanel(item)}
                  </article>
                );
              })}
            </div>
            <div className="builder-grid">
              <section className="builder" id="pattern-builder" aria-labelledby="pattern-heading"><p className="eyebrow">Custom observation</p><h3 id="pattern-heading">Find repository signals</h3><p>Record counts and locations for a bounded pattern. Matching source text is not stored.</p><label className="field">Observation ID<input placeholder="deprecated-api" value={patternId} onChange={(event) => setPatternId(event.target.value)} /></label><label className="field">Regular expression<input placeholder="\\boldFunction\\s*\\(" value={patternRegex} onChange={(event) => setPatternRegex(event.target.value)} /></label><label className="field">File globs, comma separated<input placeholder="**/*.js, **/*.ts" value={patternGlobs} onChange={(event) => setPatternGlobs(event.target.value)} /></label><button className="primary" onClick={addPatternObservation}>Add observation</button>{activePlan.activities.filter((item: Json) => item.collector_id === "codestrata.file-pattern").flatMap((item: Json) => item.configuration.patterns ?? []).map((pattern: Json) => <div className="configured-row" key={pattern.id}><code>{pattern.id}</code><span>{pattern.globs.join(", ")}</span><button aria-label={`Remove ${pattern.id}`} onClick={() => removePattern(pattern.id)}>Remove</button></div>)}</section>
              <section className="builder" aria-labelledby="sarif-heading"><p className="eyebrow">Existing tool output</p><h3 id="sarif-heading">Import SARIF 2.1</h3><p>Normalize results from pre-commit tools, MegaLinter, Super-Linter, Trivy, CodeQL, or another SARIF producer. The path must stay inside the repository.</p><label className="field">Repository-relative path<input placeholder="artifacts/results.sarif" value={sarifPath} onChange={(event) => setSarifPath(event.target.value)} /></label><button className="primary" onClick={addSarifImport}>Add SARIF import</button>{plan.imports.map((item: Json) => <div className="configured-row" key={item.import_id}><code>{item.import_id}</code><span>{item.path}</span><button aria-label={`Remove ${item.import_id}`} onClick={() => updatePlan({ imports: plan.imports.filter((candidate: Json) => candidate.import_id !== item.import_id) })}>Remove</button></div>)}</section>
            </div>
            <details className="advanced" open={advanced} onToggle={(event) => setAdvanced((event.target as HTMLDetailsElement).open)}>
              <summary>Advanced plan editor</summary>
              <p>This form is generated from the same JSON Schema enforced by the local engine.</p>
              {advanced && <Suspense fallback={<p>Loading schema editor…</p>}><AdvancedPlanEditor schema={bootstrap.plan_schema as RJSFSchema} plan={plan} onChange={(next) => { setPlan(next); setConfirmed(false); }} /></Suspense>}
            </details>
            <div className="button-row"><button className="primary" disabled={busy} onClick={refreshPreview}>{busy ? "Validating…" : "Preview the plan"}</button><button className="secondary" onClick={downloadPlan}>Download YAML</button></div>
          </section>
        )}

        {step === 2 && preview && (
          <section className="workspace" aria-labelledby="review-heading">
            <div className="section-lead"><p className="eyebrow">Review before execution</p><h2 id="review-heading">Know exactly what will happen.</h2></div>
            <div className="review-grid">
              <div className="review-card"><h3>Reads</h3><ul>{preview.reads.map((item: string) => <li key={item}>{item}</li>)}</ul></div>
              <div className="review-card"><h3>Executes</h3><ul>{preview.executes.length ? preview.executes.map((item: string) => <li key={item}>{item}</li>) : <li>Nothing</li>}</ul></div>
              <div className="review-card"><h3>Leaves this machine</h3><ul>{preview.leaves_machine.map((item: string) => <li key={item}>{item}</li>)}</ul></div>
            </div>
            <div className="table-wrap"><table><thead><tr><th>Activity</th><th>Status</th><th>Why</th><th>Produces</th></tr></thead><tbody>{preview.collectors.map((item: Json) => <tr key={item.activity_id}><td>{item.manifest.label}</td><td><span className={`status ${item.status}`}>{item.status}</span></td><td>{item.reason}</td><td>{item.manifest.output_kinds.join(", ")}</td></tr>)}</tbody></table></div>
            <details className="blind-spots"><summary>Known blind spots ({preview.blind_spots.length})</summary><ul>{preview.blind_spots.map((item: string) => <li key={item}>{item}</li>)}</ul></details>
            <label className="confirmation"><input type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} /> I reviewed what will be read, executed, and sent off-machine.</label>
            <div className="button-row"><button className="primary" disabled={busy || !confirmed} onClick={startRun}>{busy ? "Starting…" : "Run evidence plan"}</button><button className="secondary" onClick={() => setStep(1)}>Edit evidence</button></div>
          </section>
        )}

        {step === 3 && (
          <section className="workspace" aria-labelledby="run-heading">
            <div className="section-lead"><p className="eyebrow">Observable execution</p><h2 id="run-heading">{job ? `Run ${job.status}` : "No run started yet"}</h2></div>
            <div className="run-status" aria-live="polite" aria-atomic="false">
              {job?.events?.map((event: Json) => <div className="event" key={event.sequence}><span className={`dot ${event.status}`} /><div><strong>{event.activity_id}</strong><br />{event.message}</div><time>{new Date(event.occurred_at).toLocaleTimeString()}</time></div>)}
            </div>
            {job && !["completed", "partial", "failed", "cancelled"].includes(job.status) && <button className="danger" onClick={() => api(`/api/runs/${job.job_id}/cancel`, { method: "POST", body: "{}" })}>Cancel safely</button>}
            {job?.result && <div className="result-card"><p className="eyebrow">Assessment ready</p><h3>{job.result.assessment.findings.length} findings · {job.result.assessment.actions.length} actions</h3><p>{job.result.evidence_count} normalized evidence records are stored at <code>{job.result.output_directory}</code>.</p><a className="primary link-button" target="_blank" rel="noreferrer" href={`/api/runs/${job.job_id}/report?token=${encodeURIComponent(token)}`}>Open decision report</a></div>}
          </section>
        )}
      </main>
      <footer>CodeStrata Evidence Studio · Collected evidence stays local. GitHub acquisition and reviewed external activities are the only network paths.</footer>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);
