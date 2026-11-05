// Example: How to Use NewsAPI in Your React Components

// ===================================================================
// EXAMPLE 1: Update News.tsx to display real market news
// ===================================================================

import React, { useEffect, useState } from 'react';

const News = () => {
	const [news, setNews] = useState([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState(null);

	useEffect(() => {
		fetchNews();
		// Refresh news every 5 minutes
		const interval = setInterval(fetchNews, 5 * 60 * 1000);
		return () => clearInterval(interval);
	}, []);

	const fetchNews = async () => {
		try {
			setLoading(true);
			const response = await fetch('/api/news');
			const data = await response.json();
			
			if (data.success) {
				setNews(data.data);
				setError(null);
			} else {
				setError('Failed to load news');
			}
		} catch (err) {
			setError('Error fetching news: ' + err.message);
			console.error(err);
		} finally {
			setLoading(false);
		}
	};

	if (loading) {
		return <div style={{ padding: '20px' }}>📰 Loading latest market news...</div>;
	}

	if (error) {
		return <div style={{ padding: '20px', color: 'red' }}>❌ {error}</div>;
	}

	return (
		<div style={{ padding: '20px' }}>
			<h1>📰 Latest Market News</h1>
			<p style={{ color: '#666' }}>Global news about Gold, Silver, Platinum & Currency Markets</p>
			
			{news.length === 0 ? (
				<p style={{ marginTop: '20px', color: '#999' }}>
					No news articles found. Check back soon!
				</p>
			) : (
				<div style={{ marginTop: '20px' }}>
					{news.map((article) => (
						<div
							key={article.news_id}
							style={{
								border: '1px solid #ddd',
								borderRadius: '8px',
								padding: '15px',
								marginBottom: '15px',
								backgroundColor: '#f9f9f9',
								transition: 'all 0.3s ease'
							}}
							onMouseEnter={(e) => {
								e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
								e.currentTarget.style.transform = 'translateY(-2px)';
							}}
							onMouseLeave={(e) => {
								e.currentTarget.style.boxShadow = 'none';
								e.currentTarget.style.transform = 'translateY(0)';
							}}
						>
							<h3 style={{ margin: '0 0 10px 0', color: '#333' }}>
								{article.title}
							</h3>
							
							<p style={{ margin: '10px 0', color: '#666', fontSize: '14px' }}>
								{article.description || 'No description available'}
							</p>
							
							<div style={{
								display: 'flex',
								justifyContent: 'space-between',
								alignItems: 'center',
								marginTop: '15px',
								fontSize: '12px',
								color: '#999'
							}}>
								<div>
									<span style={{ marginRight: '15px' }}>
										📌 <strong>{article.source}</strong>
									</span>
									<span>
										🕐 {new Date(article.published_at).toLocaleDateString()} 
										{' '}{new Date(article.published_at).toLocaleTimeString()}
									</span>
								</div>
								<a
									href={article.news_url}
									target="_blank"
									rel="noopener noreferrer"
									style={{
										padding: '6px 12px',
										backgroundColor: '#007bff',
										color: 'white',
										textDecoration: 'none',
										borderRadius: '4px',
										fontSize: '12px'
									}}
								>
									Read More →
								</a>
							</div>
						</div>
					))}
				</div>
			)}
		</div>
	);
};

export default News;


// ===================================================================
// EXAMPLE 2: Add News Widget to Dashboard
// ===================================================================

import React, { useEffect, useState } from 'react';

const DashboardNews = () => {
	const [topNews, setTopNews] = useState([]);

	useEffect(() => {
		fetchTopNews();
	}, []);

	const fetchTopNews = async () => {
		try {
			const response = await fetch('/api/news');
			const data = await response.json();
			if (data.success) {
				// Get top 3 most recent news
				setTopNews(data.data.slice(0, 3));
			}
		} catch (err) {
			console.error('Failed to fetch news:', err);
		}
	};

	return (
		<div style={{
			backgroundColor: '#fff',
			borderRadius: '8px',
			padding: '20px',
			marginTop: '20px',
			boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
		}}>
			<h2 style={{ marginTop: '0' }}>📰 Latest Market News</h2>
			
			<div style={{ maxHeight: '400px', overflowY: 'auto' }}>
				{topNews.map((article) => (
					<div key={article.news_id} style={{
						borderLeft: '4px solid #FFD700',
						paddingLeft: '12px',
						marginBottom: '15px',
						paddingBottom: '15px',
						borderBottom: '1px solid #f0f0f0'
					}}>
						<h4 style={{ margin: '0 0 5px 0', fontSize: '14px' }}>
							{article.title.substring(0, 60)}...
						</h4>
						<p style={{ margin: '5px 0', fontSize: '12px', color: '#666' }}>
							{article.source} • {new Date(article.published_at).toLocaleDateString()}
						</p>
						<a href={article.news_url} target="_blank" rel="noopener noreferrer" 
						   style={{ color: '#007bff', fontSize: '12px' }}>
							Read full article →
						</a>
					</div>
				))}
			</div>
			
			<a href="/news" style={{
				display: 'block',
				marginTop: '15px',
				textAlign: 'center',
				color: '#007bff',
				textDecoration: 'none',
				fontWeight: 'bold'
			}}>
				View All News →
			</a>
		</div>
	);
};

export default DashboardNews;


// ===================================================================
// EXAMPLE 3: News Filter Component
// ===================================================================

import React, { useEffect, useState } from 'react';

const FilteredNews = () => {
	const [news, setNews] = useState([]);
	const [filteredNews, setFilteredNews] = useState([]);
	const [selectedFilter, setSelectedFilter] = useState('all');

	const filters = [
		{ value: 'all', label: '📰 All News' },
		{ value: 'gold', label: '🥇 Gold News' },
		{ value: 'silver', label: '🥈 Silver News' },
		{ value: 'platinum', label: '🏆 Platinum News' },
		{ value: 'currency', label: '💱 Currency News' },
		{ value: 'forex', label: '📊 Forex News' }
	];

	useEffect(() => {
		fetchNews();
	}, []);

	useEffect(() => {
		filterNews(selectedFilter);
	}, [news, selectedFilter]);

	const fetchNews = async () => {
		try {
			const response = await fetch('/api/news');
			const data = await response.json();
			if (data.success) {
				setNews(data.data);
			}
		} catch (err) {
			console.error('Failed to fetch news:', err);
		}
	};

	const filterNews = (filter) => {
		if (filter === 'all') {
			setFilteredNews(news);
		} else {
			const filtered = news.filter(article => 
				article.title.toLowerCase().includes(filter) ||
				article.description?.toLowerCase().includes(filter)
			);
			setFilteredNews(filtered);
		}
		setSelectedFilter(filter);
	};

	return (
		<div>
			<div style={{ marginBottom: '20px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
				{filters.map(filter => (
					<button
						key={filter.value}
						onClick={() => filterNews(filter.value)}
						style={{
							padding: '8px 16px',
							border: selectedFilter === filter.value ? '2px solid #FFD700' : '1px solid #ddd',
							backgroundColor: selectedFilter === filter.value ? '#fff8dc' : '#fff',
							borderRadius: '20px',
							cursor: 'pointer',
							fontSize: '14px',
							fontWeight: selectedFilter === filter.value ? 'bold' : 'normal'
						}}
					>
						{filter.label}
					</button>
				))}
			</div>

			<div>
				<p style={{ color: '#666', marginBottom: '15px' }}>
					📊 Showing {filteredNews.length} article(s) for "{selectedFilter}"
				</p>
				
				{filteredNews.length === 0 ? (
					<p style={{ color: '#999', padding: '20px', textAlign: 'center' }}>
						No articles found for this category
					</p>
				) : (
					filteredNews.map(article => (
						<NewsCard key={article.news_id} article={article} />
					))
				)}
			</div>
		</div>
	);
};

const NewsCard = ({ article }) => (
	<div style={{
		border: '1px solid #ddd',
		borderRadius: '8px',
		padding: '15px',
		marginBottom: '15px',
		backgroundColor: '#fafafa'
	}}>
		<h3 style={{ margin: '0 0 10px 0' }}>{article.title}</h3>
		<p style={{ margin: '10px 0', color: '#666' }}>
			{article.description}
		</p>
		<div style={{
			display: 'flex',
			justifyContent: 'space-between',
			alignItems: 'center',
			marginTop: '10px',
			fontSize: '12px',
			color: '#999'
		}}>
			<span>{article.source} • {new Date(article.published_at).toLocaleDateString()}</span>
			<a href={article.news_url} target="_blank" rel="noopener noreferrer" 
			   style={{ color: '#007bff', fontWeight: 'bold' }}>
				Read More
			</a>
		</div>
	</div>
);

export default FilteredNews;


// ===================================================================
// EXAMPLE 4: Hook for Easy News Fetching
// ===================================================================

// useNews.js
import { useState, useEffect } from 'react';

const useNews = (refreshInterval = 5 * 60 * 1000) => {
	const [news, setNews] = useState([]);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState(null);

	const fetchNews = async () => {
		try {
			setLoading(true);
			const response = await fetch('/api/news');
			const data = await response.json();
			if (data.success) {
				setNews(data.data);
				setError(null);
			} else {
				setError(data.error || 'Failed to fetch news');
			}
		} catch (err) {
			setError(err.message);
		} finally {
			setLoading(false);
		}
	};

	useEffect(() => {
		fetchNews();
		const interval = setInterval(fetchNews, refreshInterval);
		return () => clearInterval(interval);
	}, [refreshInterval]);

	return { news, loading, error, refetch: fetchNews };
};

export default useNews;

// Usage in component:
// const { news, loading, error } = useNews();


// ===================================================================
// NOTES
// ===================================================================

/*
To use these components:

1. Update src/components/News.tsx with EXAMPLE 1 code

2. Import and use in Dashboard:
   import DashboardNews from './DashboardNews';
   <DashboardNews />

3. Create useNews hook:
   Create file: src/hooks/useNews.js
   Copy EXAMPLE 4 code

4. Use hook in any component:
   import useNews from '../hooks/useNews';
   const { news, loading, error } = useNews();

Backend API:
- GET /api/news - Returns all news articles
  Response: { success: true, data: [...articles] }

Each article has:
- news_id: Unique identifier
- title: Article headline
- description: Article summary
- source: News source name
- news_url: Full article URL (clickable)
- published_at: Publication date/time
- fetched_at: When article was added to our DB
*/
