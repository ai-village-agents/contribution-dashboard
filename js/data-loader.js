// Data loader for AI Village Contribution Dashboard
// This demonstrates how to load real data from JSON files

class DataLoader {
    constructor() {
        this.basePath = 'data/';
    }

    async loadDailyContributions() {
        return this.fetchJSON('daily_contributions.json');
    }

    async loadAgentActivity() {
        return this.fetchJSON('agent_activity_real.json');
    }

    async loadCollaborationNetwork() {
        return this.fetchJSON('collaboration_network.json');
    }

    async loadTopicEvolution() {
        return this.fetchJSON('topic_evolution.json');
    }

    async loadHistoricalTrends() {
        return this.fetchJSON('historical_trends.json');
    }

    async loadVillageGoals() {
        return this.fetchJSON('village_goals.json');
    }

    async loadVillageTimeline() {
        return this.fetchJSON('village_timeline.json');
    }

    async fetchJSON(filename) {
        try {
            const response = await fetch(`${this.basePath}${filename}`);
            if (!response.ok) {
                throw new Error(`Failed to load ${filename}: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`Error loading ${filename}:`, error);
            return null;
        }
    }

    // Calculate summary metrics from data
    async calculateSummaryMetrics(agents, dailyContributions, topics, collaborationNetwork) {
        if (!agents || !dailyContributions) return null;

        const totalContributions = dailyContributions.reduce((sum, day) => sum + day.total, 0);
        const activeAgents = agents.length;

        // Calculate collaboration density from collaboration network data
        let collaborationDensity = 0;

        if (collaborationNetwork && Array.isArray(collaborationNetwork.edges) && collaborationNetwork.edges.length > 0) {
            const edges = collaborationNetwork.edges;
            const nodesFromData = Array.isArray(collaborationNetwork.nodes) ? collaborationNetwork.nodes : [];
            const nodeIds = new Set(
                nodesFromData.map((node) => node.id).filter(Boolean)
            );

            // Fall back to deriving node count from edges if nodes array is missing
            edges.forEach((edge) => {
                if (edge?.source) nodeIds.add(edge.source);
                if (edge?.target) nodeIds.add(edge.target);
            });

            const nodeCount = nodeIds.size;
            const maxPossibleEdges = nodeCount > 1 ? (nodeCount * (nodeCount - 1)) / 2 : 0;
            const totalEdgeWeight = edges.reduce(
                (sum, edge) => sum + (typeof edge.weight === 'number' ? edge.weight : 0),
                0
            );

            if (maxPossibleEdges > 0) {
                // Normalize by maximum possible edges and assumed max weight of 20
                collaborationDensity = totalEdgeWeight / (maxPossibleEdges * 20);
            }
        }

        let trendingTopic = 'N/A';

        if (Array.isArray(topics) && topics.length > 0) {
            const validEntries = topics
                .map((entry) => ({
                    ...entry,
                    endDate: entry?.period_end ? new Date(entry.period_end) : null
                }))
                .filter((entry) => entry.endDate instanceof Date && !isNaN(entry.endDate) && typeof entry.volume === 'number');

            if (validEntries.length > 0) {
                const latestEndDate = validEntries.reduce((latest, entry) =>
                    entry.endDate > latest ? entry.endDate : latest,
                    validEntries[0].endDate
                );

                const latestTopics = validEntries.filter((entry) => entry.endDate.getTime() === latestEndDate.getTime());
                const topEntry = latestTopics.reduce((top, entry) =>
                    entry.volume > (top?.volume ?? -Infinity) ? entry : top,
                    null
                );

                trendingTopic = topEntry?.topic ?? trendingTopic;
            }
        }

        return {
            totalContributions,
            activeAgents,
            collaborationDensity,
            trendingTopic
        };
    }
}

// Initialize and load data when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    console.log('AI Village Dashboard - Data Loader Initialized');

    const loader = new DataLoader();

    const metricCards = Array.from(document.querySelectorAll('.summary-grid .metric'));
    const setMetric = (index, value, tagText) => {
        const card = metricCards[index];
        if (!card) return;

        card.classList.remove('loading');

        const strong = card.querySelector('strong');
        if (strong) {
            strong.textContent = value ?? 'N/A';
        }

        if (tagText) {
            const tag = card.querySelector('.tag');
            if (tag) {
                tag.textContent = tagText;
            }
        }
    };

    const showUnavailable = (message = 'Data unavailable') => {
        metricCards.forEach((card) => {
            card.classList.remove('loading');
            const strong = card.querySelector('strong');
            if (strong) strong.textContent = 'N/A';
            const tag = card.querySelector('.tag');
            if (tag) tag.textContent = message;
        });
    };

    try {
        const [agents, daily, topics, collaborationNetwork] = await Promise.all([
            loader.loadAgentActivity(),
            loader.loadDailyContributions(),
            loader.loadTopicEvolution(),
            loader.loadCollaborationNetwork()
        ]);

        if (!agents || !daily) {
            showUnavailable();
            return;
        }

        const metrics = await loader.calculateSummaryMetrics(agents, daily, topics, collaborationNetwork);
        if (!metrics) {
            showUnavailable('Metrics unavailable');
            return;
        }

        const lastTwoWeeks = daily.slice(-14);
        const lastWeek = lastTwoWeeks.slice(-7);
        const priorWeek = lastTwoWeeks.slice(0, 7);
        const weeklyAverage = (days) => days.length
            ? days.reduce((sum, day) => sum + (day.total || 0), 0) / days.length
            : 0;

        const avgLastWeek = weeklyAverage(lastWeek);
        const avgPriorWeek = weeklyAverage(priorWeek);
        const change = avgPriorWeek > 0 ? ((avgLastWeek - avgPriorWeek) / avgPriorWeek) * 100 : 0;
        const changeLabel = `${change >= 0 ? '+' : ''}${Math.round(change)}% vs last week`;

        setMetric(0, metrics.totalContributions.toLocaleString(), changeLabel);
        setMetric(1, metrics.activeAgents.toString(), 'Currently contributing');
        setMetric(2, (Number.isFinite(metrics.collaborationDensity) ? metrics.collaborationDensity : 0).toFixed(2), 'Collaboration health');
        setMetric(3, metrics.trendingTopic, 'Top mentioned topic');

        console.log('Loaded metrics:', metrics);
    } catch (error) {
        console.error('Error loading metrics:', error);
        showUnavailable();
    }
});
