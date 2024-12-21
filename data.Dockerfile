FROM alpine:3.18

WORKDIR /data

# Add user with same UID/GID as other containers
RUN addgroup -g 1000 appgroup && \
    adduser -u 1000 -G appgroup -s /bin/sh -D appuser

# Create directories first
RUN mkdir -p /data/market_data /data/cache /data/portfolios

# Copy data files
COPY --chown=1000:1000 data/ .

# Set permissions for shared access and verify
RUN chown -R 1000:1000 /data && \
    chmod -R 775 /data && \
    chmod g+s /data /data/market_data /data/cache /data/portfolios && \
    echo "Verifying permissions:" && \
    ls -ln /data

USER 1000:1000

# Add permission check to startup
CMD ls -ln /data && echo "Running as: $(id)" && tail -f /dev/null
