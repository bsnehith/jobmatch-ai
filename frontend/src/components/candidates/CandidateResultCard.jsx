import { ExternalLink } from 'lucide-react'
import { normalizeList, toTitleCase } from '../../utils/formatters'
import Badge from '../ui/Badge'
import Card from '../ui/Card'

function recommendationTone(recommendation = '') {
  const value = recommendation.toLowerCase()
  if (value.includes('hire') || value.includes('interview')) return 'success'
  if (value.includes('insufficient')) return 'warning'
  if (value.includes('reject') || value.includes('no-hire')) return 'danger'
  return 'neutral'
}

function CandidateResultCard({ result }) {
  if (!result) return null

  const strengths = normalizeList(result.strengths)
  const gaps = normalizeList(result.gaps)
  const finalReason = result.reason || result.final_reason || 'No reason returned.'

  return (
    <Card title="Latest Evaluation" subtitle="Decision output from the agent">
      <div className="result-header">
        <div>
          <p className="result-name">{result.name || result.candidate || 'Unknown Candidate'}</p>
          <p className="result-score">Score: {result.score ?? 'N/A'} / 100</p>
        </div>
        <Badge tone={recommendationTone(result.recommendation)}>
          {toTitleCase(result.recommendation || 'Pending')}
        </Badge>
      </div>

      <p className="result-reason">{finalReason}</p>

      <div className="list-grid">
        <div>
          <h3 className="list-title">Strengths</h3>
          <ul className="bullet-list">
            {strengths.length ? (
              strengths.map((item) => <li key={item}>{item}</li>)
            ) : (
              <li>No strengths returned.</li>
            )}
          </ul>
        </div>

        <div>
          <h3 className="list-title">Gaps</h3>
          <ul className="bullet-list">
            {gaps.length ? (
              gaps.map((item) => <li key={item}>{item}</li>)
            ) : (
              <li>No gaps returned.</li>
            )}
          </ul>
        </div>
      </div>

      {result.web_url ? (
        <a className="result-link" href={result.web_url} target="_blank" rel="noreferrer">
          <ExternalLink size={14} />
          <span>Open candidate profile</span>
        </a>
      ) : null}
    </Card>
  )
}

export default CandidateResultCard
