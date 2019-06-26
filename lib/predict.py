from imutils import paths
import dlib
import cv2
import os
import numpy as np
import lib.models as models
import lib.encodings.encodings as codes





default_path_encodings = codes.default_encodings
default_encoding_data = codes.encoding_data




def face_distance(face_encodings, face_to_compare):
	if len(face_encodings) == 0:
		return np.empty((0))

	return np.linalg.norm(face_encodings - face_to_compare)


def detection_method(method):
	if method == "cnn":
		face_detector = models.cnn_face_detector
	elif method == "haar":
		face_detector = models.haar_face_detector.detectMultiScale
	elif method == "hog":
		face_detector = models.hog_face_detector
	else :
		face_detector = None

	return face_detector


#1
def preprocess(image,method="hog"):
	# load the input image and convert it from BGR to RGB

	img = cv2.imread(image)
	processed_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
	return processed_image






#2
def detect_face_boxes_prediction(img,method="hog"):
	face_detector = detection_method(method)
	boxes = []

	raw_face_locations = face_detector(img, 1)

	for face in raw_face_locations :
		rect_to_css = face.top(), face.right(), face.bottom(), face.left() # this is just for HOG, do it for the other methods too
		boxes.append((max(rect_to_css[0], 0), min(rect_to_css[1], img.shape[1]), min(rect_to_css[2], img.shape[0]), max(rect_to_css[3], 0)))

	return boxes



#3
def detect_landmarks(processed_image,boxes):
	boxes = [dlib.rectangle(box[3], box[0], box[1], box[2]) for box in boxes]
	pose_predictor = models.pose_predictor_68_point
	raw_landmarks = [pose_predictor(processed_image, box) for box in boxes]
	return raw_landmarks

#4
def encode(processed_image,raw_landmarks):
	encodings = [np.array(models.face_encoder.compute_face_descriptor(processed_image, raw_landmark_set,1)) for raw_landmark_set in raw_landmarks]
	return encodings



def recognize_simple(encoding,datas):
	matches = []
	for data in datas["data"] :
		match = (face_distance(data["encoding"], encoding) <= 0.6)
		matches.append(match)
	name = "Unknown"
	precision = 1

	# check to see if we have found a match
	if True in matches:
		# find the indexes of all matched faces then initialize a
		# dictionary to count the total number of times each face
		# was matched
		matchedIdxs = [i for (i, b) in enumerate(matches) if b]
		counts = {}
		# loop over the matched indexes and maintain a count for
		# each recognized face face
		for i in matchedIdxs:
			name = datas["data"][i]["category"]
			counts[name] = counts.get(name, 0) + 1

		# determine the recognized face with the largest number of
		# votes (note: in the event of an unlikely tie Python will
		# select first entry in the dictionary)
		name = max(counts, key=counts.get)
		precision = counts.get(name,0)/len(matchedIdxs)
	response = {"category" : name,"precision":precision}
	return response


#5
def recognize(encodings, boxes,data):
	response = []
# loop over the facial embeddings
	for (box,encoding) in zip(boxes,encodings):
		category = recognize_simple(encoding,data)
		prediction = {"category":category["category"],"precision":category["precision"],"box":box}
		response.append(prediction)
	return response


def draw_boxes(read_image,response):
    for (i,r) in enumerate(response):
        print("\n \n the number ",i+1," prediction  is  :   ",r)
        box = dlib.rectangle(r["box"][3], r["box"][0], r["box"][1], r["box"][2])
        top = box.top()
        right = box.right()
        bottom = box.bottom()
        left = box.left()
        cv2.rectangle(read_image, (left, top), (right, bottom), (0, 255, 0), 2)
        y = top - 15 if top - 15 > 15 else top + 15
        cv2.putText(read_image, r["category"], (left, y), cv2.FONT_HERSHEY_SIMPLEX,
                    0.75, (0, 255, 0), 2)
    return read_image

def save_image(image_path,drawn_image,path_to_results=""):
    image_name = image_path.split("/")[-1].split(".")[0]
    cv2.imwrite(path_to_results + image_name + ".jpg", drawn_image)





def recognize_face(image,method="hog",encoding_path=default_path_encodings):
	if encoding_path == codes.default_encodings :
		data = default_encoding_data
	else :
		data = codes.load_encodings(encoding_path)
	processed_image = preprocess(image,method)
	boxes = detect_face_boxes_prediction(processed_image,method)
	raw_landmarks = detect_landmarks(processed_image,boxes)
	encodings = encode(processed_image,raw_landmarks)
	response = recognize(encodings, boxes,data)
	return response
