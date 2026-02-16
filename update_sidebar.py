import re

with open('index.html', 'r') as f:
    content = f.read()

# Add Village Goals Timeline to Dashboard navigation
pattern = r'(<div class="nav-title">Dashboard</div>\n        <nav class="nav-links">\n          <a href="#overview">Overview</a>\n          <a href="#agent-activity">Agent Activity</a>\n          <a href="#collaboration-network">Collaboration Network</a>\n          <a href="#topic-evolution">Topic Evolution</a>\n          <a href="#historical-trends">Historical Trends</a>\n        </nav>)'

replacement = r'''<div class="nav-title">Dashboard</div>
        <nav class="nav-links">
          <a href="#overview">Overview</a>
          <a href="#agent-activity">Agent Activity</a>
          <a href="#collaboration-network">Collaboration Network</a>
          <a href="#topic-evolution">Topic Evolution</a>
          <a href="#historical-trends">Historical Trends</a>
          <a href="#village-goals-timeline">Village Goals Timeline</a>
        </nav>'''

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('index.html', 'w') as f:
    f.write(new_content)

print("Sidebar updated successfully")
