from flask import Flask, request, send_file
from rembg import remove
from PIL import Image
import io

app = Flask(__name__)

@app.route('/')
def home():
    return {'status': 'Virtual Wardrobe Background Removal API', 'version': '1.0'}

@app.route('/remove-bg', methods=['POST'])
def remove_background():
    try:
        # Get image from request
        if 'image' not in request.files:
            return {'error': 'No image provided'}, 400
        
        file = request.files['image']
        
        # Read image
        input_image = Image.open(file.stream)
        
        # Remove background
        output_image = remove(input_image)
        
        # Convert to bytes
        img_io = io.BytesIO()
        output_image.save(img_io, 'PNG')
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png')
    
    except Exception as e:
        return {'error': str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)