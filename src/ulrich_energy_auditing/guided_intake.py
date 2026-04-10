from __future__ import annotations

import json
import threading
import webbrowser
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from ulrich_energy_auditing.analysis import analyze_audit
from ulrich_energy_auditing.importers import (
    build_audit_input,
    load_utility_bills_text,
    write_audit_json,
)
from ulrich_energy_auditing.models import AuditInput
from ulrich_energy_auditing.persistence import save_audit_bundle
from ulrich_energy_auditing.reporting import render_markdown_report, write_pdf_report

_DEFAULT_EMIT_JSON_PATH = Path("reports") / "guided-intake-audit.json"


@dataclass(slots=True)
class GuidedIntakeOptions:
    emit_json_path: Path
    output_path: Path
    pdf_output_path: Path | None
    benchmark_pack_id: str | None
    save_name: str | None
    host: str = "127.0.0.1"
    port: int = 0
    open_browser: bool = True


@dataclass(slots=True)
class GuidedIntakeSession:
    options: GuidedIntakeOptions
    result: dict[str, Any] | None = None
    completed: threading.Event = field(default_factory=threading.Event)


def launch_guided_intake(
    *,
    emit_json_path: Path | None,
    output_path: Path,
    pdf_output_path: Path | None,
    benchmark_pack_id: str | None,
    save_name: str | None,
    port: int = 0,
    open_browser: bool = True,
) -> dict[str, Any]:
    options = GuidedIntakeOptions(
        emit_json_path=emit_json_path or _DEFAULT_EMIT_JSON_PATH,
        output_path=output_path,
        pdf_output_path=pdf_output_path,
        benchmark_pack_id=benchmark_pack_id,
        save_name=save_name,
        port=port,
        open_browser=open_browser,
    )
    session = GuidedIntakeSession(options=options)
    handler = _build_handler(session)
    server = ThreadingHTTPServer((options.host, options.port), handler)
    server.daemon_threads = True
    host, bound_port = server.server_address
    url = f"http://{host}:{bound_port}/"
    print(f"Guided intake ready at {url}")
    print("Submit the form in your browser to generate the normalized audit and report outputs.")

    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    try:
        if options.open_browser:
            webbrowser.open(url)
        session.completed.wait()
        if session.result is None:
            raise RuntimeError("Guided intake session ended before a submission completed.")
        return session.result
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=5)


def process_guided_intake_submission(
    payload: dict[str, Any],
    *,
    options: GuidedIntakeOptions,
) -> dict[str, Any]:
    audit_payload = payload.get("audit")
    if not isinstance(audit_payload, dict):
        raise ValueError("Guided intake submission must include an audit object.")

    utility_bills_csv = str(payload.get("utility_bills_csv") or "").strip()
    save_name = str(payload.get("save_name") or options.save_name or "").strip()

    audit = build_audit_input(audit_payload)
    if utility_bills_csv:
        consumption = load_utility_bills_text(utility_bills_csv)
        audit = AuditInput(
            building=audit.building,
            systems=audit.systems,
            consumption=consumption,
            notes=list(audit.notes),
        )

    summary = analyze_audit(audit, benchmark_pack_id=options.benchmark_pack_id)
    report_markdown = render_markdown_report(audit, summary)

    options.emit_json_path.parent.mkdir(parents=True, exist_ok=True)
    write_audit_json(audit, options.emit_json_path)

    options.output_path.parent.mkdir(parents=True, exist_ok=True)
    options.output_path.write_text(report_markdown, encoding="utf-8")

    if options.pdf_output_path is not None:
        write_pdf_report(audit, summary, options.pdf_output_path)

    save_metadata: dict[str, Any] | None = None
    if save_name:
        save_metadata = save_audit_bundle(
            audit,
            summary,
            report_markdown=report_markdown,
            input_path=None,
            utility_bills_path=None,
            save_name=save_name,
            pdf_output_path=options.pdf_output_path,
            input_source_override=(
                "guided-intake+utility-bills" if utility_bills_csv else "guided-intake"
            ),
        )

    return {
        "emit_json_path": str(options.emit_json_path),
        "output_path": str(options.output_path),
        "pdf_output_path": str(options.pdf_output_path) if options.pdf_output_path else None,
        "benchmark_pack_id": summary.benchmark_comparison.pack.pack_id,
        "benchmark_pack_label": summary.benchmark_comparison.pack.label,
        "saved_bundle_dir": (
            str(Path(save_metadata["audit_json_path"]).parent) if save_metadata is not None else None
        ),
        "save_id": save_metadata["save_id"] if save_metadata is not None else None,
    }


def _build_handler(session: GuidedIntakeSession) -> type[BaseHTTPRequestHandler]:
    class GuidedIntakeHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/favicon.ico":
                self.send_response(HTTPStatus.NO_CONTENT)
                self.end_headers()
                return
            if self.path != "/":
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self._write_json_or_html(
                HTTPStatus.OK,
                _render_page(session.options),
                content_type="text/html; charset=utf-8",
            )

        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/api/submit":
                self.send_error(HTTPStatus.NOT_FOUND)
                return

            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length)
            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except json.JSONDecodeError:
                self._write_json_or_html(
                    HTTPStatus.BAD_REQUEST,
                    json.dumps({"error": "Submission payload must be valid JSON."}),
                    content_type="application/json; charset=utf-8",
                )
                return

            try:
                result = process_guided_intake_submission(payload, options=session.options)
            except ValueError as exc:
                self._write_json_or_html(
                    HTTPStatus.BAD_REQUEST,
                    json.dumps({"error": str(exc)}),
                    content_type="application/json; charset=utf-8",
                )
                return
            except Exception as exc:  # pragma: no cover - defensive path for local server failures
                self._write_json_or_html(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    json.dumps({"error": str(exc)}),
                    content_type="application/json; charset=utf-8",
                )
                return

            session.result = result
            session.completed.set()
            self._write_json_or_html(
                HTTPStatus.OK,
                json.dumps(result),
                content_type="application/json; charset=utf-8",
            )
            threading.Thread(target=self.server.shutdown, daemon=True).start()

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return

        def _write_json_or_html(self, status: HTTPStatus, body: str, *, content_type: str) -> None:
            encoded = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    return GuidedIntakeHandler


def _render_page(options: GuidedIntakeOptions) -> str:
    page_config = json.dumps(
        {
            "emitJsonPath": str(options.emit_json_path),
            "outputPath": str(options.output_path),
            "pdfOutputPath": str(options.pdf_output_path) if options.pdf_output_path else None,
            "defaultSaveName": options.save_name or "",
        }
    )
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Ulrich Energy Auditing Guided Intake</title>
    <style>
      :root {{
        color-scheme: light;
        --bg: #f6f3ec;
        --surface: #fffaf2;
        --ink: #1f1c18;
        --muted: #6f675e;
        --accent: #9c4f24;
        --accent-soft: #f0d2bf;
        --line: #d4c7b9;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        font-family: "Segoe UI", Tahoma, sans-serif;
        background: linear-gradient(180deg, #f3eadb 0%, var(--bg) 100%);
        color: var(--ink);
      }}
      main {{
        width: min(980px, calc(100% - 2rem));
        margin: 2rem auto 4rem;
      }}
      .hero {{
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 20px;
        padding: 1.5rem;
        box-shadow: 0 10px 30px rgba(31, 28, 24, 0.08);
      }}
      h1, h2 {{ margin-top: 0; }}
      p {{ line-height: 1.55; }}
      form {{
        display: grid;
        gap: 1rem;
        margin-top: 1.5rem;
      }}
      section {{
        background: rgba(255, 255, 255, 0.68);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 1rem;
      }}
      .grid {{
        display: grid;
        gap: 0.85rem;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      }}
      label {{
        display: grid;
        gap: 0.35rem;
        font-weight: 600;
      }}
      input, textarea, select {{
        width: 100%;
        border-radius: 12px;
        border: 1px solid var(--line);
        padding: 0.75rem 0.85rem;
        font: inherit;
        background: #fff;
      }}
      textarea {{
        min-height: 130px;
        resize: vertical;
      }}
      .helper {{
        color: var(--muted);
        font-size: 0.95rem;
        margin: 0;
      }}
      .callout {{
        background: var(--accent-soft);
        border-radius: 14px;
        padding: 0.9rem 1rem;
      }}
      button {{
        width: fit-content;
        padding: 0.9rem 1.25rem;
        border: 0;
        border-radius: 999px;
        background: var(--accent);
        color: #fff;
        font: inherit;
        font-weight: 700;
        cursor: pointer;
      }}
      #status {{
        margin-top: 1rem;
        padding: 1rem;
        border-radius: 14px;
        background: #fff;
        border: 1px solid var(--line);
        display: none;
      }}
      #status[data-state="error"] {{
        border-color: #b8472f;
        background: #fff1ed;
      }}
      #status[data-state="success"] {{
        border-color: #2f7f53;
        background: #eef9f1;
      }}
      code {{
        font-family: Consolas, monospace;
        font-size: 0.95rem;
      }}
    </style>
  </head>
  <body>
    <main>
      <div class="hero">
        <p class="helper">Ulrich Energy Auditing guided intake</p>
        <h1>Capture one audit in the browser and land on the same CLI contract</h1>
        <p>
          This wizard writes the same normalized audit JSON used by the existing CLI, then
          generates the Markdown report and optional PDF through the current Python workflow.
        </p>
        <div class="callout">
          <strong>Output contract:</strong>
          <div><code id="emit-json-path"></code></div>
          <div><code id="output-path"></code></div>
          <div><code id="pdf-output-path"></code></div>
        </div>
        <form id="guided-intake-form">
          <section>
            <h2>Building</h2>
            <div class="grid">
              <label>Client name
                <input name="client_name" required>
              </label>
              <label>Address
                <input name="address" required>
              </label>
              <label>Building type
                <select name="building_type">
                  <option value="residential">Residential</option>
                  <option value="small-office">Small office</option>
                </select>
              </label>
              <label>Square feet
                <input name="square_feet" type="number" min="1" step="1" required>
              </label>
              <label>Year built
                <input name="year_built" type="number" min="1800" step="1" required>
              </label>
            </div>
          </section>
          <section>
            <h2>Systems</h2>
            <div class="grid">
              <label>HVAC age (years)
                <input name="hvac_age_years" type="number" min="0" step="1" required>
              </label>
              <label>Water heater age (years)
                <input name="water_heater_age_years" type="number" min="0" step="1" required>
              </label>
              <label>Attic insulation R-value
                <input name="attic_insulation_r_value" type="number" min="0" step="1" required>
              </label>
              <label>Blower door ACH50
                <input name="blower_door_ach50" type="number" min="0" step="0.1" required>
              </label>
              <label>Duct leakage percent
                <input name="duct_leakage_percent" type="number" min="0" step="0.1" required>
              </label>
            </div>
          </section>
          <section>
            <h2>Consumption</h2>
            <p class="helper">
              Enter annual totals directly, or upload a utility-bill CSV to override these values.
            </p>
            <div class="grid">
              <label>Annual electric usage (kWh)
                <input name="annual_electric_kwh" type="number" min="0" step="0.1" required>
              </label>
              <label>Annual gas usage (therms)
                <input name="annual_gas_therms" type="number" min="0" step="0.1" required>
              </label>
              <label>Utility-bill CSV
                <input id="utility-bills" name="utility_bills" type="file" accept=".csv,text/csv">
              </label>
              <label>Save bundle name (optional)
                <input name="save_name" placeholder="Main Street audit">
              </label>
            </div>
          </section>
          <section>
            <h2>Notes</h2>
            <label>One note per line
              <textarea name="notes" placeholder="South-facing rooms run warm in summer.&#10;Duct insulation missing in attic trunk line."></textarea>
            </label>
          </section>
          <button type="submit">Generate audit outputs</button>
        </form>
        <div id="status" aria-live="polite"></div>
      </div>
    </main>
    <script>
      const config = {page_config};
      document.querySelector("#emit-json-path").textContent = `Normalized audit: ${{config.emitJsonPath}}`;
      document.querySelector("#output-path").textContent = `Markdown report: ${{config.outputPath}}`;
      document.querySelector("#pdf-output-path").textContent = config.pdfOutputPath
        ? `PDF report: ${{config.pdfOutputPath}}`
        : "PDF report: not requested for this launch";
      document.querySelector('input[name="save_name"]').value = config.defaultSaveName;

      const form = document.querySelector("#guided-intake-form");
      const status = document.querySelector("#status");

      function showStatus(state, html) {{
        status.dataset.state = state;
        status.innerHTML = html;
        status.style.display = "block";
      }}

      async function readUtilityBillsCsv() {{
        const fileInput = document.querySelector("#utility-bills");
        const file = fileInput.files[0];
        if (!file) {{
          return "";
        }}
        return await file.text();
      }}

      form.addEventListener("submit", async (event) => {{
        event.preventDefault();
        const formData = new FormData(form);
        const payload = {{
          audit: {{
            building: {{
              client_name: formData.get("client_name"),
              address: formData.get("address"),
              building_type: formData.get("building_type"),
              square_feet: Number(formData.get("square_feet")),
              year_built: Number(formData.get("year_built")),
            }},
            systems: {{
              hvac_age_years: Number(formData.get("hvac_age_years")),
              water_heater_age_years: Number(formData.get("water_heater_age_years")),
              attic_insulation_r_value: Number(formData.get("attic_insulation_r_value")),
              blower_door_ach50: Number(formData.get("blower_door_ach50")),
              duct_leakage_percent: Number(formData.get("duct_leakage_percent")),
            }},
            consumption: {{
              annual_electric_kwh: Number(formData.get("annual_electric_kwh")),
              annual_gas_therms: Number(formData.get("annual_gas_therms")),
            }},
            notes: String(formData.get("notes") || "")
              .split(/\\r?\\n/)
              .map((entry) => entry.trim())
              .filter(Boolean),
          }},
          utility_bills_csv: await readUtilityBillsCsv(),
          save_name: String(formData.get("save_name") || "").trim(),
        }};

        showStatus("working", "Generating normalized audit and report outputs...");
        const response = await fetch("/api/submit", {{
          method: "POST",
          headers: {{
            "Content-Type": "application/json",
          }},
          body: JSON.stringify(payload),
        }});
        const result = await response.json();
        if (!response.ok) {{
          showStatus("error", `<strong>Submission failed.</strong><div>${{result.error}}</div>`);
          return;
        }}
        const savedLine = result.saved_bundle_dir
          ? `<div>Saved bundle: <code>${{result.saved_bundle_dir}}</code></div>`
          : "<div>Saved bundle: not requested</div>";
        showStatus(
          "success",
          `<strong>Guided intake completed.</strong>
          <div>Normalized audit: <code>${{result.emit_json_path}}</code></div>
          <div>Markdown report: <code>${{result.output_path}}</code></div>
          <div>Benchmark pack: <code>${{result.benchmark_pack_id}}</code> (${{result.benchmark_pack_label}})</div>
          <div>${{result.pdf_output_path ? `PDF report: <code>${{result.pdf_output_path}}</code>` : "PDF report: not requested"}}</div>
          ${{savedLine}}`
        );
      }});
    </script>
  </body>
</html>
"""
