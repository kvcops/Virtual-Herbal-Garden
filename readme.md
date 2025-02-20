# AYUSH Virtual Herbal Garden

**AYUSH Virtual Herbal Garden** is an innovative, interactive web application that brings the ancient wisdom of AYUSH (Ayurveda, Yoga & Naturopathy, Unani, Siddha, and Homeopathy) to life. Explore a virtual garden of medicinal plants through stunning 3D models, rich multimedia content, and AI-powered insights—all from your browser!

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Demo](#demo)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Overview
The **AYUSH Virtual Herbal Garden** project combines centuries-old traditional knowledge with modern technology. Users can interact with realistic 3D models, dive into detailed plant information, and enjoy multimedia content that enhances the learning experience. Whether you are a student, practitioner, or simply curious about natural remedies, this project makes exploring medicinal plants engaging and accessible.

## Features
- **Interactive 3D Models:** Rotate, zoom, and explore detailed models of medicinal plants using A-Frame.
- **Comprehensive Information:** Access in-depth details on botanical data, medicinal uses, cultivation techniques, chemical composition, and more.
- **Multimedia Integration:** Enjoy high-quality images, informative videos, and audio narrations.
- **Advanced Search & Filtering:** Easily find plants based on AYUSH system, medicinal use, region, and other criteria.
- **Virtual Tours:** Experience guided tours focused on themes like digestive health, immunity boosting, and stress relief.
- **User Interaction:** Bookmark your favorite plants, take notes, and share your discoveries on social media.

## Technologies Used
- **Front-End:**  
  - HTML, CSS, JavaScript  
  - [A-Frame](https://aframe.io/) for creating immersive 3D/VR experiences  
  - [GSAP](https://greensock.com/gsap/) for smooth animations
- **Back-End:**  
  - Python with [Flask](https://flask.palletsprojects.com/)  
  - [Google Generative AI API](https://cloud.google.com/ai) for dynamic content generation  
  - [Firebase](https://firebase.google.com/) for authentication and database (Firestore)  
  - [Sketchfab API](https://sketchfab.com/developers) for 3D model integration  
  - Web scraping tools (e.g., BeautifulSoup, requests) for data collection

## Demo
Watch the demo video to see the project in action:

[![AYUSH Virtual Herbal Garden Demo](https://img.youtube.com/vi/9OF1SdJ65Hc/hqdefault.jpg)](https://youtu.be/9OF1SdJ65Hc?si=mKuEqsXC3L89sEr_)

## Installation
Follow these steps to set up the project locally:

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/ayush-virtual-herbal-garden.git
   cd ayush-virtual-herbal-garden
   ```

2. **Set Up the Backend:**
   - Ensure you have Python installed.
   - Create and activate a virtual environment:
     ```bash
     python -m venv venv
     source venv/bin/activate  # On Windows: venv\Scripts\activate
     ```
   - Install required packages:
     ```bash
     pip install -r requirements.txt
     ```
   - Configure your Firebase and Google Generative AI API credentials.

3. **Set Up the Front-End:**
   - Open `index.html` in your browser, or start a local server:
     ```bash
     python -m http.server
     ```

4. **Run the Application:**
   - Start the Flask server:
     ```bash
     python app.py
     ```
   - Visit `http://localhost:5000` to explore the virtual garden.

## Usage
- **Explore:** Navigate through interactive 3D models and read detailed descriptions of each medicinal plant.
- **Search & Filter:** Use the search bar and filters to quickly find plants that interest you.
- **Virtual Tours:** Start guided tours to learn about specific health benefits.
- **Interact:** Bookmark your favorite plants, take notes, and share insights with friends.

## Contributing
Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Commit your changes with clear messages.
4. Push your branch and open a pull request.

Please follow the existing coding style and include tests where applicable.

## License
This project is licensed under the [MIT License](LICENSE).

---

Enjoy exploring the **AYUSH Virtual Herbal Garden** and feel free to share your thoughts or suggestions. Let's bridge the gap between traditional wisdom and modern technology—together!
