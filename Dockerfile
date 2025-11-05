# ============================================================================
# Multi-stage Dockerfile for Sentiment Finance Lambda Function
# Optimized for AWS Lambda deployment with minimal image size
# ============================================================================

# Build stage - includes all build dependencies
FROM public.ecr.aws/lambda/python:3.11 as builder

# Set working directory
WORKDIR /app

# Install system dependencies for building packages
RUN yum update -y && \
    yum install -y gcc g++ make && \
    yum clean all

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -t /app/dependencies

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt', download_dir='/app/nltk_data'); nltk.download('stopwords', download_dir='/app/nltk_data'); nltk.download('wordnet', download_dir='/app/nltk_data'); nltk.download('vader_lexicon', download_dir='/app/nltk_data')"

# ============================================================================
# Runtime stage - minimal image with only runtime dependencies
# ============================================================================
FROM public.ecr.aws/lambda/python:3.11

# Set NLTK data path
ENV NLTK_DATA=/var/task/nltk_data

# Copy dependencies from builder stage
COPY --from=builder /app/dependencies ${LAMBDA_TASK_ROOT}
COPY --from=builder /app/nltk_data ${LAMBDA_TASK_ROOT}/nltk_data

# Copy application code
COPY src/ ${LAMBDA_TASK_ROOT}/src/
COPY src/lambda_handler.py ${LAMBDA_TASK_ROOT}/

# Set the Lambda handler
CMD ["lambda_handler.lambda_handler"]