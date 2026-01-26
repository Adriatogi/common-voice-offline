import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { LanguageProvider } from './utils/LanguageContext'
import Home from './pages/Home'
import UserStats from './pages/UserStats'

function App() {
  return (
    <LanguageProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/stats/*" element={<UserStats />} />
        </Routes>
      </BrowserRouter>
    </LanguageProvider>
  )
}

export default App
