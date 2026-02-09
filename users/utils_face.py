try:
    import face_recognition
    import numpy as np
    FACE_REC_AVAILABLE = True
except ImportError:
    FACE_REC_AVAILABLE = False
    print("WARNING: face_recognition library not found. Running in MOCK mode.")

def get_face_encoding(image_file):
    """
    Processes an uploaded image file and returns the face encoding.
    Returns None if no face is found or multiples are found (optional strictness).
    """
    if not FACE_REC_AVAILABLE:
        # Return None to prevent invalid enrollments when library is missing
        print("ERROR: Face recognition library missing. Enrollment failed for security.")
        return None

    try:
        image = face_recognition.load_image_file(image_file)
        encodings = face_recognition.face_encodings(image)
        
        if len(encodings) > 0:
            return encodings[0].tobytes() # Store as bytes
        return None
    except Exception as e:
        print(f"Face processing error: {e}")
        return None

def compare_faces(known_encoding_bytes, unknown_image_file, tolerance=0.45):
    """
    Compares the stored enrollment encoding (Machine Learning feature) 
    with a new image captured from the live camera.
    Tolerance: 0.45 is strict (standard is 0.6). Lower is MORE secure.
    """
    if not FACE_REC_AVAILABLE:
        print("CRITICAL: Machine Learning library (face_recognition) not detected.")
        return False

    if not known_encoding_bytes:
        print("ERROR: No enrollment data for this voter.")
        return False

    try:
        # Convert stored bytes back to a numpy array for comparison
        known_encoding = np.frombuffer(known_encoding_bytes, dtype=np.float64)
        
        # Load the live captured image from the camera
        unknown_image = face_recognition.load_image_file(unknown_image_file)
        
        # Extract features (encodings) from the live image
        unknown_encodings = face_recognition.face_encodings(unknown_image)
        
        if not unknown_encodings:
            print("INFO: No face detected in the camera frame.")
            return False
            
        # Perform the ML comparison
        matches = face_recognition.compare_faces([known_encoding], unknown_encodings[0], tolerance=tolerance)
        
        if matches[0]:
            print("SUCCESS: Live camera image matches the uploaded profile photo!")
            return True
        else:
            print("FAILED: Camera image DOES NOT match the profile photo.")
            return False
            
    except Exception as e:
        print(f"ML Processing error: {e}")
        return False
