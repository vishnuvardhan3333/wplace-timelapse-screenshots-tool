#usage: python timelapse.py .\project\ output_timelapse.mp4 --seconds_per_image 0.1
# 0.1 seconds per image is 10fps, if you want 60fps set it to 0.01667
import cv2
import os
import argparse
import numpy as np

def images_to_video(input_dir, output_file, fps):
    # Get all image files
    images = [f for f in os.listdir(input_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    images.sort()  # Sort ascending by filename

    if not images:
        print("No images found in the directory.")
        return

    # Read the first image to get frame size (RGB only)
    first_img_path = os.path.join(input_dir, images[0])
    frame = cv2.imread(first_img_path, cv2.IMREAD_UNCHANGED)
    if frame.shape[2] == 4:  # if RGBA
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
    height, width, layers = frame.shape

    # Define video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(output_file, fourcc, fps, (width, height))

    # Add images to video
    for img_name in images:
        img_path = os.path.join(input_dir, img_name)
        img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)  # keep alpha if exists
        if img is None:
            print(f"Skipping {img_name} (could not read)")
            continue

        # Separate alpha channel if present
        if img.shape[2] == 4:
            alpha = img[:, :, 3] / 255.0
            img = img[:, :, :3]
        else:
            alpha = np.ones(img.shape[:2], dtype=np.float32)

        # Create white background
        canvas = np.ones((height, width, 3), dtype=np.uint8) * 255

        # Scale image to fit inside the frame while keeping aspect ratio
        img_h, img_w = img.shape[:2]
        scale = min(width / img_w, height / img_h)
        new_w, new_h = int(img_w * scale), int(img_h * scale)
        resized_img = cv2.resize(img, (new_w, new_h))
        resized_alpha = cv2.resize(alpha, (new_w, new_h))

        # Center position
        x_offset = (width - new_w) // 2
        y_offset = (height - new_h) // 2

        # Region of interest on canvas
        roi = canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w]

        # Blend using alpha channel
        for c in range(3):
            roi[:, :, c] = (resized_alpha * resized_img[:, :, c] +
                            (1 - resized_alpha) * roi[:, :, c])

        canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = roi

        video.write(canvas.astype(np.uint8))

    video.release()
    print(f"Video saved as {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Combine images into a video with white background, preserving transparency.")
    parser.add_argument("input_dir", help="Folder containing the images")
    parser.add_argument("output_file", help="Path to save the output video (e.g., output.mp4)")
    parser.add_argument("--seconds_per_image", type=float, default=1, help="How many seconds each image is shown")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second of the video file")

    args = parser.parse_args()

    # Calculate actual FPS based on seconds_per_image
    display_fps = 1 / args.seconds_per_image
    total_fps = display_fps if display_fps > 0 else 1

    images_to_video(args.input_dir, args.output_file, total_fps)


