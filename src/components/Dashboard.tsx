import React from 'react';

const Dashboard = () => {
	return (
		<div className="page-card page-card--wide">
			<h1 style={{ fontSize: '2.4rem', marginBottom: '10px' }}>Dashboard</h1>
			<p style={{ color: '#4b5563', fontSize: '1.05rem', marginBottom: '24px' }}>Welcome to your dashboard</p>
			<div style={{ marginTop: '20px', padding: '32px', background: '#f0f0f0', borderRadius: '18px', boxShadow: '0 18px 50px rgba(15,23,42,0.08)' }}>
				<h3 style={{ marginBottom: '16px', fontSize: '1.15rem' }}>Live Metal Prices</h3>
				<p style={{ margin: '12px 0', fontSize: '1.08rem' }}>🥇 Gold: ₹15,260.40 per 10g</p>
				<p style={{ margin: '12px 0', fontSize: '1.08rem' }}>🥈 Silver: ₹253.80 per gram</p>
				<p style={{ margin: '12px 0', fontSize: '1.08rem' }}>🔶 Platinum: ₹6,182.50 per 10g</p>
			</div>
		</div>
	);
};

export default Dashboard;
