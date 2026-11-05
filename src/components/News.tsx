import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';

interface NewsArticle {
	title: string;
	description: string;
	source: string;
	news_url: string;
	published_at: string;
}

const News = () => {
	const [articles, setArticles] = useState<NewsArticle[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [lastUpdated, setLastUpdated] = useState<string>(new Date().toLocaleTimeString());

	// Function to fetch news from API
	const fetchNews = async () => {
		try {
			setLoading(true);
			setError(null);
			const response = await apiClient.get('/news?limit=15');
			
			if (response.success && response.data) {
				setArticles(response.data);
				setLastUpdated(new Date().toLocaleTimeString());
				console.log('📰 News fetched successfully:', response.data.length, 'articles');
			} else {
				setError('Failed to fetch news');
			}
		} catch (err) {
			console.error('News fetch error:', err);
			setError('Error fetching news articles');
		} finally {
			setLoading(false);
		}
	};

	// useEffect to fetch news on component mount and set up interval
	useEffect(() => {
		// Fetch immediately on mount
		fetchNews();

		// Set up interval to refresh every 60 minutes (3600000 ms)
		const intervalId = setInterval(() => {
			console.log('🔄 Auto-refreshing news (60-min interval)...');
			fetchNews();
		}, 3600000); // 60 minutes

		// Cleanup interval on component unmount
		return () => clearInterval(intervalId);
	}, []);

	return (
		<div className="page-card page-card--wide">
			<h1 style={{ fontSize: '2.4rem', marginBottom: '10px' }}>📰 Market News</h1>
			<p style={{ color: '#4b5563', fontSize: '1.05rem', marginBottom: '8px' }}>
				Live global metals & currency market news
			</p>
			<p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '20px' }}>
				Last updated: {lastUpdated} | Auto-refresh: Every 60 minutes
			</p>

			{loading && articles.length === 0 && (
				<div style={{
					padding: '32px',
					textAlign: 'center',
					background: '#f0f0f0',
					borderRadius: '12px',
					marginTop: '20px'
				}}>
					<p style={{ fontSize: '1.1rem', color: '#666' }}>⏳ Loading news articles...</p>
				</div>
			)}

			{error && (
				<div style={{
					padding: '16px',
					background: '#ffe6e6',
					color: '#d00',
					borderRadius: '8px',
					marginTop: '12px',
					borderLeft: '4px solid #d00'
				}}>
					⚠️ {error}
				</div>
			)}

			{articles.length > 0 && (
				<div style={{
					display: 'grid',
					gap: '16px',
					marginTop: '20px'
				}}>
					{articles.map((article, idx) => (
						<div
							key={idx}
							style={{
								padding: '16px',
								background: '#fff',
								border: '1px solid #e0e0e0',
								borderRadius: '8px',
								boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
								transition: 'all 0.3s ease',
								cursor: 'pointer',
								hover: 'transform: translateY(-2px)'
							}}
							onMouseOver={(e) => {
								(e.currentTarget as HTMLDivElement).style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
								(e.currentTarget as HTMLDivElement).style.transform = 'translateY(-2px)';
							}}
							onMouseOut={(e) => {
								(e.currentTarget as HTMLDivElement).style.boxShadow = '0 2px 4px rgba(0,0,0,0.05)';
								(e.currentTarget as HTMLDivElement).style.transform = 'translateY(0)';
							}}
						>
							<h3 style={{
								margin: '0 0 8px 0',
								fontSize: '1.1rem',
								color: '#1a1a1a',
								fontWeight: '600'
							}}>
								{article.title}
							</h3>

							{article.description && (
								<p style={{
									margin: '0 0 10px 0',
									fontSize: '0.95rem',
									color: '#555',
									lineHeight: '1.5'
								}}>
									{article.description}
								</p>
							)}

							<div style={{
								display: 'flex',
								justifyContent: 'space-between',
								alignItems: 'center',
								fontSize: '0.85rem',
								color: '#888',
								marginTop: '10px'
							}}>
								<span style={{ fontWeight: '500' }}>📌 {article.source}</span>
								<span>{new Date(article.published_at).toLocaleDateString()} {new Date(article.published_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
							</div>

							{article.news_url && article.news_url !== '#' && (
								<a
									href={article.news_url}
									target="_blank"
									rel="noopener noreferrer"
									style={{
										display: 'inline-block',
										marginTop: '10px',
										color: '#0066cc',
										textDecoration: 'none',
										fontSize: '0.9rem',
										fontWeight: '500'
									}}
									onMouseOver={(e) => (e.currentTarget.style.textDecoration = 'underline')}
									onMouseOut={(e) => (e.currentTarget.style.textDecoration = 'none')}
								>
									🔗 Read Full Article →
								</a>
							)}
						</div>
					))}
				</div>
			)}

			{!loading && articles.length === 0 && !error && (
				<div style={{
					padding: '32px',
					textAlign: 'center',
					background: '#f9f9f9',
					borderRadius: '12px',
					marginTop: '20px',
					color: '#666'
				}}>
					<p>📭 No news articles available at the moment.</p>
					<p style={{ fontSize: '0.9rem', marginTop: '8px' }}>Check back later or wait for the next update.</p>
				</div>
			)}

			{/* Manual refresh button for testing */}
			<button
				onClick={fetchNews}
				disabled={loading}
				style={{
					marginTop: '20px',
					padding: '10px 16px',
					background: loading ? '#ccc' : '#0066cc',
					color: 'white',
					border: 'none',
					borderRadius: '6px',
					cursor: loading ? 'not-allowed' : 'pointer',
					fontSize: '0.95rem',
					fontWeight: '500',
					transition: 'all 0.3s ease'
				}}
				onMouseOver={(e) => {
					if (!loading) {
						(e.currentTarget as HTMLButtonElement).style.background = '#0052a3';
						(e.currentTarget as HTMLButtonElement).style.transform = 'scale(1.02)';
					}
				}}
				onMouseOut={(e) => {
					if (!loading) {
						(e.currentTarget as HTMLButtonElement).style.background = '#0066cc';
						(e.currentTarget as HTMLButtonElement).style.transform = 'scale(1)';
					}
				}}
			>
				{loading ? '⏳ Refreshing...' : '🔄 Refresh News Now'}
			</button>
		</div>
	);
};

export default News;
