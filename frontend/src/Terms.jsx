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

export default function Terms() {
  return (
    <div className="min-h-screen bg-paper-100 text-ink-900">
      <header className="sticky top-0 z-10 bg-paper-100 border-b border-paper-300">
        <div className="max-w-content mx-auto px-6 h-14 flex items-center gap-4">
          <Link to="/" className="font-serif font-semibold text-base text-ink-900 tracking-tight hover:text-ink-700 transition-colors">
            VUL-LLM
          </Link>
          <span className="text-ink-300 select-none">|</span>
          <span className="text-xs text-ink-500">Terms of Use</span>
        </div>
      </header>

      <main className="max-w-content mx-auto px-6 py-12">
        <div className="max-w-2xl flex flex-col gap-10">
          <div>
            <p className="text-xs text-ink-400 mb-2 font-mono uppercase tracking-widest">
              Last updated {LAST_UPDATED}
            </p>
            <h1 className="font-serif text-3xl font-semibold text-ink-900 leading-tight">
              Terms of Use
            </h1>
            <p className="mt-3 text-sm text-ink-500 leading-relaxed">
              By running or using VUL-LLM you accept these terms. If you do not
              accept them, do not use the software.
            </p>
          </div>

          <Section title="Purpose and scope">
            <p>
              VUL-LLM is an open-source academic research tool. Its purpose is
              to benchmark PII masking methods for use with large language
              models. It is made available for research, education, and personal
              experimentation only.
            </p>
            <p>
              VUL-LLM is not a licensed medical device, legal service, or
              financial product. It must not be used to make decisions that
              affect the health, safety, finances, or legal rights of any person.
            </p>
          </Section>

          <Section title="Acceptable use">
            <p>You may use VUL-LLM to:</p>
            <ul className="list-disc pl-5 flex flex-col gap-1">
              <li>Research and compare PII masking techniques</li>
              <li>Run experiments on synthetic or anonymised data</li>
              <li>Evaluate the semantic utility cost of different privacy methods</li>
              <li>Build on or modify the codebase under the terms of its open-source licence</li>
            </ul>
            <p>You must not use VUL-LLM to:</p>
            <ul className="list-disc pl-5 flex flex-col gap-1">
              <li>Process real patient records, government identity documents, or regulated financial data without proper legal authority and safeguards</li>
              <li>Attempt to reverse-engineer or extract PII from third-party AI provider responses</li>
              <li>Circumvent the prompt injection firewall or other security controls</li>
              <li>Deploy the tool as a shared public service without reviewing the security guidance in the README</li>
            </ul>
          </Section>

          <Section title="AI provider outputs">
            <p>
              When a live AI provider is configured, responses come from that
              provider's model. VUL-LLM does not verify, validate, or endorse
              any AI-generated output. AI responses may be inaccurate,
              incomplete, or inappropriate. You are responsible for evaluating
              any output before acting on it.
            </p>
            <p>
              When the mock provider is active, responses are generated locally
              by deterministic logic. They do not reflect real AI model output.
              The interface labels simulated results clearly.
            </p>
          </Section>

          <Section title="No warranty">
            <p>
              VUL-LLM is provided as-is, with no warranty of any kind, express
              or implied. The masking pipelines reduce the risk of PII exposure
              to AI providers but do not guarantee complete elimination of
              sensitive data in all cases. No system can guarantee this. You
              accept full responsibility for evaluating whether the tool is
              suitable for your use case before submitting any data.
            </p>
          </Section>

          <Section title="Limitation of liability">
            <p>
              To the maximum extent permitted by applicable law, the authors and
              contributors of VUL-LLM are not liable for any direct, indirect,
              incidental, or consequential damages arising from your use of the
              software, including but not limited to data exposure, business
              loss, or regulatory penalties.
            </p>
          </Section>

          <Section title="Open-source licence">
            <p>
              VUL-LLM is released under the MIT Licence. You are free to use,
              copy, modify, merge, publish, distribute, and sublicence the code,
              provided you include the original copyright notice and this licence
              notice in all copies or substantial portions of the software. The
              software is provided without warranty as stated above.
            </p>
          </Section>

          <Section title="Third-party services">
            <p>
              When you supply an API key for Groq, Google Gemini, OpenAI, or
              Anthropic, your use of that provider is governed by their
              respective terms of service. VUL-LLM is not affiliated with any
              of these companies. API key costs, rate limits, and data handling
              are your responsibility as the key holder.
            </p>
          </Section>

          <Section title="Changes to these terms">
            <p>
              These terms may be updated as the project develops. The date at
              the top of this page reflects the last revision. Continued use
              after a revision constitutes acceptance of the updated terms.
            </p>
          </Section>

          <div className="pt-4 border-t border-paper-300">
            <Link to="/" className="text-sm text-accent hover:underline">Back to benchmark</Link>
          </div>
        </div>
      </main>

      <footer className="border-t border-paper-300 mt-16">
        <div className="max-w-content mx-auto px-6 py-6 flex flex-col sm:flex-row justify-between gap-3">
          <p className="text-xs text-ink-400">VUL-LLM is a research prototype released under the MIT Licence.</p>
          <nav className="flex gap-4 text-xs text-ink-400">
            <Link to="/privacy" className="hover:text-ink-900 transition-colors">Privacy policy</Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}
