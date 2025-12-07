import logging
import os
from datetime import datetime
from contextlib import contextmanager
import requests

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from prometheus_flask_exporter import PrometheusMetrics
import psycopg2
import redis

# Логирование
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
app.config['DEBUG'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-key')

# CORS
CORS(app, resources={r'/api/*': {'origins': '*'}})

# Rate limiting
limiter = Limiter(app=app, key_func=get_remote_address)

# Metrics
metrics = PrometheusMetrics(app)

# Database
class DBConnector:
    def __init__(self):
        self.conn_string = (
            f"dbname={os.getenv('DB_NAME')} "
            f"user={os.getenv('DB_USER')} "
            f"password={os.getenv('DB_PASSWORD')} "
            f"host={os.getenv('DB_HOST')} "
            f"port={os.getenv('DB_PORT', 5432)}"
        )

    def get_connection(self):
        return psycopg2.connect(self.conn_string)

@contextmanager
def get_db_connection():
    connector = DBConnector()
    conn = None
    try:
        conn = connector.get_connection()
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"DB Error: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()

# Redis
try:
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        decode_responses=True
    )
except Exception as e:
    logger.warning(f"Redis connection failed: {str(e)}")
    redis_client = None

# Routes
@app.route('/health', methods=['GET'])
def health():
    status = {
        'status': 'healthy', 
        'database': 'disconnected', 
        'cache': 'disconnected',
        'prometheus': 'disconnected',
        'grafana': 'disconnected'
    }
    try:
        with get_db_connection() as conn:
            status['database'] = 'connected'
    except:
        pass

    try:
        if redis_client:
            redis_client.ping()
            status['cache'] = 'connected'
    except:
        pass

    # Check Prometheus
    try:
        response = requests.get('http://prometheus:9090/-/healthy', timeout=2)
        if response.status_code == 200:
            status['prometheus'] = 'connected'
    except:
        pass

    # Check Grafana
    try:
        response = requests.get('http://grafana:3000/api/health', timeout=2)
        if response.status_code == 200:
            status['grafana'] = 'connected'
    except:
        pass

    return jsonify(status), 200 if status['database'] == 'connected' else 503

@app.route('/', methods=['GET'])
def index():
    try:
        with open('templates/index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error loading index.html: {str(e)}")
        return jsonify({'error': 'Not found'}), 404

@app.route('/api/test', methods=['GET'])
@limiter.limit("10 per minute")
def get_test():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, value, created_at FROM test_table LIMIT 100')
            columns = [desc[0] for desc in cursor.description]
            data = [dict(zip(columns, row)) for row in cursor.fetchall()]
            cursor.close()
        return jsonify({'success': True, 'data': data, 'count': len(data)}), 200
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test', methods=['POST'])
@limiter.limit("10 per minute")
def create_test():
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'Missing name'}), 400

        name = str(data['name']).strip()[:255]
        value = str(data.get('value', '')).strip()

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO test_table (name, value) VALUES (%s, %s) RETURNING id, name, value, created_at',
                (name, value)
            )
            result = cursor.fetchone()
            columns = [desc[0] for desc in cursor.description]
            record = dict(zip(columns, result))
            cursor.close()

        logger.info(f"Created record: {record['id']}")
        return jsonify(record), 201
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/overview', methods=['GET'])
def overview():
    try:
        overview = {'database': {}, 'cache': {}}

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM test_table')
            overview['database']['total_records'] = cursor.fetchone()[0]
            cursor.close()

        if redis_client:
            try:
                info = redis_client.info()
                overview['cache']['keys'] = redis_client.dbsize()
                
                # Memory in MB (used_memory is in bytes)
                used_memory_bytes = info.get('used_memory', 0)
                overview['cache']['memory_mb'] = round(used_memory_bytes / 1024 / 1024, 2) if used_memory_bytes else 0
                
                # Calculate hit rate
                hits = info.get('keyspace_hits', 0)
                misses = info.get('keyspace_misses', 0)
                total = hits + misses
                if total > 0:
                    overview['cache']['hit_rate'] = round(hits / total, 4)
                else:
                    overview['cache']['hit_rate'] = 0
            except Exception as e:
                logger.error(f"Redis metrics error: {str(e)}")
                overview['cache'] = {'keys': 0, 'memory_mb': 0, 'hit_rate': 0}

        return jsonify(overview), 200
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Redis Cache Management
@app.route('/api/cache', methods=['GET'])
@limiter.limit("30 per minute")
def get_cache_keys():
    """Get all keys in Redis cache."""
    try:
        if not redis_client:
            return jsonify({'error': 'Redis not available'}), 503
        
        keys = []
        for key in redis_client.scan_iter():
            keys.append(key)
        
        return jsonify({'keys': keys, 'count': len(keys)}), 200
    except Exception as e:
        logger.error(f"Error getting cache keys: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cache/<key>', methods=['GET'])
@limiter.limit("30 per minute")
def get_cache_value(key):
    """Get value from Redis cache by key."""
    try:
        if not redis_client:
            return jsonify({'error': 'Redis not available'}), 503
        
        value = redis_client.get(key)
        if value is None:
            return jsonify({'error': 'Key not found'}), 404
        
        ttl = redis_client.ttl(key)
        return jsonify({
            'key': key,
            'value': value,
            'ttl': ttl if ttl > 0 else None
        }), 200
    except Exception as e:
        logger.error(f"Error getting cache value: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cache', methods=['POST'])
@limiter.limit("30 per minute")
def set_cache_value():
    """Set key-value in Redis cache."""
    try:
        if not redis_client:
            return jsonify({'error': 'Redis not available'}), 503
        
        data = request.get_json()
        if not data or 'key' not in data or 'value' not in data:
            return jsonify({'error': 'Missing key or value'}), 400
        
        key = str(data['key']).strip()
        value = str(data['value']).strip()
        ttl = data.get('ttl')  # Time to live in seconds
        
        if ttl and ttl > 0:
            redis_client.setex(key, ttl, value)
        else:
            redis_client.set(key, value)
        
        logger.info(f"Cache set: {key}")
        return jsonify({
            'key': key,
            'value': value,
            'ttl': ttl
        }), 201
    except Exception as e:
        logger.error(f"Error setting cache value: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cache/<key>', methods=['DELETE'])
@limiter.limit("30 per minute")
def delete_cache_key(key):
    """Delete key from Redis cache."""
    try:
        if not redis_client:
            return jsonify({'error': 'Redis not available'}), 503
        
        deleted = redis_client.delete(key)
        if deleted == 0:
            return jsonify({'error': 'Key not found'}), 404
        
        logger.info(f"Cache deleted: {key}")
        return jsonify({'success': True, 'key': key}), 200
    except Exception as e:
        logger.error(f"Error deleting cache key: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(429)
def ratelimit(e):
    return jsonify({'error': 'Too many requests'}), 429

@app.errorhandler(500)
def error500(e):
    logger.error(f"Internal error: {str(e)}")
    return jsonify({'error': 'Internal error'}), 500

if __name__ == '__main__':
    logger.info("Starting app...")
    app.run(host='0.0.0.0', port=3000, debug=False)
