import re

with open('index.html', 'r') as f:
    content = f.read()

# Find the historical-trends panel and insert the new timeline panel after it
# Look for the pattern: </div>\n      </section>
pattern = r'(        <div class="panel loading" id="historical-trends">\n          <h3>Historical Trends</h3>\n          <canvas id="trendChart" aria-label="Historical trends chart" role="img"></canvas>\n        </div>\n      </section>)'

replacement = r'''        <div class="panel loading" id="historical-trends">
          <h3>Historical Trends</h3>
          <canvas id="trendChart" aria-label="Historical trends chart" role="img"></canvas>
        </div>
        <div class="panel loading" id="village-goals-timeline">
          <h3>Village Goals Timeline</h3>
          <canvas id="timelineChart" aria-label="Village goals timeline chart" role="img"></canvas>
          <div class="timeline-info" style="margin-top: 15px; font-size: 0.85rem; color: #94a3b8;">
            <p>Click timeline periods to view corresponding Time Capsule documents and knowledge frameworks</p>
          </div>
        </div>
      </section>'''

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('index.html', 'w') as f:
    f.write(new_content)

print("Timeline panel inserted successfully")
