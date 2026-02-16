import re

with open('index.html', 'r') as f:
    content = f.read()

# Find the closing script tag and insert timeline chart before it
pattern = r'(    })\(\);\n  </script>\n</body>\n</html>)'

timeline_code = '''
    // Village goals timeline
    (() => {
      const ctx = document.getElementById('timelineChart').getContext('2d');
      gradients.timeline = buildGradient(ctx, 'rgba(192, 132, 252, 0.5)', 'rgba(192, 132, 252, 0.1)');
      
      // Placeholder data - will be replaced by real data loading
      const timelineData = {
        labels: ['Days 1-38', 'Days 39-40', 'Days 41-44', 'Days 45-78', 'Days 79-81'],
        datasets: [{
          label: 'Village Goals',
          data: [5, 1, 2, 8, 1],
          backgroundColor: gradients.timeline,
          borderColor: '#c084fc',
          borderWidth: 2,
          borderRadius: 6,
          borderSkipped: false
        }]
      };
      
      new Chart(ctx, {
        type: 'bar',
        data: timelineData,
        options: {
          indexAxis: 'y',
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: (context) => {
                  const labels = [
                    'Charity fundraising (66 agent hours)',
                    'Reflection period (4 agent hours)',
                    'Identify bugs in AI systems (9 agent hours)',
                    'Write story together (57 agent hours)',
                    'Unsupervised agents (4 agent hours)'
                  ];
                  return labels[context.dataIndex] || 'Goal period';
                }
              }
            }
          },
          scales: {
            x: {
              grid: { color: 'rgba(255,255,255,0.04)' },
              title: {
                display: true,
                text: 'Duration (days)',
                color: '#94a3b8'
              }
            },
            y: {
              grid: { display: false },
              ticks: { color: '#cbd5e1' }
            }
          },
          onClick: (evt, elements) => {
            if (elements.length > 0) {
              const index = elements[0].index;
              const goalUrls = [
                'https://github.com/ai-village-agents/village-time-capsule/tree/main/content/history/village_origins.md',
                'https://github.com/ai-village-agents/village-time-capsule/tree/main/content/history/village_milestones.md',
                'https://github.com/ai-village-agents/village-time-capsule/tree/main/content/history/village_origins.md',
                'https://github.com/ai-village-agents/village-time-capsule/tree/main/content/history/village_origins.md',
                'https://github.com/ai-village-agents/village-time-capsule/tree/main/content/history/village_milestones.md'
              ];
              if (goalUrls[index]) {
                window.open(goalUrls[index], '_blank');
              }
            }
          }
        }
      });
    })();
'''

replacement = timeline_code + r'''    })();
  </script>
</body>
</html>'''

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('index.html', 'w') as f:
    f.write(new_content)

print("Timeline chart added successfully")
