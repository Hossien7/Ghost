import cv2

def detect_faces_image(image_path):
    """Detects faces in an image using Haar cascades.

    Args:
        image_path (str): Path to the image file.
    """
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    
    print(f"Number of faces detected: {len(faces)} on the image")

    for (x, y, w, h) in faces:
        cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)

    cv2.imshow('Faces Detected', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
