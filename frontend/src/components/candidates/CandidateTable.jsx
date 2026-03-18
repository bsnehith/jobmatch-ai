import { Trash2 } from 'lucide-react'
import { formatDate, toTitleCase } from '../../utils/formatters'
import Badge from '../ui/Badge'

function scoreTone(score) {
  if (score >= 75) return 'success'
  if (score >= 50) return 'warning'
  return 'danger'
}

function CandidateTable({ candidates, onDelete, deletingName = '' }) {
  if (!candidates.length) {
    return <p className="empty-note">No candidates in the database yet.</p>
  }

  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Score</th>
            <th>Recommendation</th>
            <th>Updated</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {candidates.map((candidate) => {
            const isDeleting = deletingName === candidate.name
            return (
              <tr key={`${candidate.name}-${candidate.updated_at ?? ''}`}>
                <td data-label="Name">{candidate.name}</td>
                <td data-label="Score">
                  <Badge tone={scoreTone(Number(candidate.score || 0))}>
                    {candidate.score ?? '-'} / 100
                  </Badge>
                </td>
                <td data-label="Recommendation">
                  {toTitleCase(candidate.recommendation || 'N/A')}
                </td>
                <td data-label="Updated">
                  {formatDate(candidate.updated_at || candidate.created_at)}
                </td>
                <td data-label="Actions">
                  <button
                    type="button"
                    className="btn btn-danger btn-icon"
                    onClick={() => onDelete(candidate.name)}
                    disabled={isDeleting}
                  >
                    <Trash2 size={14} />
                    <span>{isDeleting ? 'Removing...' : 'Delete'}</span>
                  </button>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

export default CandidateTable
