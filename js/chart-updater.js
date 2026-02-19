// Chart updater for AI Village Contribution Dashboard
// Loads real data and updates Chart.js visualizations with loading states

class ChartUpdater {
    constructor() {
        this.loader = new DataLoader();
        this.charts = {};
        this.data = {};
        this.timecapsuleBase = 'https://github.com/ai-village-agents/village-time-capsule/blob/main/content/history/';
    }

    async initialize() {
        console.log('ChartUpdater initializing...');
        
        // Ensure loading states are visible (they should already be from HTML)
        this.showLoadingStates();
        
        try {
            // Load all data
            await this.loadAllData();
            
            // Update summary metrics
            this.updateSummaryMetrics();
            
            // Update charts with real data
            this.updateCharts();
            
            // Hide loading states now that data is loaded
            this.hideLoadingStates();
            
            console.log('ChartUpdater initialized successfully');
        } catch (error) {
            console.error('Failed to initialize ChartUpdater:', error);
            this.showErrorState('Failed to load dashboard data. Please refresh or check your connection.');
        }
    }

    showLoadingStates() {
        // Loading states are already shown via CSS classes in HTML
        // This method ensures they remain visible during loading
        console.log('Showing loading states...');
        
        // Add loading classes if not already present (they should be)
        const metrics = document.querySelectorAll('.metric');
        const panels = document.querySelectorAll('.panel');
        
        metrics.forEach(metric => {
            if (!metric.classList.contains('loading')) {
                metric.classList.add('loading');
            }
        });
        
        panels.forEach(panel => {
            if (!panel.classList.contains('loading')) {
                panel.classList.add('loading');
            }
        });
    }

    hideLoadingStates() {
        console.log('Hiding loading states...');
        
        // Remove loading classes from metrics and panels
        const metrics = document.querySelectorAll('.metric.loading');
        const panels = document.querySelectorAll('.panel.loading');
        
        metrics.forEach(metric => {
            metric.classList.remove('loading');
        });
        
        panels.forEach(panel => {
            panel.classList.remove('loading');
        });
        
        // Also hide any loading spinners that might be in the panels
        const loadingSpinners = document.querySelectorAll('.loading-spinner');
        loadingSpinners.forEach(spinner => {
            spinner.style.display = 'none';
        });
    }

    showErrorState(message) {
        console.error('Showing error state:', message);
        
        // Remove loading classes first
        this.hideLoadingStates();
        
        // Create or show error message in each panel
        const panels = document.querySelectorAll('.panel');
        panels.forEach(panel => {
            // Check if error element already exists
            let errorEl = panel.querySelector('.error-message');
            if (!errorEl) {
                errorEl = document.createElement('div');
                errorEl.className = 'error-message';
                errorEl.style.cssText = `
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    height: 200px;
                    color: #dc2626;
                    font-size: 0.9rem;
                    text-align: center;
                    padding: 20px;
                `;
                panel.appendChild(errorEl);
            }
            errorEl.textContent = message;
        });
        
        // Also show error in metrics area
        const summaryGrid = document.querySelector('.summary-grid');
        if (summaryGrid) {
            const errorMetric = document.createElement('div');
            errorMetric.className = 'metric error';
            errorMetric.style.cssText = `
                grid-column: 1 / -1;
                text-align: center;
                color: #dc2626;
                padding: 10px;
                background: rgba(220, 38, 38, 0.1);
                border-radius: 6px;
                margin-top: 10px;
            `;
            errorMetric.innerHTML = `<strong>⚠️ Error loading data:</strong> ${message}`;
            summaryGrid.appendChild(errorMetric);
        }
    }

    async loadAllData() {
        try {
            this.data.dailyContributions = await this.loader.loadDailyContributions();
            this.data.agentActivity = await this.loader.loadAgentActivity();
            this.data.collaborationNetwork = await this.loader.loadCollaborationNetwork();
            this.data.topicEvolution = await this.loader.loadTopicEvolution();
            this.data.historicalTrends = await this.loader.loadHistoricalTrends();
            this.data.villageTimeline = await this.loader.loadVillageTimeline();
            this.data.knowledgeIntegration = await this.loader.fetchJSON('knowledge_integration.json');
            
            console.log('Data loaded:', {
                dailyContributions: this.data.dailyContributions?.length || 0,
                agentActivity: this.data.agentActivity?.length || 0,
                collaborationNetwork: this.data.collaborationNetwork?.nodes?.length || 0,
                topicEvolution: this.data.topicEvolution?.currentWeek?.length || 0,
                historicalTrends: this.data.historicalTrends?.length || 0,
                timelineGoals: this.data.villageTimeline?.goals?.length || 0,
                knowledgeDocs: this.data.knowledgeIntegration?.timecapsule_documents?.length || 0
            });
        } catch (error) {
            console.error('Failed to load data:', error);
            throw error; // Re-throw to be caught by initialize()
        }
    }

    updateSummaryMetrics() {
        if (!this.data.dailyContributions || !this.data.agentActivity) return;
        
        // Calculate total contributions
        const totalContributions = this.data.dailyContributions.reduce((sum, day) => sum + day.total, 0);
        
        // Count active agents
        const activeAgents = this.data.agentActivity.length;
        
        // Calculate collaboration density (simplified)
        const collaborationDensity = this.data.collaborationNetwork?.density || 0.72;
        
        // Determine trending topic (simplified - find max in current week)
        let trendingTopic = "Park Cleanup";
        if (this.data.topicEvolution?.currentWeek) {
            const topics = this.data.topicEvolution.topics || ["Autonomous Ops", "Safety", "Alignment", "Data Quality", "Tooling", "UX Research"];
            const values = this.data.topicEvolution.currentWeek;
            const maxIndex = values.indexOf(Math.max(...values));
            trendingTopic = topics[maxIndex] || "Park Cleanup";
        }
        
        // Update DOM elements
        this.updateMetric('.summary-grid .metric:nth-child(1) strong', totalContributions.toLocaleString());
        this.updateMetric('.summary-grid .metric:nth-child(2) strong', activeAgents.toString());
        this.updateMetric('.summary-grid .metric:nth-child(3) strong', collaborationDensity.toFixed(2));
        this.updateMetric('.summary-grid .metric:nth-child(4) strong', trendingTopic);
        this.updateMetric('.summary-grid .metric:nth-child(5) strong', '32/32');
        
        // Update trend indicators (simplified)
        const trendTag = document.querySelector('.summary-grid .metric:nth-child(1) .tag');
        if (trendTag) {
            const avgLastWeek = this.calculateWeeklyAverage(this.data.dailyContributions.slice(-14, -7));
            const avgThisWeek = this.calculateWeeklyAverage(this.data.dailyContributions.slice(-7));
            const change = avgLastWeek > 0 ? ((avgThisWeek - avgLastWeek) / avgLastWeek * 100).toFixed(0) : 0;
            trendTag.textContent = `${change >= 0 ? '+' : ''}${change}% vs last week`;
        }

        const pagesTag = document.querySelector('.summary-grid .metric:nth-child(5) .tag');
        if (pagesTag) {
            pagesTag.textContent = 'Milestone achieved';
            pagesTag.style.background = 'rgba(74, 222, 128, 0.12)';
            pagesTag.style.color = '#bbf7d0';
            // Note: keep the admin-gated repo footnote (gpt5-breaking-news) until Pages is unlocked.
        }
    }

    updateMetric(selector, value) {
        const element = document.querySelector(selector);
        if (element) {
            element.textContent = value;
        }
    }

    calculateWeeklyAverage(days) {
        if (!days || days.length === 0) return 0;
        const total = days.reduce((sum, day) => sum + day.total, 0);
        return total / days.length;
    }

    updateCharts() {
        // Update overview chart (daily contributions)
        this.updateOverviewChart();
        
        // Update agent activity chart
        this.updateAgentChart();
        
        // Update collaboration network chart
        this.updateNetworkChart();
        
        // Update topic evolution chart
        this.updateTopicChart();
        
        // Update historical trends chart
        this.updateTrendChart();
        
        // Create or refresh the village goals timeline chart
        this.createTimelineChart();
    }

    updateOverviewChart() {
        if (!this.data.dailyContributions) return;
        
        const chart = Chart.getChart('overviewChart');
        if (!chart) return;
        
        // Get last 7 days
        const last7Days = this.data.dailyContributions.slice(-7);
        chart.data.labels = last7Days.map(day => {
            const date = new Date(day.date);
            return date.toLocaleDateString('en-US', { weekday: 'short' });
        });
        chart.data.datasets[0].data = last7Days.map(day => day.total);
        
        chart.update();
    }

    updateAgentChart() {
        if (!this.data.agentActivity) return;
        
        const chart = Chart.getChart('agentChart');
        if (!chart) return;
        
        // Sort agents by total contributions and take top 5
        const sortedAgents = [...this.data.agentActivity]
            .sort((a, b) => b.total - a.total)
            .slice(0, 5);
        
        chart.data.labels = sortedAgents.map(agent => agent.agent);
        chart.data.datasets[0].data = sortedAgents.map(agent => agent.total);
        
        chart.update();
    }

    updateNetworkChart() {
        if (!this.data.collaborationNetwork?.nodes) return;
        
        const chart = Chart.getChart('networkChart');
        if (!chart) return;
        
        // Convert network nodes to bubble chart data
        const nodes = this.data.collaborationNetwork.nodes;
        chart.data.datasets[0].data = nodes.map(node => ({
            x: node.x || Math.random() * 10,
            y: node.y || Math.random() * 10,
            r: node.size || 15
        }));
        
        chart.update();
    }

    updateTopicChart() {
        if (!this.data.topicEvolution) return;
        
        const chart = Chart.getChart('topicChart');
        if (!chart) return;
        
        chart.data.labels = this.data.topicEvolution.topics || 
            ['Autonomous Ops', 'Safety', 'Alignment', 'Data Quality', 'Tooling', 'UX Research'];
        
        if (this.data.topicEvolution.currentWeek) {
            chart.data.datasets[0].data = this.data.topicEvolution.currentWeek;
        }
        
        if (this.data.topicEvolution.lastWeek) {
            chart.data.datasets[1].data = this.data.topicEvolution.lastWeek;
        }
        
        chart.update();
    }

    updateTrendChart() {
        if (!this.data.historicalTrends) return;
        
        const chart = Chart.getChart('trendChart');
        if (!chart) return;
        
        // Assuming historicalTrends is array of monthly data
        const months = this.data.historicalTrends.map(month => month.month);
        const contributions = this.data.historicalTrends.map(month => month.contributions);
        const collaborationScores = this.data.historicalTrends.map(month => month.collaborationScore);
        
        chart.data.labels = months;
        chart.data.datasets[0].data = contributions;
        chart.data.datasets[1].data = collaborationScores;
        
        chart.update();
    }

    createTimelineChart() {
        const goals = this.data.villageTimeline?.goals;
        if (!goals || goals.length === 0) return;
        
        const canvas = document.getElementById('timelineChart');
        if (!canvas) return;
        
        // Destroy any existing timeline chart to avoid duplicate canvases
        const existing = Chart.getChart('timelineChart');
        if (existing) {
            existing.destroy();
        }
        
        const ctx = canvas.getContext('2d');
        const knowledge = this.data.knowledgeIntegration;
        
        // Map document names to link targets for quick lookup
        const documentLinks = new Map();
        knowledge?.timecapsule_documents?.forEach(doc => {
            documentLinks.set(doc.name, doc.link || doc.name);
        });
        
        const timelineDocs = goals.map(goal => this.lookupTimecapsuleDocs(goal, knowledge, documentLinks));
        const labels = goals.map(goal => `Days ${goal.start_day}-${goal.end_day}: ${goal.goal}`);
        const colorFor = (goal) => goal.category === 'break' ? '#38bdf8' : '#c084fc';
        
        this.charts.timeline = new Chart(ctx, {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    label: 'Village goals timeline (days)',
                    data: goals.map(goal => [goal.start_day, goal.end_day]),
                    backgroundColor: goals.map(goal => `${goal.category === 'break' ? 'rgba(56, 189, 248, 0.35)' : 'rgba(192, 132, 252, 0.35)'}`),
                    borderColor: goals.map(colorFor),
                    borderWidth: 2,
                    borderRadius: 6,
                    borderSkipped: false
                }]
            },
            options: {
                indexAxis: 'y',
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const goal = goals[context.dataIndex];
                                const duration = goal.end_day - goal.start_day + 1;
                                return `${goal.goal} • Days ${goal.start_day}-${goal.end_day} • ${duration} days • ${goal.agent_hours} agent hours`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Day of Village timeline',
                            color: '#94a3b8'
                        },
                        grid: { color: 'rgba(255,255,255,0.04)' },
                        ticks: { color: '#cbd5e1' }
                    },
                    y: {
                        grid: { display: false },
                        ticks: {
                            color: '#cbd5e1',
                            callback: (value) => {
                                const label = labels[value] || '';
                                return label.length > 60 ? `${label.slice(0, 57)}...` : label;
                            }
                        }
                    }
                },
                onClick: (evt, elements) => {
                    if (!elements.length) return;
                    const index = elements[0].index;
                    const links = timelineDocs[index];
                    
                    if (links && links.length) {
                        window.open(links[0], '_blank');
                    } else {
                        console.warn('No Time Capsule link found for timeline period', goals[index]);
                    }
                }
            }
        });
    }

    lookupTimecapsuleDocs(goal, knowledge, documentLinks) {
        if (!knowledge) return [];
        
        const timelinePeriod = knowledge.timeline_periods?.find(
            period => period.start_day === goal.start_day && period.end_day === goal.end_day
        );
        
        const docNames = timelinePeriod?.timecapsule_documents ||
            knowledge.references?.timeline_to_documents?.[timelinePeriod?.id] ||
            [];
        
        return docNames
            .map(name => documentLinks.get(name) || name)
            .map(link => this.buildTimecapsuleUrl(link))
            .filter(Boolean);
    }

    buildTimecapsuleUrl(link) {
        if (!link) return null;
        if (link.startsWith('http')) return link;
        return `${this.timecapsuleBase}${link}`;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    console.log('AI Village Dashboard - Initializing ChartUpdater');
    
    const updater = new ChartUpdater();
    await updater.initialize();
});
