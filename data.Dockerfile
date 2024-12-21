FROM alpine:3.18

WORKDIR /data

# Create appuser with same UID/GID as in python-base
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser

# Copy your data directory
COPY data/ .

# Make sure the files are owned by appuser
RUN chown -R appuser:appuser /data

# Use appuser
USER appuser

CMD ["tail", "-f", "/dev/null"]
