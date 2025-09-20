import React, { useState } from 'react';

const SearchBar = ({ onScrape, isLoading }) => {
  const [username, setUsername] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onScrape(username);
  };

  return (
    <form onSubmit={handleSubmit} className="search-bar">
      <input
        type="text"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        placeholder="Enter Instagram username (e.g., nike)"
        disabled={isLoading}
      />
      <button type="submit" disabled={isLoading}>
        {isLoading ? 'Scraping...' : 'Scrape Reels'}
      </button>
    </form>
  );
};

export default SearchBar;