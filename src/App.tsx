import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Topbar from './components/Topbar';
import Dashboard from './components/Dashboard';
import InvestmentAdvisor from './components/InvestmentAdvisor';
import News from './components/News';
import Preferences from './components/Preferences';
import Alerts from './components/Alerts';
import RightSidebar from './components/RightSidebar';
import './styles.css';

const App = () => {
	const [activeSection, setActiveSection] = useState('dashboard');
	const [activeRightTab, setActiveRightTab] = useState('gold');
	const [darkMode, setDarkMode] = useState(false);

	const renderSection = () => {
		const sections = {
			dashboard: <Dashboard />,
			investment: <InvestmentAdvisor />,
			news: <News />,
			preferences: <Preferences />,
			alerts: <Alerts />
		};
		const component = sections[activeSection];
		console.log('Rendering section:', activeSection, component);
		return component || <Dashboard />;
	};

	return (
		<div className={`app ${darkMode ? 'dark' : ''}`}>
			<Sidebar
				activeSection={activeSection}
				setActiveSection={setActiveSection}
				darkMode={darkMode}
				toggleDarkMode={() => setDarkMode(!darkMode)}
			/>
			<div className="main-content">
				<Topbar activeSection={activeSection} setActiveSection={setActiveSection} />
				<div className="content-layout">
					<div className="content">
						{renderSection()}
					</div>
					<RightSidebar activeRightTab={activeRightTab} setActiveRightTab={setActiveRightTab} />
				</div>
			</div>
		</div>
	);
};

export default App;
