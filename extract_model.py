import bz2
import shutil

# Extract the dlib model file
with bz2.BZ2File('models/shape_predictor_68_face_landmarks.dat.bz2', 'rb') as src:
    with open('models/shape_predictor_68_face_landmarks.dat', 'wb') as dst:
        shutil.copyfileobj(src, dst)

print("Model file extracted successfully!")