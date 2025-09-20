import { useState } from 'react';
import axios from 'axios';
import Header from './components/Header';
import SearchBar from './components/SearchBar';
import ReelCard from './components/ReelCard';
import Loader from './components/Loader';
import ErrorMessage from './components/ErrorMessage';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [reels, setReels] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [profile, setProfile] = useState(null);

  const handleScrape = async (username) => {
    if (!username) {
      setError('Please enter a username.');
      return;
    }
    setIsLoading(true);
    setError('');
    setReels([]);
    setProfile(null);

    try {
      const response = await axios.get(`${API_URL}/scrape`, {
        params: {
          username: username,
          limit: 30
        },
      });
      setReels(response.data.reels);
      setProfile({
        username: response.data.username,
        count: response.data.count,
      });
    } catch (err) {
      const detail = err.response?.data?.detail || 'Failed to scrape. The profile might be private, non-existent, or an API error occurred.';
      setError(detail);
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container">
      <Header />
      <SearchBar onScrape={handleScrape} isLoading={isLoading} />

      {isLoading && <Loader />}
      {error && <ErrorMessage message={error} />}

      {profile && (
        <div className="profile-header">
          <h2>
            Reels from <a href={`https://instagram.com/${profile.username}`} target="_blank" rel="noopener noreferrer">@{profile.username}</a>
          </h2>
          <p>Found {profile.count} reels.</p>
        </div>
      )}

      <div className="reels-grid">
        {reels.map((reel) => (
          <ReelCard key={reel.id} reel={reel} />
        ))}
      </div>
    </div>
  );
}

export default App;