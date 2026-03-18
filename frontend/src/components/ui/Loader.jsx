function Loader({ label = 'Loading...' }) {
  return (
    <div className="loader-wrap" role="status" aria-live="polite">
      <span className="loader" />
      <span>{label}</span>
    </div>
  )
}

export default Loader
