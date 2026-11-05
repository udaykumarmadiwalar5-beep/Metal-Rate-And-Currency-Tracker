import React from 'react';

const Preferences = () => {
	return (
		<div>
			<h1>Preferences</h1>
			<p>Manage your preferences</p>
			<div style={{ marginTop: '20px', padding: '15px', background: '#f0f0f0', borderRadius: '8px' }}>
				<label><input type="checkbox" defaultChecked /> Email Notifications</label><br/>
				<label><input type="checkbox" defaultChecked /> Price Alerts</label>
			</div>
		</div>
	);
};

export default Preferences;
