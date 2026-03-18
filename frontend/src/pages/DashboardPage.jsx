import { useMemo, useState } from 'react'
import CandidateResultCard from '../components/candidates/CandidateResultCard'
import Card from '../components/ui/Card'
import Loader from '../components/ui/Loader'
import { evaluateCandidate } from '../services/jobMatchApi'

const sampleCommand =
  'Score Rahul Sharma for our Python backend role, search his GitHub, save results, and recommend.'

const defaultJD = `Role: Python Backend Developer
Skills: Python, FastAPI/Flask, SQL, API design
Experience: 1+ year
Nice to have: Docker, cloud deployment`

function DashboardPage() {
  const [command, setCommand] = useState(sampleCommand)
  const [jobDescription, setJobDescription] = useState(defaultJD)
  const [result, setResult] = useState(null)
  const [finalAnswer, setFinalAnswer] = useState('')
  const [trace, setTrace] = useState([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')

  const stats = useMemo(() => {
    if (!result) return null
    const score = Number(result.score ?? 0)
    return {
      score,
      recommendation: result.recommendation || 'pending',
      confidence:
        result.confidence ?? (score >= 75 ? 'High' : score >= 50 ? 'Medium' : 'Low'),
    }
  }, [result])

  async function handleEvaluate(event) {
    event.preventDefault()
    setError('')
    setFinalAnswer('')
    setIsSubmitting(true)
    try {
      const response = await evaluateCandidate({
        command: command.trim(),
        jd: jobDescription.trim(),
      })
      setResult(response?.result ?? response)
      setFinalAnswer(response?.final_answer || '')
      setTrace(response?.trace ?? response?.reasoning_steps ?? [])
    } catch (err) {
      setError(err.message || 'Unable to evaluate candidate.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="page-grid">
      <Card
        title="Evaluate Candidate"
        subtitle="One command triggers web search, scoring, save, and recommendation. For DB-only commands, JD can be left blank."
      >
        <form className="stack-form" onSubmit={handleEvaluate}>
          <label className="input-group">
            <span>Recruiter Command</span>
            <textarea
              rows={3}
              value={command}
              onChange={(event) => setCommand(event.target.value)}
              placeholder="Type recruiter command..."
              required
            />
          </label>

          <label className="input-group">
            <span>Job Description</span>
            <textarea
              rows={6}
              value={jobDescription}
              onChange={(event) => setJobDescription(event.target.value)}
              placeholder="Paste job description (optional for DB commands like list/top/delete)..."
            />
          </label>

          <div className="form-actions">
            <button type="submit" className="btn" disabled={isSubmitting}>
              {isSubmitting ? 'Evaluating...' : 'Run JobMatch Agent'}
            </button>
          </div>
        </form>
        {error ? <p className="error-text">{error}</p> : null}
      </Card>

      {isSubmitting ? <Loader label="Agent is reasoning and calling tools..." /> : null}

      {stats ? (
        <div className="stat-grid">
          <article className="stat-card">
            <p className="stat-label">Score</p>
            <p className="stat-value">{stats.score} / 100</p>
          </article>
          <article className="stat-card">
            <p className="stat-label">Recommendation</p>
            <p className="stat-value">{stats.recommendation}</p>
          </article>
          <article className="stat-card">
            <p className="stat-label">Confidence</p>
            <p className="stat-value">{stats.confidence}</p>
          </article>
        </div>
      ) : null}

      {finalAnswer ? (
        <Card title="Final Response" subtitle="Recruiter-facing summary from the agent">
          <p className="result-reason">{finalAnswer}</p>
        </Card>
      ) : null}

      <CandidateResultCard result={result} />

      <Card title="Reasoning Trace" subtitle="Thought -> Action -> Observation logs">
        {!trace.length ? (
          <p className="empty-note">No trace yet. Run an evaluation to view agent reasoning.</p>
        ) : (
          <ol className="trace-list">
            {trace.map((item, index) => (
              <li key={`${index}-${item.action ?? ''}`} className="trace-item">
                <p>
                  <strong>Thought:</strong> {item.thought || item.step || 'N/A'}
                </p>
                <p>
                  <strong>Action:</strong> {item.action || 'N/A'}
                </p>
                <p>
                  <strong>Observation:</strong> {item.observation || item.result || 'N/A'}
                </p>
              </li>
            ))}
          </ol>
        )}
      </Card>
    </div>
  )
}

export default DashboardPage
