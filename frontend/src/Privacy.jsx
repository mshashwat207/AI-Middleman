import { Link } from "react-router-dom";

const LAST_UPDATED = "30 September 2026";

function Section({ title, children }) {
  return (
    <section className="flex flex-col gap-3">
      <h2 className="font-serif text-lg font-semibold text-ink-900 border-b border-paper-300 pb-2">
        {title}
      </h2>
      <div className="text-sm text-ink-500 leading-relaxed flex flex-col gap-3">
        {children}
      </div>
    </section>
  );
}

export default function Privacy() {
  return (
    <div className="min-h-screen bg-paper-100 text-ink-900">
      <header className="sticky top-0 z-10 bg-paper-100 border-b border-paper-300">
        <div className="max-w-content mx-auto px-6 h-14 flex items-center gap-4">
          <Link to="/" className="font-serif font-semibold text-base text-ink-900 tracking-tight hover:text-ink-700 transition-colors">
            VUL-LLM
          </Link>
          <span className="text-ink-300 select-none">|</span>
          <span className="text-xs text-ink-500">Privacy Policy</span>
        </div>
      </header>

      <main className="max-w-content mx-auto px-6 py-12">
        <div className="max-w-2xl flex flex-col gap-10">
          <div>
            <p className="text-xs text-ink-400 mb-2 font-mono uppercase tracking-widest">
              Last updated {LAST_UPDATED}
            </p>
            <h1 className="font-serif text-3xl font-semibold text-ink-900 leading-tight">
              Privacy Policy
            </h1>
            <p className="mt-3 text-sm text-ink-500 leading-relaxed">
              This policy describes what data VUL-LLM processes, where it goes,
              and how it is protected. VUL-LLM is a local research prototype.
              All data stays on the machine you run it on unless you explicitly
              configure a third-party AI provider key.
            </p>
          </div>

          <Section title="What VUL-LLM is">
            <p>
              VUL-LLM is an open-source research tool that benchmarks three
              privacy-preserving methods for handling personally identifiable
              information (PII) before sending text to large language models.
              It is designed for academic evaluation, not for production use with
              real patient, legal, or financial records.
            </p>
          </Section>

          <Section title="Data you submit">
            <p>
              When you type a prompt or upload a file, the text is processed
              entirely on the server you are running. If you are running VUL-LLM
              locally, that is your own machine. No text is sent to any
              third-party service by default.
            </p>
            <p>
              When you select a live AI provider (Groq, Google Gemini, OpenAI,
              or Anthropic) and that provider has a configured API key, the
              masked version of your text is sent to that provider over HTTPS.
              The original unmasked text never leaves the server. Only the
              output of the masking step (redacted text, tokens, or synthetic
              substitutes) is transmitted.
            </p>
          </Section>

          <Section title="What gets stored locally">
            <p>
              VUL-LLM stores the following in a local SQLite database file
              named <code className="font-mono text-ink-700">middleman.db</code> in
              the backend directory:
            </p>
            <ul className="list-disc pl-5 flex flex-col gap-1">
              <li>Session identifiers and expiry timestamps</li>
              <li>Encrypted token mappings that link masked tokens back to original values. These are encrypted with a Fernet symmetric key stored in your .env file and expire after 30 minutes by default.</li>
              <li>Audit log entries containing: request ID, session ID, provider name, entity type counts, injection risk score, latency, and timestamp. Audit logs never contain original PII values.</li>
            </ul>
            <p>
              You can delete the database file at any time to remove all stored
              data. No data is sent to any analytics service or external
              logging platform.
            </p>
          </Section>

          <Section title="Third-party AI providers">
            <p>
              If you configure an API key, your masked text is sent to that
              provider. Each provider has its own data handling practices:
            </p>
            <ul className="list-disc pl-5 flex flex-col gap-1">
              <li>Groq: <a href="https://groq.com/privacy-policy/" className="text-accent hover:underline" target="_blank" rel="noreferrer">groq.com/privacy-policy</a></li>
              <li>Google Gemini: <a href="https://policies.google.com/privacy" className="text-accent hover:underline" target="_blank" rel="noreferrer">policies.google.com/privacy</a></li>
              <li>OpenAI: <a href="https://openai.com/policies/privacy-policy" className="text-accent hover:underline" target="_blank" rel="noreferrer">openai.com/policies/privacy-policy</a></li>
              <li>Anthropic: <a href="https://www.anthropic.com/privacy" className="text-accent hover:underline" target="_blank" rel="noreferrer">anthropic.com/privacy</a></li>
            </ul>
            <p>
              Because VUL-LLM only transmits masked text, the risk of personal
              data exposure to these providers is reduced, but not eliminated.
              Do not submit real regulated personal data (medical records,
              financial data, government IDs) through this tool.
            </p>
          </Section>

          <Section title="Cookies and tracking">
            <p>
              VUL-LLM does not set cookies. It does not use analytics, tracking
              pixels, third-party scripts, or any form of usage tracking.
            </p>
          </Section>

          <Section title="Data security">
            <p>
              Token mappings are encrypted at rest using Fernet symmetric
              encryption (AES-128-CBC). The encryption key is held in your
              local .env file. Connections between the browser and the backend
              server use plain HTTP when running locally. If you deploy this
              tool to a network-accessible server, you are responsible for
              adding TLS.
            </p>
          </Section>

          <Section title="Your data rights">
            <p>
              Because all data is stored locally on hardware you control, you
              have full access to and control over everything VUL-LLM stores.
              You can inspect, export, or delete the SQLite database at any time
              without contacting anyone.
            </p>
          </Section>

          <Section title="Changes to this policy">
            <p>
              This policy will be updated as the project develops. The date at
              the top of this page reflects the last revision. Significant
              changes will be noted in the project changelog.
            </p>
          </Section>

          <div className="pt-4 border-t border-paper-300">
            <Link to="/" className="text-sm text-accent hover:underline">Back to benchmark</Link>
          </div>
        </div>
      </main>

      <footer className="border-t border-paper-300 mt-16">
        <div className="max-w-content mx-auto px-6 py-6 flex flex-col sm:flex-row justify-between gap-3">
          <p className="text-xs text-ink-400">VUL-LLM is a research prototype. Run it on hardware you control.</p>
          <nav className="flex gap-4 text-xs text-ink-400">
            <Link to="/terms" className="hover:text-ink-900 transition-colors">Terms of use</Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}
