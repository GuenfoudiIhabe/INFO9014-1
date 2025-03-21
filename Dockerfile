FROM python:3.9-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir pandas psycopg2-binary tqdm tabulate

# Copy the application files
COPY . /app/

# Create a wrapper script to handle database connections
RUN echo '#!/bin/bash\n\
sed -i "s/host=\"localhost\"/host=\"$DB_HOST\"/g" src/scripts/load_data.py\n\
sed -i "s/host=\"localhost\"/host=\"$DB_HOST\"/g" src/scripts/run_queries.py\n\
python src/scripts/load_data.py && python src/scripts/run_queries.py\n' > /app/entrypoint.sh && \
chmod +x /app/entrypoint.sh

# Set the entrypoint command to use the wrapper script
CMD ["/app/entrypoint.sh"]
