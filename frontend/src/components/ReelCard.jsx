import React from 'react';

// Helper function to format large numbers
const formatNumber = (num) => {
  if (num === null || num === undefined) return 'N/A';
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toString();
};


const ReelCard = ({ reel }) => {
  return (
    <div className="reel-card">
      <a href={reel.reel_url} target="_blank" rel="noopener noreferrer" className="thumbnail-container">
        <img src={reel.thumbnail_url} alt={`Reel by ${reel.id}`} loading="lazy" />
        <div className="play-icon">▶</div>
      </a>
      <div className="card-content">
        <p className="caption">
          {reel.caption ? (reel.caption.length > 100 ? `${reel.caption.substring(0, 100)}...` : reel.caption) : <i>No caption</i>}
        </p>
        <div className="stats">
          <span>❤️ {formatNumber(reel.likes)}</span>
          <span>💬 {formatNumber(reel.comments)}</span>
          <span>👁️ {formatNumber(reel.views)}</span>
        </div>
      </div>
    </div>
  );
};

export default ReelCard;