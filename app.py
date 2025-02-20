from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, send_from_directory
import google.generativeai as genai
import requests
from requests.exceptions import Timeout
from bs4 import BeautifulSoup
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import random
import time
import firebase_admin
from firebase_admin import credentials, auth, firestore
import secrets
import os
from firebase_admin.exceptions import FirebaseError
from firebase_admin.auth import EmailNotFoundError
from google.generativeai.types import GenerationConfig, HarmCategory, HarmBlockThreshold

# Replace with your actual Firebase credentials file path
cred_path = "path/to/your/firebase_credentials.json"  #Update with correct path
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)
db = firestore.client()

app = Flask(__name__, static_url_path='/static')
app.secret_key = secrets.token_urlsafe(32)


generation_config = GenerationConfig(
    temperature=0.9,
    top_p=1,
    top_k=1,
    max_output_tokens=2048,
    candidate_count=1  
)

safety = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}


# Replace with your actual Gemini API key
genai_api_key = "your_gemini_api_key" #Update with your key
genai.configure(api_key=genai_api_key)
model = genai.GenerativeModel('gemini-1.5-flash',generation_config=generation_config,safety_settings=safety)

# Replace with your actual Sketchfab API token
SKETCHFAB_API_TOKEN = "your_sketchfab_api_token" #Update with your key


def login_required(f):
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_uid' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def make_request_with_timeout(url, timeout=10, headers=None, params=None):
    try:
        return requests.get(url, timeout=timeout, headers=headers, params=params)
    except Timeout:
        print(f"Request to {url} timed out")
        return None
    except Exception as e:
        print(f"Error making request to {url}: {str(e)}")
        return None


def search_bing_images(plant_name):
    search_url = f"https://www.bing.com/images/search?q={plant_name}+plant&FORM=HDRSC2"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
    try:
        response = make_request_with_timeout(search_url, headers=headers)
        if response:
            soup = BeautifulSoup(response.text, 'html.parser')
            image_element = soup.find('a', class_='iusc')
            if image_element:
                image_data = json.loads(image_element['m'])
                return image_data.get('murl')
    except Exception as e:
        print(f"Bing image search failed: {e}")
    return None


def search_unsplash_images(plant_name):
    search_url = f"https://unsplash.com/s/photos/{plant_name}"
    try:
        response = make_request_with_timeout(search_url)
        if response:
            soup = BeautifulSoup(response.text, 'html.parser')
            image_element = soup.find('img', class_='_2zEKz')
            if image_element:
                return image_element['src']
    except Exception as e:
        print(f"Unsplash image search failed: {e}")
    return None


def search_pixabay_images(plant_name):
    search_url = f"https://pixabay.com/images/search/{plant_name}/"
    try:
        response = make_request_with_timeout(search_url)
        if response:
            soup = BeautifulSoup(response.text, 'html.parser')
            image_element = soup.find('img', class_='preview')
            if image_element:
                return image_element['src']
    except Exception as e:
        print(f"Pixabay image search failed: {e}")
    return None


def search_pexels_images(plant_name):
    search_url = f"https://www.pexels.com/search/{plant_name}/"
    try:
        response = make_request_with_timeout(search_url)
        if response:
            soup = BeautifulSoup(response.text, 'html.parser')
            image_element = soup.find('img', class_='photo-item__img')
            if image_element:
                return image_element['src']
    except Exception as e:
        print(f"Pexels image search failed: {e}")
    return None


def search_flickr_images(plant_name):
    search_url = f"https://www.flickr.com/search/?text={plant_name}"
    try:
        response = make_request_with_timeout(search_url)
        if response:
            soup = BeautifulSoup(response.text, 'html.parser')
            image_element = soup.find('img', class_='photo-list-photo-view')
            if image_element:
                return image_element['src']
    except Exception as e:
        print(f"Flickr image search failed: {e}")
    return None


def fetch_image_concurrently(plant_name):
    search_methods = [
        search_bing_images,
        search_unsplash_images,
        search_pixabay_images,
        search_pexels_images,
        search_flickr_images
    ]

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_search = {executor.submit(method, plant_name): method for method in search_methods}
        for future in as_completed(future_to_search):
            image_url = future.result()
            if image_url:
                return image_url
    return None


def search_sketchfab(plant_name):
    api_url = "https://api.sketchfab.com/v3/search"
    params = {
        "q": plant_name + " plant",
        "type": "models",
        "sort_by": "-relevance",
        "downloadable": True
    }
    headers = {
        "Authorization": f"Bearer {SKETCHFAB_API_TOKEN}"
    }

    try:
        response = make_request_with_timeout(api_url, params=params, headers=headers)
        if response and response.status_code == 200:
            data = response.json()
            if data['results']:
                return data['results'][0]['embedUrl']
        else:
            print(f"Sketchfab API request failed: {response.status_code if response else 'No response'}")
    except Exception as e:
        print(f"Error in search_sketchfab: {str(e)}")
    return None

@app.route('/search_sketchfab')
def search_sketchfab_route():
    plant_name = request.args.get('plant_name')
    if not plant_name:
        return jsonify({"error": "No plant name provided"}), 400
    
    embed_url = search_sketchfab(plant_name)
    if embed_url:
        return jsonify({"embedUrl": embed_url})
    else:
        return jsonify({"error": "No model found"}), 404

def get_plant_info(plant_name):
    prompt = f"""
    Provide accurate details about the medicinal plant {plant_name}, including:
        1. Botanical Information:
        - Scientific Name
        - Common Names
        - Family
        - Taxonomic Classification
        2. Physical Description:
        - Plant Characteristics
        - Leaf, Flower, and Fruit Details
        3. Habitat and Distribution:
        - Native Regions
        - Current Global Distribution
        4. Medicinal Uses:
        - Traditional Uses
        - Modern Medicinal Applications
        - Active Compounds
        5. Cultivation Methods:
        - Growing Conditions
        - Propagation Techniques
        - Harvesting Practices
        6. Chemical Composition:
        - Major Phytochemicals
        - Nutritional Content (if applicable)
        7. Pharmacological Effects:
        - Reported Therapeutic Actions
        - Mechanism of Action (if known)
        8. Clinical Studies and Research:
        - Summary of Key Findings
        - Ongoing Research Areas
        9. Safety and Precautions:
        - Potential Side Effects
        - Contraindications
        - Drug Interactions
        10. Cultural and Historical Significance
        11. Sources to Find the Plant:
        - Sources in india
        12. Reference Links:
        - Scientific Databases
        - Authoritative Websites
        - Research Papers
        Format the response in HTML with collapsible sections for each topic.
        Ensure all information is accurate and up-to-date, citing reliable sources where possible.

    """
    response = model.generate_content(prompt)

    while not response.text:
        time.sleep(1)
        response = model.generate_content(prompt)
    
    return response.text


@app.route('/')
@login_required
def index():
    return render_template('index.html')

# Replace with your actual Firebase API key
FIREBASE_API_KEY = "your_firebase_api_key" #Update with your key
FIREBASE_SIGN_IN_URL = f'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}'

def verify_password_with_firebase(email, password):
    payload = json.dumps({
        "email": email,
        "password": password,
        "returnSecureToken": True
    })
    
    response = requests.post(FIREBASE_SIGN_IN_URL, data=payload)
    
    return response.status_code == 200


# Replace with your actual Firebase Web API key
FIREBASE_WEB_API_KEY = "your_firebase_web_api_key" #Update with your key
def exchange_custom_token_for_id_token(custom_token, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={FIREBASE_WEB_API_KEY}"
    
    payload = json.dumps({
        "token": custom_token.decode('utf-8'),
        "returnSecureToken": True
    })
    
    response = requests.post(url, data=payload)
    
    return response

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            if verify_password_with_firebase(email, password):
                user = auth.get_user_by_email(email)
                session['user_uid'] = user.uid
                session['user_email'] = email
                session['user_display_name'] = user.display_name if user.display_name else email.split('@')[0]
                flash('Logged in successfully.', 'success')
                return redirect(url_for('index'))
            else:
                error = 'Invalid email or password.'
                return render_template('login.html', error=error)
        except auth.AuthError as e:
            error = f'Authentication failed: {str(e)}'
            return render_template('login.html', error=error)
        except Exception as e:
            error = f'An error occurred: {str(e)}'
            return render_template('login.html', error=error)

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        try:
            user = auth.create_user(
                email=email,
                password=password,
                display_name=name
            )
            session.permanent = True  
            session['user_uid'] = user.uid
            session['user_email'] = email
            session['user_display_name'] = name
            return redirect(url_for('index'))
        except Exception as e:
            error = str(e)
            return render_template('signup.html', error=error)

    return render_template('signup.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/search', methods=['POST'])
@login_required
def search():
    plant_name = request.form['plant_name']
    model_url = search_sketchfab(plant_name)
    plant_info = get_plant_info(plant_name)

    if not model_url:
        image_url = fetch_image_concurrently(plant_name)
        return jsonify({
            'image_url': image_url,
            'plant_info': plant_info
        })
    else:
        return jsonify({
            'model_url': model_url,
            'plant_info': plant_info
        })


@app.route('/bookmark', methods=['POST'])
@login_required
def bookmark():
    try:
        plant_data = request.get_json()
        if not plant_data:
            return jsonify({'success': False, 'message': 'No JSON data received'}), 400

        user_uid = session.get('user_uid')
        if not user_uid:
            return jsonify({'success': False, 'message': 'User not authenticated'}), 401

        if 'name' not in plant_data:
            return jsonify({'success': False, 'message': 'Plant name is required'}), 400

        doc_ref = db.collection('users').document(user_uid).collection('bookmarks').document(plant_data['name'])

        doc = doc_ref.get()
        if doc.exists:
            doc_ref.update({
                'info': plant_data.get('info', ''),
                'model_url': plant_data.get('model_url'),
                'image_url': plant_data.get('image_url'),
                'notes': plant_data.get('notes', '')
            })
        else:
            doc_ref.set({
                'name': plant_data['name'],
                'info': plant_data.get('info', ''),
                'model_url': plant_data.get('model_url'),
                'image_url': plant_data.get('image_url'),
                'notes': plant_data.get('notes', '')
            })

        return jsonify({'success': True, 'message': 'Bookmark saved successfully'})
    except Exception as e:
        print(f"Error in bookmark function: {str(e)}")
        return jsonify({'success': False, 'message': f'Failed to save bookmark: {str(e)}'}), 500
    
# Add this new route to debug the incoming data
@app.route('/debug_bookmark', methods=['POST'])
@login_required
def debug_bookmark():
    print("Received data:", request.get_json())
    print("Headers:", dict(request.headers))
    return jsonify({'message': 'Debug information printed to console'})


@app.route('/remove_bookmark', methods=['POST'])
@login_required
def remove_bookmark():
    plant_data = request.get_json()
    user_uid = session['user_uid']
    plant_name = plant_data.get('name')

    if not plant_name:
        return jsonify({'success': False, 'message': 'Plant name is required'}), 400

    doc_ref = db.collection('users').document(user_uid).collection('bookmarks').document(plant_name)
    doc_ref.delete()

    return jsonify({'success': True})


@app.route('/get_bookmark_data', methods=['POST'])
@login_required
def get_bookmark_data():
    plant_name = request.form['plant_name']
    user_uid = session['user_uid']

    doc_ref = db.collection('users').document(user_uid).collection('bookmarks').document(plant_name)
    doc = doc_ref.get()

    if doc.exists:
        return jsonify(doc.to_dict())
    else:
        return jsonify({'error': 'Bookmark not found'}), 404


@app.route('/update_bookmark_notes', methods=['POST'])
@login_required
def update_bookmark_notes():
    user_uid = session['user_uid']
    plant_name = request.form.get('plant_name')
    notes = request.form.get('notes')

    if not plant_name:
        return jsonify({'success': False, 'message': 'Plant name is required'}), 400

    doc_ref = db.collection('users').document(user_uid).collection('bookmarks').document(plant_name)
    
    try:
        doc = doc_ref.get()
        if doc.exists:
            doc_ref.update({'notes': notes})
            return jsonify({'success': True})
        else:
            doc_ref.set({'name': plant_name, 'notes': notes})
            return jsonify({'success': True, 'message': 'Bookmark created with notes'})
    except Exception as e:
        print(f"Error in update_bookmark_notes function: {str(e)}")
        return jsonify({'success': False, 'message': f'Failed to update notes: {str(e)}'}), 500


@app.route('/bookmarks', methods=['GET'])
@login_required
def get_bookmarks():
    user_uid = session['user_uid']
    bookmarks = []
    
    try:
        docs = db.collection('users').document(user_uid).collection('bookmarks').stream()
        for doc in docs:
            bookmark_data = doc.to_dict()
            bookmark_data['id'] = doc.id 
            bookmarks.append(bookmark_data)
        return jsonify(bookmarks)
    except Exception as e:
        print(f"Error in get_bookmarks function: {str(e)}")
        return jsonify({'error': 'Failed to retrieve bookmarks'}), 500

@app.route('/virtual_tour', methods=['GET'])
@login_required
def virtual_tour():
    tour_theme = request.args.get('theme', 'digestive_health') 
    tour_plants = get_tour_plants(tour_theme)
    return render_template('virtual_tour.html', theme=tour_theme, plants=tour_plants)


def get_tour_plants(theme):
    prompt = f"""
    Provide a list of 5 medicinal plants commonly used in AYUSH systems for {theme}.
    Include: Plant name, Brief description, Primary use in AYUSH for {theme}, and a short description to generate an image of the plant.
    Format the response as a JSON array.
    """
    response = model.generate_content(prompt)

    json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
    if json_match:
        try:
            plants = json.loads(json_match.group())
            for plant in plants:
                plant['model_url'] = search_sketchfab(plant['name'])
                if not plant['model_url']:
                    plant['image_url'] = fetch_image_concurrently(plant['name'])
            return plants
        except json.JSONDecodeError:
            print("Failed to parse JSON from AI response.")
    return []

@app.route('/filter_plants', methods=['POST'])
def filter_plants():
    criteria = request.json
    system = criteria.get('system', '')
    part = criteria.get('part', '')
    use = criteria.get('use', '')
    region = criteria.get('region', '')  # New region filter

    prompt = f"""
    Provide a list of 5 medicinal plants used in AYUSH systems that match the following criteria:
    AYUSH System: {system}
    Plant Part: {part}
    Medicinal Use: {use}
    Region: {region}  

    For each plant, include:
    - name: (plant name)
    - description: (brief description, 1-2 sentences)
    - matches_criteria: (how it matches the given criteria)

    Format the response as a JSON array of objects with the above fields.
    """
    response = model.generate_content(prompt)

    json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
    if json_match:
        try:
            plants = json.loads(json_match.group())
            # Add image fetching here for each plant
            for plant in plants:
                plant['image_url'] = fetch_image_concurrently(plant['name'])
            return jsonify(plants)
        except json.JSONDecodeError:
            return jsonify([{"name": "Error", "description": "Failed to parse results", "matches_criteria": response.text}])
    else:
        return jsonify([{"name": "Error", "description": "No valid JSON found in the response", "matches_criteria": response.text}])

@app.route('/bg.jpg')
def serve_background():
    return send_from_directory(app.root_path, 'templates/bg.jpg') 


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        try:
            user = auth.get_user_by_email(email)
            auth.send_password_reset_email(user.uid) 
            flash('If an account exists with that email, a password reset link has been sent.', 'success')
            return redirect(url_for('login'))
        except auth.UserNotFoundError:
            flash('If an account exists with that email, a password reset link has been sent.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
    
    return render_template('forgot_password.html')



from flask import jsonify, current_app

def extract_json_from_response(response_text):
    match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
    if match:
        return match.group(1)
    return response_text  

@app.route('/plant_of_the_day')
def plant_of_the_day():
    prompt = """
    Provide information about a random medicinal plant used in AYUSH systems. Include: Plant Name, Scientific Name, AYUSH System, Brief Description, Main Medicinal Uses, and Interesting Fact.
    Format the response as a JSON object.
    """
    try:
        response = model.generate_content(prompt)
        
        current_app.logger.debug(f"Raw API response: {response.text}")
        
        if not response.text:
            raise ValueError("Empty response from API")
        
        json_content = extract_json_from_response(response.text)
        plant_data = json.loads(json_content)
        
        plant_data['image_url'] = fetch_image_concurrently(plant_data['Plant Name'])
        
        return jsonify(plant_data)
    except json.JSONDecodeError as e:
        current_app.logger.error(f"JSON decoding error: {str(e)}")
        return jsonify({"error": "Invalid data received from API"}), 500
    except Exception as e:
        current_app.logger.error(f"Error in plant_of_the_day: {str(e)}")
        return jsonify({"error": "An error occurred while processing the request"}), 500

@app.route('/plant_quiz')
def plant_quiz():
    prompt = """
    Generate a multiple-choice question about medicinal plants used in AYUSH systems. Include:
    - question: The question text
    - options: An object with keys A, B, C, D for the four options
    - correct_answer: The letter of the correct answer (A, B, C, or D)
    - explanation: Brief explanation of the correct answer
    Format the response as a JSON object.
    """
    try:
        response = model.generate_content(prompt)
        
        if not response.text:
            raise ValueError("Empty response from API")
        
        # Try to parse the entire response as JSON
        try:
            quiz_data = json.loads(response.text)
        except json.JSONDecodeError:
            # If that fails, try to extract JSON from the response
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                quiz_data = json.loads(json_match.group())
            else:
                raise ValueError("No valid JSON found in the response")
        
        # Validate the structure of the quiz data
        required_keys = ['question', 'options', 'correct_answer', 'explanation']
        if not all(key in quiz_data for key in required_keys):
            raise ValueError("Quiz data is missing required fields")
        
        return jsonify(quiz_data)
    except Exception as e:
        current_app.logger.error(f"Error in plant_quiz: {str(e)}")
        return jsonify({"error": "An error occurred while generating the quiz"}), 500

@app.route('/generate_story', methods=['POST'])
def generate_story():
    data = request.get_json()
    prompt = data.get('prompt')
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400

    response = model.generate_content(prompt)
    
    return jsonify({'story': response.text})

if __name__ == '__main__':
    app.run(debug=True) 