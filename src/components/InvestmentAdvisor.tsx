import React, { useState, useEffect } from 'react';

type Company = {
	id: string;
	name: string;
	ticker: string;
	sector: string;
	risk: string;
	expectedReturn: number; // percent
};

const initialCompanies: Company[] = [
	{ id: 'hdfc', name: 'HDFC Bank Ltd', ticker: 'HDFCBANK', sector: 'Banking', risk: 'Low', expectedReturn: 11.8 },
	{ id: 'infy', name: 'Infosys Ltd', ticker: 'INFY', sector: 'IT', risk: 'Low', expectedReturn: 13.2 },
	{ id: 'reliance', name: 'Reliance Industries', ticker: 'RELIANCE', sector: 'Energy', risk: 'Low', expectedReturn: 15.4 },
	{ id: 'axis', name: 'Axis Bank Ltd', ticker: 'AXISBANK', sector: 'Banking', risk: 'Medium', expectedReturn: 10.5 },
	{ id: 'icici', name: 'ICICI Bank Ltd', ticker: 'ICICIBANK', sector: 'Banking', risk: 'Medium', expectedReturn: 12.8 },
];

const InvestmentAdvisor: React.FC = () => {
	const [companies] = useState<Company[]>(initialCompanies);
	const [selected, setSelected] = useState<string[]>([]);
	const [profileCount, setProfileCount] = useState<number>(2);
	const [profileName, setProfileName] = useState<string>('My Profile');
	const [step, setStep] = useState<number>(1); // 1: select, 2: profile details, 3: results
	const [showResults, setShowResults] = useState(false);

	const toggleSelect = (id: string) => {
		setShowResults(false);
		setSelected(prev => (prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]));
	};

	const handleProfileCountChange = (value: number) => {
		if (value < 1) value = 1;
		if (value > selected.length) value = selected.length;
		setProfileCount(value);
	};

	const onNext = () => {
		if (selected.length === 0) return alert('Please select at least one company');
		if (step === 1) {
			// move to profile details
			if (selected.length <= 2) setProfileCount(selected.length);
			else if (profileCount > selected.length) setProfileCount(selected.length);
			setStep(2);
			setShowResults(false);
			return;
		}

		if (step === 2) {
			// finalize and show results
			if (selected.length <= 2) setProfileCount(selected.length);
			else if (profileCount > selected.length) setProfileCount(selected.length);
			setShowResults(true);
			setStep(3);
		}
	};

	const onBack = () => {
		setShowResults(false);
		if (step > 1) setStep(step - 1);
	};

	const saveProfile = (continueAfterSave = false) => {
		const payload = { selected, profileCount, profileName, timestamp: Date.now() };
		try {
			window.localStorage.setItem('investmentAdvisorProfile', JSON.stringify(payload));
			if (continueAfterSave) {
				alert('Profile saved. You can continue later.');
			}
		} catch (err) {
			console.error('Save failed', err);
			alert('Failed to save profile');
		}
	};

	useEffect(() => {
		// load saved profile if present
		try {
			const raw = window.localStorage.getItem('investmentAdvisorProfile');
			if (raw) {
				const parsed = JSON.parse(raw);
				if (parsed && parsed.selected) {
					setSelected(parsed.selected);
					setProfileCount(parsed.profileCount || 2);
					setProfileName(parsed.profileName || 'My Profile');
					// restore to profile details step so user can continue
					setStep(2);
				}
			}
		} catch (err) {
			// ignore parse errors
		}
	}, []);

	const selectedCompanies = companies.filter(c => selected.includes(c.id));

	// When more than 2 selected, show top-N by expectedReturn according to profileCount
	const resultCompanies = showResults
		? selectedCompanies
			  .slice()
			  .sort((a, b) => b.expectedReturn - a.expectedReturn)
			  .slice(0, Math.max(1, profileCount))
		: [];

	return (
		<div className="page-card page-card--wide">
			<h1 style={{ color: '#000', fontSize: '2.3rem', marginBottom: '8px' }}>Investment Advisor</h1>
			<p style={{ color: '#333', fontSize: '1.1rem', marginBottom: '12px' }}>Select one or more companies to get personalized suggestions.</p>

			<div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '8px' }}>
				<div style={{ fontSize: '0.95rem' }}><strong>Selected:</strong> {selected.length}</div>

				{step === 2 && (
					<div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
						<div style={{ fontSize: '0.95rem' }}>
							<label style={{ marginRight: 8 }}>Profile name:</label>
							<input value={profileName} onChange={e => setProfileName(e.target.value)} style={{ padding: '6px 8px', borderRadius: 6 }} />
						</div>

						{selected.length > 2 && (
							<div style={{ fontSize: '0.95rem' }}>
								<label style={{ marginRight: 8 }}>Profile companies:</label>
								<input
									type="number"
									min={1}
									max={selected.length}
									value={profileCount}
									onChange={e => handleProfileCountChange(Number(e.target.value))}
									style={{ width: 72, padding: '6px 8px', borderRadius: 6 }}
								/>
								<span style={{ marginLeft: 8, color: '#666' }}>(Will show top N by expected return)</span>
							</div>
						)}
					</div>
				)}

				<div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
					<button onClick={() => saveProfile(true)} style={{ background: '#eee', border: '1px solid #ddd', padding: '8px 12px', borderRadius: 8, cursor: 'pointer' }}>Save</button>
					<button onClick={onBack} disabled={step===1} style={{ background: '#fff', border: '1px solid #ddd', padding: '8px 12px', borderRadius: 8, cursor: step===1 ? 'not-allowed' : 'pointer' }}>Back</button>
					<button onClick={onNext} style={{ background: '#d4af37', border: 'none', padding: '8px 14px', borderRadius: 8, cursor: 'pointer' }}>{step===2 ? 'Continue → Results' : 'Next → Profile Details'}</button>
				</div>
			</div>

			<div style={{ marginTop: '8px', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px' }}>
				{companies.map(c => {
					const isSelected = selected.includes(c.id);
					return (
						<div
							key={c.id}
							onClick={() => toggleSelect(c.id)}
							role="button"
							tabIndex={0}
							onKeyDown={e => {
								if (e.key === 'Enter' || e.key === ' ') {
									e.preventDefault();
									toggleSelect(c.id);
								}
							}}
							style={{ background: isSelected ? '#fff8e1' : '#f5f5f5', padding: '16px', borderRadius: '12px', borderLeft: `4px solid ${isSelected ? '#ffd700' : '#eee'}`, minHeight: '140px', cursor: 'pointer' }}>
							<div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
								<h3 style={{ color: '#000', margin: '0 0 8px 0', fontSize: '1.05rem' }}>{c.name}</h3>
								<input
									type="checkbox"
									checked={isSelected}
									onChange={e => { e.stopPropagation(); toggleSelect(c.id); }}
									onClick={e => e.stopPropagation()}
								/>
							</div>
							<p style={{ color: '#555', margin: '4px 0' }}>Ticker: {c.ticker}</p>
							<p style={{ color: '#555', margin: '4px 0' }}>Sector: {c.sector}</p>
							<p style={{ color: '#555', margin: '4px 0' }}>Risk: {c.risk}</p>
							<p style={{ color: '#555', margin: '4px 0' }}>Expected Return: {c.expectedReturn}%</p>
						</div>
					);
				})}
			</div>

			{showResults && step===3 && (
				<div style={{ marginTop: '24px', background: '#ffffff', padding: '18px', borderRadius: 12, boxShadow: '0 1px 3px rgba(0,0,0,0.06)' }}>
					<h2 style={{ marginTop: 0 }}>Profile Results</h2>
					{selectedCompanies.length === 0 && <p>No companies selected.</p>}

					{selectedCompanies.length > 0 && (
						<>
							<p style={{ color: '#444' }}>Showing results for top <strong>{Math.max(1, Math.min(profileCount, selectedCompanies.length))}</strong> company(ies) from your selection.</p>

							<div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '12px', marginTop: '12px' }}>
								{resultCompanies.map(c => (
									<div key={c.id} style={{ background: '#f9f9f9', padding: '12px', borderRadius: 10 }}>
										<h4 style={{ margin: '0 0 8px 0' }}>{c.name} <span style={{ color: '#999', fontSize: '0.85rem' }}>({c.ticker})</span></h4>
										<p style={{ margin: '6px 0', color: '#555' }}>Sector: {c.sector}</p>
										<p style={{ margin: '6px 0', color: '#555' }}>Risk: {c.risk}</p>
										<p style={{ margin: '6px 0', color: '#555' }}>Expected Return: {c.expectedReturn}%</p>
									</div>
								))}
							</div>
						</>
					)}
				</div>
			)}
			{step !== 3 && (
				<div style={{ marginTop: 12, color: '#666' }}>
					<small>Step {step} of 3</small>
				</div>
			)}
		</div>
	);
};

export default InvestmentAdvisor;