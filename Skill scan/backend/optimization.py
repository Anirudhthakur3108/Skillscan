"""
Performance Optimization & Database Tuning for SkillScan Backend
Includes query optimization, caching, and resource management
"""

import logging
from functools import wraps
from flask import request, g
import time
from datetime import datetime, timedelta
from sqlalchemy import event, text
from sqlalchemy.pool import Pool

logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE PERFORMANCE: Connection Pooling & Optimization
# ============================================================================

class DatabaseOptimization:
    """Configure database for optimal performance"""
    
    @staticmethod
    def configure_connection_pool(db):
        """Setup connection pooling for production"""
        from sqlalchemy.pool import StaticPool, QueuePool
        
        # For production (PostgreSQL)
        db.engine.pool = QueuePool(
            db.engine.raw_connection,
            max_overflow=20,
            pool_size=10,
            timeout=30,
            recycle=3600  # Recycle connections every hour
        )
        
        # Log pool events
        @event.listens_for(Pool, "connect")
        def receive_connect(dbapi_conn, connection_record):
            logger.debug("Database connection established")
        
        @event.listens_for(Pool, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            logger.debug("Database connection checked out from pool")
    
    @staticmethod
    def enable_query_logging(db):
        """Enable SQL query logging for optimization analysis"""
        import sqlalchemy
        
        @event.listens_for(sqlalchemy.engine.Engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            g.query_start_time = time.time()
            logger.debug(f"Query: {statement[:100]}...")
        
        @event.listens_for(sqlalchemy.engine.Engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            elapsed = time.time() - g.query_start_time
            if elapsed > 0.1:  # Log slow queries (>100ms)
                logger.warning(f"SLOW QUERY ({elapsed:.2f}s): {statement[:100]}...")
    
    @staticmethod
    def add_indexes(db):
        """Create indexes for frequently queried fields"""
        with db.engine.connect() as conn:
            try:
                # Index on student email (unique lookup)
                conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS idx_student_email ON student(email)"
                ))
                
                # Index on student_skill (foreign key lookups)
                conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS idx_student_skill_student ON student_skill(student_id)"
                ))
                
                # Index on assessment_response (student lookups)
                conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS idx_assessment_response_student ON assessment_response(student_id)"
                ))
                
                # Index on skill_score (score lookups)
                conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS idx_skill_score_student_skill ON skill_score(student_id, skill_id)"
                ))
                
                # Index on learning_plan (active plans)
                conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS idx_learning_plan_active ON learning_plan(student_id, status)"
                ))
                
                conn.commit()
                logger.info("Database indexes created successfully")
            except Exception as e:
                logger.warning(f"Could not create indexes: {str(e)}")


# ============================================================================
# QUERY OPTIMIZATION: Eager Loading & Pagination
# ============================================================================

class QueryOptimizer:
    """Optimize SQLAlchemy queries"""
    
    @staticmethod
    def eager_load_student_skills(query):
        """Prevent N+1 query problem"""
        from sqlalchemy.orm import joinedload
        return query.options(joinedload('student_skills'))
    
    @staticmethod
    def eager_load_assessments(query):
        """Load assessment data eagerly"""
        from sqlalchemy.orm import joinedload
        return query.options(
            joinedload('assessments'),
            joinedload('skill_scores')
        )
    
    @staticmethod
    def paginate_results(query, page=1, per_page=20):
        """Implement pagination to reduce data transfer"""
        if page < 1:
            page = 1
        if per_page > 100:
            per_page = 100  # Cap at 100 per page
        
        total = query.count()
        items = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return {
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        }


# ============================================================================
# CACHING: Response & Computation Caching
# ============================================================================

class CacheManager:
    """Manage caching of expensive operations"""
    
    # In-memory cache (production: use Redis)
    _cache = {}
    _cache_expiry = {}
    
    @staticmethod
    def get(key):
        """Get cached value if not expired"""
        if key in CacheManager._cache:
            if datetime.now() < CacheManager._cache_expiry.get(key, datetime.now()):
                logger.debug(f"Cache HIT: {key}")
                return CacheManager._cache[key]
            else:
                # Cache expired
                del CacheManager._cache[key]
                del CacheManager._cache_expiry[key]
        logger.debug(f"Cache MISS: {key}")
        return None
    
    @staticmethod
    def set(key, value, ttl_minutes=5):
        """Set cached value with expiry"""
        CacheManager._cache[key] = value
        CacheManager._cache_expiry[key] = datetime.now() + timedelta(minutes=ttl_minutes)
        logger.debug(f"Cache SET: {key} (TTL: {ttl_minutes}m)")
    
    @staticmethod
    def invalidate(key):
        """Remove cached value"""
        if key in CacheManager._cache:
            del CacheManager._cache[key]
            del CacheManager._cache_expiry[key]
            logger.debug(f"Cache INVALIDATED: {key}")
    
    @staticmethod
    def cached_result(ttl_minutes=5):
        """Decorator for caching function results"""
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                # Generate cache key from function name and args
                cache_key = f"{f.__name__}:{str(args)}:{str(kwargs)}"
                
                cached = CacheManager.get(cache_key)
                if cached is not None:
                    return cached
                
                result = f(*args, **kwargs)
                CacheManager.set(cache_key, result, ttl_minutes)
                return result
            return wrapper
        return decorator


# ============================================================================
# API RESPONSE OPTIMIZATION
# ============================================================================

class ResponseOptimizer:
    """Optimize API response size and format"""
    
    @staticmethod
    def minimize_json_payload(data, exclude_fields=None):
        """Remove unnecessary fields from response"""
        exclude_fields = exclude_fields or [
            'password_hash', 'created_at_timestamp',
            'updated_at_timestamp', '_sa_instance_state'
        ]
        
        if isinstance(data, dict):
            return {
                k: ResponseOptimizer.minimize_json_payload(v, exclude_fields)
                for k, v in data.items()
                if k not in exclude_fields
            }
        elif isinstance(data, list):
            return [ResponseOptimizer.minimize_json_payload(item, exclude_fields) for item in data]
        else:
            return data
    
    @staticmethod
    def paginate_large_exports(data, chunk_size=1000):
        """Yield data in chunks for large exports"""
        if not isinstance(data, list):
            yield data
            return
        
        for i in range(0, len(data), chunk_size):
            yield data[i:i + chunk_size]


# ============================================================================
# PDF GENERATION OPTIMIZATION
# ============================================================================

class PDFOptimization:
    """Optimize PDF generation"""
    
    _pdf_cache = {}
    
    @staticmethod
    def cache_pdf_template(template_name):
        """Cache PDF templates"""
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                if template_name not in PDFOptimization._pdf_cache:
                    result = f(*args, **kwargs)
                    PDFOptimization._pdf_cache[template_name] = result
                    logger.debug(f"PDF template cached: {template_name}")
                    return result
                else:
                    logger.debug(f"Using cached PDF template: {template_name}")
                    return PDFOptimization._pdf_cache[template_name]
            return wrapper
        return decorator
    
    @staticmethod
    def stream_pdf_generation(pdf_generator, chunk_size=8192):
        """Stream PDF generation to reduce memory usage"""
        def generate():
            pdf_bytes = BytesIO()
            for chunk in pdf_generator:
                pdf_bytes.write(chunk)
                if pdf_bytes.tell() > chunk_size:
                    yield pdf_bytes.getvalue()
                    pdf_bytes = BytesIO()
            
            # Yield remaining data
            if pdf_bytes.tell() > 0:
                yield pdf_bytes.getvalue()
        
        return generate()


# ============================================================================
# REQUEST/RESPONSE TIMING
# ============================================================================

def track_request_time(f):
    """Decorator to track and log request timing"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = f(*args, **kwargs)
            elapsed = time.time() - start_time
            
            if elapsed > 1.0:  # Log slow endpoints
                logger.warning(
                    f"SLOW ENDPOINT ({elapsed:.2f}s): {request.method} {request.path}"
                )
            else:
                logger.debug(
                    f"Endpoint ({elapsed:.2f}s): {request.method} {request.path}"
                )
            
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"ERROR ENDPOINT ({elapsed:.2f}s): {request.method} {request.path} - {str(e)}"
            )
            raise
    
    return wrapper


# ============================================================================
# MEMORY OPTIMIZATION
# ============================================================================

class MemoryOptimization:
    """Monitor and optimize memory usage"""
    
    @staticmethod
    def check_memory_usage():
        """Check current memory usage"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        return {
            'rss': memory_info.rss / (1024 * 1024),  # MB
            'vms': memory_info.vms / (1024 * 1024),  # MB
            'percent': process.memory_percent()
        }
    
    @staticmethod
    def memory_efficient_file_processing(file_stream, chunk_size=1024):
        """Process large files in chunks to save memory"""
        while True:
            chunk = file_stream.read(chunk_size)
            if not chunk:
                break
            yield chunk
    
    @staticmethod
    def cleanup_on_request_end(response):
        """Cleanup resources after request"""
        # Close file handles, clear large objects
        logger.debug("Request cleanup completed")
        return response


# ============================================================================
# ASSET OPTIMIZATION
# ============================================================================

class AssetOptimization:
    """Optimize static assets"""
    
    @staticmethod
    def get_gzip_settings():
        """Configure gzip compression"""
        return {
            'COMPRESS_LEVEL': 9,  # Max compression
            'COMPRESS_MIN_SIZE': 500,  # Only compress > 500 bytes
            'COMPRESS_MIMETYPES': [
                'text/html',
                'text/css',
                'application/json',
                'application/javascript'
            ]
        }
    
    @staticmethod
    def add_cache_headers(response):
        """Add caching headers to responses"""
        if request.path.endswith(('.css', '.js', '.woff2', '.png', '.jpg')):
            # Cache static assets for 1 week
            response.cache_control.public = True
            response.cache_control.max_age = 7 * 24 * 60 * 60
        else:
            # No cache for dynamic content
            response.cache_control.no_cache = True
            response.cache_control.no_store = True
        
        return response


# ============================================================================
# USAGE: Apply to Flask app
# ============================================================================

"""
Usage in main app:

from optimization import DatabaseOptimization, track_request_time, CacheManager, AssetOptimization

# Setup optimization
DatabaseOptimization.configure_connection_pool(db)
DatabaseOptimization.enable_query_logging(db)
DatabaseOptimization.add_indexes(db)

# Apply decorators to routes
@app.route('/api/assessments/generate', methods=['POST'])
@track_request_time
def generate_assessment():
    # ... route logic

# Apply response optimization
@app.after_request
def optimize_response(response):
    response = AssetOptimization.add_cache_headers(response)
    return response

# Example: Use caching decorator
@CacheManager.cached_result(ttl_minutes=10)
def get_benchmark_data(skill_id):
    # ... expensive computation
    return result
"""

from io import BytesIO
