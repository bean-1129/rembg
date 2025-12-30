from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from rembg import remove
from PIL import Image
import io
import logging
import os
import requests

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cloudinary credentials (set these in Render environment variables)
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME', 'dh7wdmycq')
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY', '')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET', '')

@app.route('/')
def home():
    return jsonify({
        'status': 'Virtual Wardrobe API',
        'version': '2.0',
        'endpoints': {
            '/remove-bg': 'POST - Remove background from image',
            '/delete-image': 'DELETE - Delete image from Cloudinary',
            '/health': 'GET - Health check'
        }
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/remove-bg', methods=['POST'])
def remove_background():
    try:
        logger.info('Background removal request received')
        
        if 'image' not in request.files:
            logger.error('No image provided in request')
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            logger.error('Empty filename')
            return jsonify({'error': 'No file selected'}), 400
        
        logger.info(f'Processing image: {file.filename}')
        input_image = Image.open(file.stream)
        
        logger.info('Removing background...')
        output_image = remove(input_image)
        
        img_io = io.BytesIO()
        output_image.save(img_io, 'PNG', optimize=True)
        img_io.seek(0)
        
        logger.info('Background removed successfully')
        
        return send_file(
            img_io, 
            mimetype='image/png',
            as_attachment=False,
            download_name='nobg.png'
        )
    
    except Exception as e:
        logger.error(f'Error removing background: {str(e)}')
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@app.route('/delete-image', methods=['DELETE'])
def delete_image():
    try:
        data = request.get_json()
        public_id = data.get('publicId')
        
        if not public_id:
            return jsonify({'error': 'No publicId provided'}), 400
        
        logger.info(f'Deleting image: {public_id}')
        
        # Construct Cloudinary delete URL
        timestamp = str(int(time.time()))
        signature = generate_signature(public_id, timestamp)
        
        url = f'https://api.cloudinary.com/v1_1/{CLOUDINARY_CLOUD_NAME}/image/destroy'
        
        response = requests.post(url, data={
            'public_id': public_id,
            'api_key': CLOUDINARY_API_KEY,
            'timestamp': timestamp,
            'signature': signature
        })
        
        if response.status_code == 200:
            logger.info('Image deleted successfully')
            return jsonify({'success': True}), 200
        else:
            logger.error(f'Cloudinary deletion failed: {response.text}')
            return jsonify({'error': 'Deletion failed'}), 500
    
    except Exception as e:
        logger.error(f'Error deleting image: {str(e)}')
        return jsonify({'error': str(e)}), 500

def generate_signature(public_id, timestamp):
    import hashlib
    import hmac
    
    # Create signature for Cloudinary API
    to_sign = f'public_id={public_id}&timestamp={timestamp}{CLOUDINARY_API_SECRET}'
    signature = hashlib.sha1(to_sign.encode()).hexdigest()
    return signature

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
