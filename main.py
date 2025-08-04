import cv2
import mediapipe as mp
import pycaw.pycaw as pycaw
import math
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pynput

preventChange = True
timer = 0

# Initialize MediaPipe Hands module
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()

spClId = "2fdbceba65d546fcad10b197d85d80b5"
secretClId = "ac3138f713b5467fa415f2b65417a280"

SCOPEs = ['app-remote-control', 'user-read-playback-state', 'user-modify-playback-state']

auth_manager = SpotifyOAuth(client_id=spClId, client_secret=secretClId, redirect_uri="https://127.0.0.1:8000/callback", scope=SCOPEs)
sp = spotipy.Spotify(auth_manager=auth_manager)

# Initialize MediaPipe Drawing module for drawing landmarks
mp_drawing = mp.solutions.drawing_utils

devices = sp.devices()

def getVolume():
  try:
    devices = sp.devices()
    for device in devices['devices']:
        if device['is_active']:
            return device['volume_percent']
  except:
     print("Timeout: getVolume")
     

def changeVolume(vol):
  try:
    for device in devices['devices']:
        if device['is_active']:
            sp.volume(int(vol*100),device['id'])
  except:
     print("Timeout: changeVolume")

# Calculate Distance
def calcDistance(pointA, pointB):
    try:
        # distance = square root (b1 - a1)^2 + (b2 - a2)^2
        distance = math.sqrt(((pointB[0] - pointA[0])**2) + ((pointB[1] - pointA[1])**2))
    except TypeError:
        # if human pose estimation cant find point it returns none for that coordinate, and so cannot be used in calculations
        distance = 0
    return distance

def playSong():
  try:
    song = sp.current_playback()
    if song['is_playing'] == False:
      for device in devices['devices']:
          if device['is_active']:
              sp.start_playback(device['id'])
              timer = 10
              print("play")
  except:
     print("Timeout: Play")

def pauseSong():
  try:
    song = sp.current_playback()
    if song['is_playing']:
      for device in devices['devices']:
          if device['is_active']:
              sp.pause_playback(device['id'])
              timer = 10
              print("pause")
  except:
     print("Timeout: Pause")

def skipSong():
  try:
    for device in devices['devices']:
        if device['is_active']:
            sp.next_track(device['id'])
            print("skip")
  except:
     print("Timeout: Skip")

def previousSong():
  try:
    for device in devices['devices']:
        if device['is_active']:
            sp.previous_track(device['id'])
            print("previous")
  except:
     print("Timeout: Previous")


# Open a video capture object (0 for the default camera)
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    
    if not ret:
        continue

    # Convert the frame to RGB format
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_rgb = cv2.flip(frame_rgb,1)
    frame = cv2.flip(frame,1)

    # Process the frame to detect hands
    results = hands.process(frame_rgb)
    
    # Check if hands are detected
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Draw landmarks on the frame
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
    # Write current prevention. TRUE = Wont change, FALSE = Will Change
    frame = cv2.putText(frame, 'Preventing: ' + str(preventChange), (frame.shape[1]-135,25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 0, 160), 1, cv2.LINE_AA)
    frame = cv2.putText(frame, 'Timer: ' + str(timer), (frame.shape[1]-130,50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 0, 160), 1, cv2.LINE_AA)

    if timer != 0:
       timer = timer-1

    # check if there are hands
    if results.multi_handedness:
        # if commands are avaialble
        if preventChange == False:

          # if two hands in view
          if len(results.multi_handedness) == 2:
            frame = cv2.putText(frame, "2 Hands", (5,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 0, 160), 3, cv2.LINE_AA)

            # change volume between hands
            distance = calcDistance((results.multi_hand_landmarks[0].landmark[8].x,results.multi_hand_landmarks[0].landmark[8].y),(results.multi_hand_landmarks[1].landmark[8].x,results.multi_hand_landmarks[1].landmark[8].y))
            dis = round(distance,2)
            volume = getVolume()
            if volume != None:
              frame = cv2.putText(frame, 'volume:' + str(round(volume,2)), (5,100), cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 0, 160), 1, cv2.LINE_AA)
            else:
              frame = cv2.putText(frame, 'volume: Error', (5,100), cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 0, 160), 1, cv2.LINE_AA)
            if dis:
              if timer == 0:
                changeVolume(abs(dis))
                timer = 15

          # if only one hand is in view
          elif len(results.multi_handedness) == 1:
            frame = cv2.putText(frame, (results.multi_handedness[0].classification[0].label) + " Hand", (5,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 0, 160), 3, cv2.LINE_AA)
            if timer == 0:
              # check if hand is fist or outstreched
              knuckleCheck = results.multi_hand_landmarks[0].landmark[17].y
              fingertips = results.multi_hand_landmarks[0].landmark
              indexFinger = fingertips[8].y
              middleFinger = fingertips[12].y
              ringFinger = fingertips[16].y
              pinkyFinger = fingertips[20].y

              if (indexFinger < knuckleCheck) and (middleFinger < knuckleCheck) and (ringFinger < knuckleCheck) and (pinkyFinger < knuckleCheck):
                playSong()

              elif (indexFinger > knuckleCheck) and (middleFinger > knuckleCheck) and (ringFinger > knuckleCheck) and (pinkyFinger > knuckleCheck):
                pauseSong()

              # set to preventing change
              elif (indexFinger < knuckleCheck) and (middleFinger > knuckleCheck) and (ringFinger > knuckleCheck) and (pinkyFinger < knuckleCheck):
                preventChange = True
                timer = 15
              
              # skip song
              elif (indexFinger > knuckleCheck) and (middleFinger < knuckleCheck) and (ringFinger > knuckleCheck) and (pinkyFinger > knuckleCheck):
                skipSong()
                timer = 15
              # skip song
              elif (indexFinger < knuckleCheck) and (middleFinger < knuckleCheck) and (ringFinger > knuckleCheck) and (pinkyFinger > knuckleCheck):
                previousSong()
                timer = 15

        # if commands are being prevented
        else:
          # if currently preventing and hand in screen
          if len(results.multi_handedness) == 1:
            fingertips = results.multi_hand_landmarks[0].landmark
            knuckleCheck = results.multi_hand_landmarks[0].landmark[17].y

            # set to not prevent change
            if (fingertips[8].y < knuckleCheck) and (fingertips[12].y > knuckleCheck) and (fingertips[16].y > knuckleCheck) and (fingertips[20].y < knuckleCheck):
              if timer == 0:
                preventChange = False
                timer = 15

    # no hands            
    else:
      frame = cv2.putText(frame, "No Hands", (5,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 0, 160), 3, cv2.LINE_AA)

    # Display the frame with hand landmarks
    cv2.imshow('Hand Recognition', frame)

    # Exit when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        changeVolume(99)
        break

# Release the video capture object and close the OpenCV windows
cap.release()
cv2.destroyAllWindows()
