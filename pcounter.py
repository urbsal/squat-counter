import os
import math
import cv2
import mediapipe as mp
import gradio as gr


# Settings
UP_ANGLE = 160# above this angel is considered as standing position
DOWN_ANGLE = 100 ## below this angel is considered as down position
SMOOTHING_WINDOW = 3 ## for moving average calcualtion
VISIBILITY_THRESHOLD = 0.5


# MediaPipe
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

pose = mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)


# Live counter state
rep_count = 0
state = "up"
recent_angles = []


# Calculate knee angle
def calculate_angle(point_a, point_b, point_c):
    ax, ay = point_a
    bx, by = point_b
    cx, cy = point_c

    v1x = ax - bx
    v1y = ay - by

    v2x = cx - bx
    v2y = cy - by

    dot_product = v1x * v2x + v1y * v2y

    length1 = math.sqrt(v1x ** 2 + v1y ** 2)
    length2 = math.sqrt(v2x ** 2 + v2y ** 2)

    if length1 == 0 or length2 == 0:
        return 180

    cos_value = dot_product / (length1 * length2)
    cos_value = max(-1, min(1, cos_value)) # The value of can be 0 to 180 

    return math.degrees(math.acos(cos_value))


# Update squat state
def update_counter(angle):
    global rep_count, state, recent_angles

    recent_angles.append(angle)

    if len(recent_angles) > SMOOTHING_WINDOW:
        recent_angles.pop(0)

    smoothed_angle = sum(recent_angles) / len(recent_angles)

    if state == "up" and smoothed_angle <= DOWN_ANGLE:
        state = "down"

    elif state == "down" and smoothed_angle >= UP_ANGLE:
        state = "up"
        rep_count += 1

    return smoothed_angle


# Reset live counter
def reset_counter():
    global rep_count, state, recent_angles

    rep_count = 0
    state = "up"
    recent_angles = []

    return "Repetitions: 0"


# Process live webcam frame
def process_frame(frame): ## The frame is provide by gradio where numpy extract the array of frame
    if frame is None:
        return None, "Repetitions: 0"

    image = frame.copy() ## duplicate the image 
    results = pose.process(image) 

    if not results.pose_landmarks:
        return image, f"Repetitions: {rep_count}"

    landmarks = results.pose_landmarks.landmark

    hip = landmarks[23] ## all the numbers are define position of body such as landmark 1 can be head or eye as an example 
    knee = landmarks[25]
    ankle = landmarks[27]

    if (
        hip.visibility < VISIBILITY_THRESHOLD
        or knee.visibility < VISIBILITY_THRESHOLD
        or ankle.visibility < VISIBILITY_THRESHOLD
    ):
        return image, f"Repetitions: {rep_count}"

    height, width, _ = image.shape ## the image shape is obtained here from which we find the cordinates of the hip, knee and ankle 

    hip_point = (int(hip.x * width), int(hip.y * height))
    knee_point = (int(knee.x * width), int(knee.y * height))
    ankle_point = (int(ankle.x * width), int(ankle.y * height))

    angle = calculate_angle(
        hip_point,
        knee_point,
        ankle_point
    )

    smoothed_angle = update_counter(angle)

    mp_drawing.draw_landmarks(
        image,
        results.pose_landmarks,
        mp_pose.POSE_CONNECTIONS
    )

    cv2.putText(
        image,
        f"Angle: {int(smoothed_angle)}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2
    )

    cv2.putText(
        image,
        f"Reps: {rep_count}",
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2
    )

    cv2.putText(
        image,
        f"State: {state.upper()}",
        (20, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2
    )

    return image, f"Repetitions: {rep_count}"


# Process uploaded video
def count_reps_in_video(video_path):
    if video_path is None:
        return "Please upload a video."

    if not os.path.exists(video_path):
        return "Video file not found."

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        return "Could not open video."

    video_count = 0
    video_state = "up"
    video_angles = []

    total_frames = 0
    detected_frames = 0

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        total_frames += 1

        image = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        results = pose.process(image)

        if not results.pose_landmarks:
            continue

        landmarks = results.pose_landmarks.landmark

        hip = landmarks[23]
        knee = landmarks[25]
        ankle = landmarks[27]

        if (
            hip.visibility < VISIBILITY_THRESHOLD
            or knee.visibility < VISIBILITY_THRESHOLD
            or ankle.visibility < VISIBILITY_THRESHOLD
        ):
            continue

        detected_frames += 1

        height, width, _ = image.shape

        hip_point = (int(hip.x * width), int(hip.y * height))
        knee_point = (int(knee.x * width), int(knee.y * height))
        ankle_point = (int(ankle.x * width), int(ankle.y * height))

        angle = calculate_angle(
            hip_point,
            knee_point,
            ankle_point
        )

        video_angles.append(angle)

        if len(video_angles) > SMOOTHING_WINDOW:
            video_angles.pop(0)

        smoothed_angle = sum(video_angles) / len(video_angles)

        if video_state == "up" and smoothed_angle <= DOWN_ANGLE:
            video_state = "down"

        elif video_state == "down" and smoothed_angle >= UP_ANGLE:
            video_state = "up"
            video_count += 1

    cap.release()

    if total_frames == 0:
        return "No readable frames in the video."

    if detected_frames == 0:
        return "No reliable pose detected. Make sure your body is visible."

    return (
        f"Repetitions: {video_count}\n"
        f"Frames processed: {total_frames}\n"
        f"Pose detected: {detected_frames} frames"
    )


# Gradio interface
with gr.Blocks() as demo:

    gr.Markdown("#  Squat Rep Counter")

    with gr.Tabs():

        # Upload video
        with gr.Tab("Upload Video"):

            video = gr.Video(
                sources=["upload"],
                label="Upload Squat Video"
            )

            count_button = gr.Button(
                "Count Squats",
                variant="primary"
            )

            video_result = gr.Textbox(
                label="Result"
            )

            count_button.click(
                count_reps_in_video,
                inputs=video,
                outputs=video_result
            )

        # Live camera
        with gr.Tab(" Live Camera"):

            camera = gr.Image(
                sources=["webcam"],
                streaming=True,
                type="numpy",
                label="Camera"
            )

            output = gr.Image(
                label="Pose Detection"
            )

            counter = gr.Textbox(
                value="Repetitions: 0",
                label="Counter"
            )

            reset_button = gr.Button("Reset Counter")

            camera.stream(
                process_frame,
                inputs=camera,
                outputs=[output, counter]
            )

            reset_button.click(
                reset_counter,
                inputs=None,
                outputs=counter
            )


if __name__ == "__main__":
    demo.launch()