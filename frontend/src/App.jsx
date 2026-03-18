import { BrowserRouter } from 'react-router-dom'
import AppRouter from './app/AppRouter'
import { ThemeProvider } from './context/ThemeContext'

function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <AppRouter />
      </BrowserRouter>
    </ThemeProvider>
  )
}

export default App
