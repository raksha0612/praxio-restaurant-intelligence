FROM python:3.13-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml .
RUN uv pip install --system \
    streamlit anthropic plotly matplotlib reportlab \
    pandas numpy openpyxl python-dotenv python-dateutil httpx psycopg2-binary

# Copy root-level Python modules
COPY config.py ./
COPY data_audit.py ./
COPY restaurant_chat.py ./
COPY scoring_engine.py ./
COPY report_generator.py ./
COPY excel_exporter.py ./
COPY translations.py ./
COPY database.py ./

# Copy app source
COPY app/ ./app/

# Streamlit config — headless, port 8502
RUN mkdir -p /app/app/.streamlit
RUN echo '[browser]\ngatherUsageStats = false\n[server]\nheadless = true\nport = 8502\naddress = "0.0.0.0"' \
    > /app/app/.streamlit/config.toml

# Call notes dir (mounted as volume in production)
RUN mkdir -p /app/scripts/data/call_notes /app/app/output/reports

EXPOSE 8502

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8502/_stcore/health || exit 1

CMD ["streamlit", "run", "app/app.py", "--server.port=8502", "--server.address=0.0.0.0"]
