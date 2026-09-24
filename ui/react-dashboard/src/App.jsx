import { useEffect, useMemo, useState } from "react";

const API_BASE_URL = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
const WORKFLOW_STEPS = [
  { number: "01", label: "Connect" },
  { number: "02", label: "Discover" },
  { number: "03", label: "Select" },
  { number: "04", label: "Assess" },
  { number: "05", label: "Migrate" }
];
const SOURCE_CONNECTORS = [
  {
    value: "postgresql",
    label: "PostgreSQL",
    hint: "Live",
    description: "Transactional schema discovery and migration source."
  },
  {
    value: "sqlite",
    label: "SQLite",
    hint: "Preview",
    description: "File-based source connector for lightweight relational apps."
  },
  {
    value: "mysql",
    label: "MySQL",
    hint: "Preview",
    description: "Showcase connector option for MySQL estates."
  },
  {
    value: "mariadb",
    label: "MariaDB",
    hint: "Preview",
    description: "Open-source relational source connector option."
  },
  {
    value: "db2",
    label: "IBM Db2",
    hint: "Preview",
    description: "Enterprise relational source option for Db2 estates."
  },
  {
    value: "sqlserver",
    label: "SQL Server",
    hint: "Preview",
    description: "Enterprise source connector option for SQL Server."
  },
  {
    value: "oracle",
    label: "Oracle",
    hint: "Preview",
    description: "Legacy source system option for Oracle workloads."
  },
  {
    value: "redshift",
    label: "Amazon Redshift",
    hint: "Preview",
    description: "Cloud warehouse source connector for analytical workloads."
  },
  {
    value: "snowflake",
    label: "Snowflake",
    hint: "Preview",
    description: "Warehouse source option for analytical migrations."
  },
  {
    value: "bigquery",
    label: "BigQuery",
    hint: "Preview",
    description: "Cloud analytics source connector for large datasets."
  },
  {
    value: "sap-hana",
    label: "SAP HANA",
    hint: "Preview",
    description: "In-memory enterprise source option for SAP landscapes."
  },
  {
    value: "cockroachdb",
    label: "CockroachDB",
    hint: "Preview",
    description: "Distributed SQL source connector for resilient workloads."
  }
];
const TARGET_CONNECTORS = [
  {
    value: "mongodb",
    label: "MongoDB",
    hint: "Live",
    description: "Primary document database migration target."
  },
  {
    value: "cosmos-nosql",
    label: "Azure Cosmos DB for NoSQL",
    hint: "Preview",
    description: "Cloud-native document destination on Azure."
  },
  {
    value: "cosmos-mongo",
    label: "Azure Cosmos DB",
    hint: "Preview",
    description: "Mongo-compatible cloud destination option."
  },
  {
    value: "firestore",
    label: "Firestore",
    hint: "Preview",
    description: "Serverless document target for Firebase and GCP apps."
  },
  {
    value: "documentdb",
    label: "Amazon DocumentDB",
    hint: "Preview",
    description: "Managed Mongo-compatible target connector."
  },
  {
    value: "opensearch",
    label: "OpenSearch",
    hint: "Preview",
    description: "Search-oriented target for denormalized document indexing."
  },
  {
    value: "dynamodb",
    label: "DynamoDB",
    hint: "Preview",
    description: "Key-value and document target for cloud-native apps."
  },
  {
    value: "scylladb",
    label: "ScyllaDB",
    hint: "Preview",
    description: "Low-latency wide-column target compatible with Cassandra APIs."
  },
  {
    value: "cassandra",
    label: "Cassandra",
    hint: "Preview",
    description: "High-throughput distributed target for wide-column workloads."
  },
  {
    value: "couchbase",
    label: "Couchbase",
    hint: "Preview",
    description: "Document target connector for hybrid operational workloads."
  },
  {
    value: "redis",
    label: "Redis",
    hint: "Preview",
    description: "Low-latency target option for cache-centric access patterns."
  },
  {
    value: "neo4j",
    label: "Neo4j",
    hint: "Preview",
    description: "Graph database destination for relationship-heavy workloads."
  }
];

const emptyAssessment = null;
const emptyMigration = null;

const createSourceForm = () => ({
  host: "",
  port: "",
  database: "",
  user: "",
  password: "",
  schema: ""
});

const createTargetForm = () => ({
  uri: "",
  host: "",
  port: "",
  database: "",
  user: "",
  password: ""
});

const createInitialState = () => ({
  sourceConnector: "",
  targetConnector: "",
  source: createSourceForm(),
  target: createTargetForm(),
  connectionResult: null,
  schemaData: null,
  selectedTables: [],
  assessment: emptyAssessment,
  migrationResult: emptyMigration,
  executionLogs: []
});

async function postJson(path, payload) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || `Request failed with status ${response.status}`);
  }
  return data;
}

function ConnectorField({ label, value, onChange, type = "text", placeholder }) {
  return (
    <label className="field">
      <span>{label}</span>
      <input type={type} value={value} placeholder={placeholder} onChange={onChange} />
    </label>
  );
}

function ConnectorSelectField({ label, value, options, onChange, placeholder }) {
  const [open, setOpen] = useState(false);
  const selectedOption = options.find((option) => option.value === value) || null;

  useEffect(() => {
    if (!open) {
      return undefined;
    }

    const handlePointerDown = (event) => {
      if (!event.target.closest(".connector-select")) {
        setOpen(false);
      }
    };

    const handleEscape = (event) => {
      if (event.key === "Escape") {
        setOpen(false);
      }
    };

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleEscape);

    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [open]);

  return (
    <label className="field">
      <span>{label}</span>
      <div className={`connector-select ${open ? "connector-select--open" : ""}`}>
        <button
          type="button"
          className={`connector-select__trigger ${selectedOption ? "" : "connector-select__trigger--placeholder"}`}
          onClick={() => setOpen((current) => !current)}
          aria-haspopup="listbox"
          aria-expanded={open}
        >
          <span>{selectedOption?.label || placeholder}</span>
          <span className="connector-select__chevron" aria-hidden="true">
            ▾
          </span>
        </button>

        {open ? (
          <div className="connector-select__menu" role="listbox" aria-label={label}>
            {options.map((option) => {
              const isSelected = option.value === value;
              return (
                <button
                  key={option.value}
                  type="button"
                  className={`connector-select__option ${isSelected ? "connector-select__option--selected" : ""}`}
                  onClick={() => {
                    onChange({ target: { value: option.value } });
                    setOpen(false);
                  }}
                  role="option"
                  aria-selected={isSelected}
                >
                  <span className="connector-select__option-main">
                    <strong>{option.label}</strong>
                    <small>{option.description}</small>
                  </span>
                  <span className="status-chip status-chip--info">{option.hint}</span>
                </button>
              );
            })}
          </div>
        ) : null}
      </div>
    </label>
  );
}

function App() {
  const initialState = useMemo(() => createInitialState(), []);
  const [sourceConnector, setSourceConnector] = useState(initialState.sourceConnector);
  const [targetConnector, setTargetConnector] = useState(initialState.targetConnector);
  const [source, setSource] = useState(initialState.source);
  const [target, setTarget] = useState(initialState.target);
  const [connectionResult, setConnectionResult] = useState(initialState.connectionResult);
  const [schemaData, setSchemaData] = useState(initialState.schemaData);
  const [selectedTables, setSelectedTables] = useState(initialState.selectedTables);
  const [assessment, setAssessment] = useState(initialState.assessment);
  const [migrationResult, setMigrationResult] = useState(initialState.migrationResult);
  const [executionLogs, setExecutionLogs] = useState(initialState.executionLogs);
  const [busyAction, setBusyAction] = useState("");
  const [error, setError] = useState("");

  const discoveredTables = schemaData?.tables || [];
  const selectedCount = selectedTables.length;
  const activeSourceConnector =
    SOURCE_CONNECTORS.find((option) => option.value === sourceConnector) || null;
  const activeTargetConnector =
    TARGET_CONNECTORS.find((option) => option.value === targetConnector) || null;

  const summaryMetrics = useMemo(() => {
    if (!assessment) {
      return [
        { label: "Tables selected", value: selectedCount, detail: "Choose tables after discovery" },
        { label: "Dependencies", value: 0, detail: "Calculated during assessment" },
        { label: "Risk level", value: "Waiting", detail: "Run assessment to see posture" },
        { label: "Validation", value: "Pending", detail: "Run migration to validate output" }
      ];
    }

    return [
      {
        label: "Tables selected",
        value: Object.keys(assessment.tables || {}).length,
        detail: "Included in this migration run"
      },
      {
        label: "Dependencies",
        value: assessment.dependency_metrics?.total_dependencies || 0,
        detail: "Foreign key edges across selected tables"
      },
      {
        label: "Risk level",
        value: assessment.risk_assessment?.risk_level || "Unknown",
        detail: `Score ${assessment.risk_assessment?.risk_score ?? "n/a"}`
      },
      {
        label: "Validation",
        value: migrationResult?.validation?.overall_success ? "Passed" : "Pending",
        detail: migrationResult?.validation?.overall_success
          ? "Post-migration checks succeeded"
          : "Run migration to validate output"
      }
    ];
  }, [assessment, migrationResult, selectedCount]);

  const toggleTable = (tableName) => {
    setSelectedTables((current) =>
      current.includes(tableName)
        ? current.filter((name) => name !== tableName)
        : [...current, tableName]
    );
  };

  const updateSource = (field) => (event) => {
    setSource((current) => ({ ...current, [field]: event.target.value }));
  };

  const updateTarget = (field) => (event) => {
    setTarget((current) => ({ ...current, [field]: event.target.value }));
  };

  const withAction = async (label, work) => {
    setBusyAction(label);
    setError("");
    try {
      await work();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyAction("");
    }
  };

  const handleTestConnections = () =>
    withAction("testing connections", async () => {
      const result = await postJson("/api/connectors/test", { source, target });
      setConnectionResult(result);
    });

  const handleTestSource = () =>
    withAction("testing source connection", async () => {
      const result = await postJson("/api/connectors/test", { source });
      if (!source.schema && result.source?.schema) {
        setSource((current) => ({ ...current, schema: result.source.schema }));
      }
      setConnectionResult((current) => ({
        ...current,
        source: result.source
      }));
    });

  const handleTestTarget = () =>
    withAction("testing target connection", async () => {
      const result = await postJson("/api/connectors/test", { target });
      setConnectionResult((current) => ({
        ...current,
        target: result.target
      }));
    });

  const handleDiscoverTables = () =>
    withAction("discovering schema", async () => {
      const result = await postJson("/api/schema/discover", { source });
      if (result.schema && result.schema !== source.schema) {
        setSource((current) => ({ ...current, schema: result.schema }));
      }
      setSchemaData(result);
      setSelectedTables(result.tables.map((table) => table.name));
      setAssessment(emptyAssessment);
      setMigrationResult(emptyMigration);
    });

  const handleRunAssessment = () =>
    withAction("running assessment", async () => {
      if (!selectedTables.length) {
        throw new Error("Select at least one table before running assessment.");
      }
      const result = await postJson("/api/assessment/run", { source, selectedTables });
      setAssessment(result);
    });

  const handleRunMigration = () =>
    withAction("running migration", async () => {
      if (!selectedTables.length) {
        throw new Error("Select at least one table before starting migration.");
      }
      setExecutionLogs([
        {
          table: "Pipeline",
          status: "running",
          message: `Migration started for ${selectedTables.length} selected tables.`
        }
      ]);

      try {
        const result = await postJson("/api/migration/run", {
          source,
          target,
          selectedTables
        });
        setAssessment(result.readiness);
        setMigrationResult(result);
        setExecutionLogs([
          {
            table: "Pipeline",
            status: "completed",
            message: "Migration request finished successfully."
          },
          ...(result.logs || [])
        ]);
      } catch (err) {
        setExecutionLogs((current) => [
          ...current,
          {
            table: "Pipeline",
            status: "failed",
            message: err.message
          }
        ]);
        throw err;
      }
    });

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <span className="eyebrow">Live migration app</span>
          <h1>Connect your own databases and run the migration from the UI.</h1>
        </div>
      </aside>

      <main className="content">
        <section className="hero-panel">
          <div className="hero-copy">
            <span className="eyebrow">Workflow</span>
            <h2>Migration runway</h2>
            <p>
              Connect your databases, discover schema, assess readiness, and launch migration from
              one clean control surface.
            </p>
          </div>

          <div className="hero-board">
            <div className="hero-actions">
              <button type="button" className="action-button" onClick={handleTestSource} disabled={!!busyAction}>
                Test source
              </button>
              <button type="button" className="action-button" onClick={handleTestTarget} disabled={!!busyAction}>
                Test target
              </button>
              <button type="button" className="action-button" onClick={handleDiscoverTables} disabled={!!busyAction}>
                Discover tables
              </button>
              <button type="button" className="action-button" onClick={handleRunAssessment} disabled={!!busyAction}>
                Run assessment
              </button>
              <button type="button" className="action-button action-button--primary hero-actions__wide" onClick={handleRunMigration} disabled={!!busyAction}>
                Start migration
              </button>
            </div>
          </div>

          <div className="hero-footer">
            <div className="workflow-line" aria-label="Migration workflow">
              {WORKFLOW_STEPS.map((step) => (
                <span key={step.label} className="workflow-line__group">
                  <span className="workflow-line__step">
                    <span className="workflow-line__index">{step.number}</span>
                    <span className="workflow-line__label">{step.label}</span>
                  </span>
                </span>
              ))}
            </div>
          </div>
        </section>

        {busyAction ? (
          <section className="notice notice--info">Currently {busyAction}.</section>
        ) : null}
        {error ? <section className="notice notice--error">{error}</section> : null}

        <section className="metric-grid">
          {summaryMetrics.map((metric) => (
            <article key={metric.label} className="metric-card">
              <span>{metric.label}</span>
              <strong>{metric.value}</strong>
              <small>{metric.detail}</small>
            </article>
          ))}
        </section>

        <section className="workspace-grid">
          <div className="workspace-grid__primary">
            <section className="panel">
              <div className="panel__header">
                <div>
                  <span className="eyebrow">Connectors</span>
                  <h3>Source and target connector configuration</h3>
                </div>
              </div>

              <div className="connector-layout">
                <article className="connector-card">
                  <div className="connector-card__top">
                    <div>
                      <span className="eyebrow">Source</span>
                      <h4>{activeSourceConnector?.label || "Select Source DB"}</h4>
                    </div>
                    <span className={connectionResult?.source?.ok ? "status-chip status-chip--healthy" : "status-chip status-chip--info"}>
                      {connectionResult?.source?.ok ? "Connected" : "Not tested"}
                    </span>
                  </div>
                  <div className="connector-select-row">
                    <ConnectorSelectField
                      label="Select source connector"
                      value={sourceConnector}
                      options={SOURCE_CONNECTORS}
                      placeholder="Select Source DB"
                      onChange={(event) => setSourceConnector(event.target.value)}
                    />
                    <span className="status-chip status-chip--info">
                      {activeSourceConnector?.hint || "Required"}
                    </span>
                  </div>
                  <div className="field-grid">
                    <ConnectorField label="Host" value={source.host} onChange={updateSource("host")} />
                    <ConnectorField label="Port" value={source.port} placeholder="5432" onChange={updateSource("port")} />
                    <ConnectorField label="Database" value={source.database} onChange={updateSource("database")} />
                    <ConnectorField
                      label="Schema"
                      value={source.schema}
                      placeholder="Leave blank to use current schema"
                      onChange={updateSource("schema")}
                    />
                    <ConnectorField label="User" value={source.user} onChange={updateSource("user")} />
                    <ConnectorField label="Password" type="password" value={source.password} onChange={updateSource("password")} />
                  </div>
                </article>

                <article className="connector-card">
                  <div className="connector-card__top">
                    <div>
                      <span className="eyebrow">Target</span>
                      <h4>{activeTargetConnector?.label || "Select Target DB"}</h4>
                    </div>
                    <span className={connectionResult?.target?.ok ? "status-chip status-chip--healthy" : "status-chip status-chip--info"}>
                      {connectionResult?.target?.ok ? "Connected" : "Not tested"}
                    </span>
                  </div>
                  <div className="connector-select-row">
                    <ConnectorSelectField
                      label="Select target connector"
                      value={targetConnector}
                      options={TARGET_CONNECTORS}
                      placeholder="Select Target DB"
                      onChange={(event) => setTargetConnector(event.target.value)}
                    />
                    <span className="status-chip status-chip--info">
                      {activeTargetConnector?.hint || "Required"}
                    </span>
                  </div>
                  <div className="field-grid">
                    <ConnectorField
                      label="Mongo URI"
                      value={target.uri}
                      onChange={updateTarget("uri")}
                      placeholder="mongodb://localhost:27017/"
                    />
                    <ConnectorField label="Database" value={target.database} onChange={updateTarget("database")} />
                    <ConnectorField label="Host" value={target.host} placeholder="localhost" onChange={updateTarget("host")} />
                    <ConnectorField label="Port" value={target.port} placeholder="27017" onChange={updateTarget("port")} />
                    <ConnectorField label="User" value={target.user} onChange={updateTarget("user")} />
                    <ConnectorField label="Password" type="password" value={target.password} onChange={updateTarget("password")} />
                  </div>
                </article>
              </div>
            </section>

            <section className="panel">
              <div className="panel__header">
                <div>
                  <span className="eyebrow">Discovery</span>
                  <h3>Choose the tables you want to migrate</h3>
                </div>
                <div className="inline-actions">
                  <span className="status-chip status-chip--info">{selectedCount} selected</span>
                  <button type="button" className="ghost-button" onClick={() => setSelectedTables(discoveredTables.map((table) => table.name))}>
                    Select all
                  </button>
                  <button type="button" className="ghost-button" onClick={() => setSelectedTables([])}>
                    Clear
                  </button>
                </div>
              </div>

              {discoveredTables.length ? (
                <div className="table-selector-wrap">
                  <div className="table-selector">
                    {discoveredTables.map((table) => (
                      <label key={table.name} className={selectedTables.includes(table.name) ? "table-card active" : "table-card"}>
                        <div className="table-card__header">
                          <input
                            type="checkbox"
                            checked={selectedTables.includes(table.name)}
                            onChange={() => toggleTable(table.name)}
                          />
                          <div>
                            <strong>{table.name}</strong>
                            <small>{table.columns.length} columns</small>
                          </div>
                          <span className="status-chip status-chip--info">{table.rowCount} rows</span>
                        </div>
                        <p>
                          Dependencies: {table.dependencies.length ? table.dependencies.join(", ") : "None"}
                        </p>
                      </label>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="empty-state">
                  Run schema discovery after entering your source connector details.
                </div>
              )}
            </section>

            <section className="panel">
              <div className="panel__header">
                <div>
                  <span className="eyebrow">Assessment</span>
                  <h3>Readiness report for your selected tables</h3>
                </div>
              </div>

              {assessment ? (
                <div className="assessment-wrap">
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Table</th>
                          <th>Rows</th>
                          <th>Columns</th>
                          <th>Checksum</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(assessment.tables || {}).map(([name, meta]) => (
                          <tr key={name}>
                            <td>{name}</td>
                            <td>{meta.row_count}</td>
                            <td>{meta.columns?.length || 0}</td>
                            <td className="mono">{meta.checksum}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <div className="empty-state">
                  Run assessment to generate readiness metrics from the selected tables.
                </div>
              )}
            </section>

            <section className="panel">
              <div className="panel__header">
                <div>
                  <span className="eyebrow">Migration activity</span>
                  <h3>Execution log from the latest migration run</h3>
                </div>
              </div>

              {executionLogs.length ? (
                <div className="activity-list">
                  {executionLogs.map((entry, index) => (
                    <article key={`${entry.table || "log"}-${index}`} className="activity-item">
                      <div className="activity-item__top">
                        <strong>{entry.table || "Pipeline"}</strong>
                        <span
                          className={
                            entry.status === "completed"
                              ? "status-chip status-chip--healthy"
                              : entry.status === "failed"
                                ? "status-chip status-chip--critical"
                              : entry.status === "skipped"
                                ? "status-chip status-chip--info"
                                : "status-chip status-chip--warning"
                          }
                        >
                          {entry.status || "info"}
                        </span>
                      </div>
                      <p>{entry.message}</p>
                      {typeof entry.migrated_count === "number" ? (
                        <small>{entry.migrated_count} rows written</small>
                      ) : null}
                    </article>
                  ))}
                </div>
              ) : (
                <div className="empty-state">
                  Start migration to see per-table execution logs here.
                </div>
              )}
            </section>

            <section className="panel">
              <div className="panel__header">
                <div>
                  <span className="eyebrow">Migration result</span>
                  <h3>Validation output after migration</h3>
                </div>
              </div>

              {migrationResult?.validation ? (
                <div className="validation-grid">
                  {migrationResult.validation.tables.map((entry) => (
                    <article key={entry.table} className="validation-card">
                      <div className="validation-card__top">
                        <strong>{entry.table}</strong>
                        <span
                          className={
                            entry.skipped
                              ? "status-chip status-chip--info"
                              : entry.count_match
                                ? "status-chip status-chip--healthy"
                                : "status-chip status-chip--critical"
                          }
                        >
                          {entry.skipped ? "Embedded" : entry.count_match ? "Matched" : "Mismatch"}
                        </span>
                      </div>
                      <dl>
                        <div>
                          <dt>Source rows</dt>
                          <dd>{entry.source_count}</dd>
                        </div>
                        <div>
                          <dt>Target docs</dt>
                          <dd>{entry.mongo_count}</dd>
                        </div>
                        <div>
                          <dt>Datatype check</dt>
                          <dd>{entry.datatype_match ? "Pass" : "Investigate"}</dd>
                        </div>
                      </dl>
                      <p>{entry.reason || "Collection migrated and validated."}</p>
                    </article>
                  ))}
                </div>
              ) : (
                <div className="empty-state">
                  Start migration to see live validation results inside the app.
                </div>
              )}
            </section>
          </div>

          <div className="workspace-grid__secondary">
            <section className="panel panel--compact">
              <div className="panel__header">
                <div>
                  <span className="eyebrow">Connection status</span>
                  <h3>Connector checks</h3>
                </div>
              </div>
              <div className="highlight-list">
                <article>
                  <strong>{activeSourceConnector?.label || "Select Source DB"}</strong>
                  <p>
                    {connectionResult?.source?.ok
                      ? `Connected to ${connectionResult.source.database} (${connectionResult.source.schema} schema)`
                      : "Not connected yet"}
                  </p>
                </article>
                <article>
                  <strong>{activeTargetConnector?.label || "Select Target DB"}</strong>
                  <p>{connectionResult?.target?.ok ? `Connected to ${connectionResult.target.database}` : "Not connected yet"}</p>
                </article>
              </div>
            </section>

            <section className="panel panel--compact">
              <div className="panel__header">
                <div>
                  <span className="eyebrow">Migration order</span>
                  <h3>Execution queue</h3>
                </div>
              </div>
              {assessment?.migration_order?.length ? (
                <div className="queue-wrap">
                  <ol className="queue-list">
                    {assessment.migration_order.map((table) => (
                      <li key={table}>{table}</li>
                    ))}
                  </ol>
                </div>
              ) : (
                <div className="empty-state empty-state--compact">Assessment will populate the migration order.</div>
              )}
            </section>

            <section className="panel panel--compact">
              <div className="panel__header">
                <div>
                  <span className="eyebrow">Preview</span>
                  <h3>First discovered table sample</h3>
                </div>
              </div>
              {discoveredTables[0]?.preview?.length ? (
                <pre className="preview-block">{JSON.stringify(discoveredTables[0].preview, null, 2)}</pre>
              ) : (
                <div className="empty-state empty-state--compact">Discover tables to inspect sample rows.</div>
              )}
            </section>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
