import { useEffect, useState } from 'react'
import CandidateTable from '../components/candidates/CandidateTable'
import Card from '../components/ui/Card'
import Loader from '../components/ui/Loader'
import {
  deleteCandidate,
  getCandidate,
  listCandidates,
  topCandidates,
} from '../services/jobMatchApi'
import { getCandidateRows } from '../utils/formatters'

function CandidatesPage() {
  const [candidates, setCandidates] = useState([])
  const [searchName, setSearchName] = useState('')
  const [limit, setLimit] = useState(3)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [deletingName, setDeletingName] = useState('')

  async function fetchAll() {
    setError('')
    setLoading(true)
    try {
      const response = await listCandidates()
      setCandidates(getCandidateRows(response))
    } catch (err) {
      setError(err.message || 'Unable to fetch candidates.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAll()
  }, [])

  async function handleTop() {
    setError('')
    setLoading(true)
    try {
      const response = await topCandidates(limit)
      setCandidates(getCandidateRows(response))
    } catch (err) {
      setError(err.message || 'Unable to fetch top candidates.')
    } finally {
      setLoading(false)
    }
  }

  async function handleSearch(event) {
    event.preventDefault()
    if (!searchName.trim()) return

    setError('')
    setLoading(true)
    try {
      const response = await getCandidate(searchName.trim())
      setCandidates(getCandidateRows(response))
    } catch (err) {
      setError(err.message || 'Candidate not found.')
      setCandidates([])
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(name) {
    const shouldDelete = window.confirm(`Delete ${name} from the database?`)
    if (!shouldDelete) return

    setError('')
    setDeletingName(name)
    try {
      await deleteCandidate(name)
      setCandidates((prev) => prev.filter((item) => item.name !== name))
    } catch (err) {
      setError(err.message || 'Unable to delete candidate.')
    } finally {
      setDeletingName('')
    }
  }

  return (
    <div className="page-grid">
      <Card title="Candidate Database" subtitle="Read, filter, rank, and delete records.">
        <div className="toolbar">
          <button type="button" className="btn btn-secondary" onClick={fetchAll}>
            Show All
          </button>
          <div className="inline-actions">
            <input
              className="limit-input"
              type="number"
              min="1"
              max="10"
              value={limit}
              onChange={(event) => setLimit(Number(event.target.value))}
            />
            <button type="button" className="btn btn-secondary" onClick={handleTop}>
              Top N
            </button>
          </div>

          <form className="inline-actions grow" onSubmit={handleSearch}>
            <input
              value={searchName}
              onChange={(event) => setSearchName(event.target.value)}
              placeholder="Search by candidate name"
            />
            <button type="submit" className="btn">
              Search
            </button>
          </form>
        </div>

        {error ? <p className="error-text">{error}</p> : null}
        {loading ? (
          <Loader label="Fetching candidates..." />
        ) : (
          <CandidateTable
            candidates={candidates}
            onDelete={handleDelete}
            deletingName={deletingName}
          />
        )}
      </Card>
    </div>
  )
}

export default CandidatesPage
