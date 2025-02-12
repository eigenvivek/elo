import os
import random
import re
import sys
import time

from PIL import Image
from pynput import keyboard


def load_image_pairs():
    # Get list of image files from slices directory
    image_dir = "slices"
    image_files = [
        f
        for f in os.listdir(image_dir)
        if f.startswith("Walnut") and "gt" not in f.lower()
    ]  # Exclude "gt" files

    # Group files by their ID and view count using the new naming convention
    image_groups = {}
    pattern = r"Walnut(\d+)_n(\d+)_.*\.png"

    for img_file in image_files:
        match = re.match(pattern, img_file)
        if match:
            walnut_id = int(match.group(1))
            view_count = int(match.group(2))
            key = (walnut_id, view_count)
            if key not in image_groups:
                image_groups[key] = []
            image_groups[key].append(img_file)

    return image_groups


def close_all_images():
    # Get all active windows
    import platform
    import subprocess

    time.sleep(0.2)  # Pause for 1 second before closing

    if platform.system() == "Darwin":  # macOS
        subprocess.run(["killall", "Preview"])
    elif platform.system() == "Windows":
        subprocess.run(
            ["taskkill", "/F", "/IM", "Microsoft.Photos.exe"], capture_output=True
        )
    elif platform.system() == "Linux":
        subprocess.run(["pkill", "display"])


def display_images(img1_path, img2_path):
    # Close any open images first
    close_all_images()

    # Open and display images side by side
    img1 = Image.open(os.path.join("slices", img1_path))
    img2 = Image.open(os.path.join("slices", img2_path))

    # Create a new image with combined width plus padding
    padding = 20  # pixels of whitespace between images
    total_width = img1.width + img2.width + padding
    max_height = max(img1.height, img2.height)
    combined_image = Image.new(
        "RGB", (total_width, max_height), "white"
    )  # white background

    # Paste images with padding between them
    combined_image.paste(img1, (0, 0))
    combined_image.paste(img2, (img1.width + padding, 0))

    # Display the combined image
    combined_image.show()

    # Close individual images
    img1.close()
    img2.close()

    return combined_image


def get_user_response():
    result = None

    def on_press(key):
        nonlocal result
        if key == keyboard.Key.esc:
            print("\nExiting program...")
            close_all_images()  # Close any open images
            os._exit(0)  # Force exit the program
        elif key == keyboard.Key.left:
            result = 0  # Image 1 is better than Image 2
            return False
        elif key == keyboard.Key.right:
            result = 1  # Image 2 is better than Image 1
            return False
        elif key == keyboard.Key.down:
            result = -1  # Images are equal
            return False
        elif key == keyboard.Key.up:
            result = 0.5  # Both images are bad
            return False
        else:
            print(
                "Invalid key! Please use arrow keys: ← (left: 1>2) → (right: 2>1) ↓ (down: both bad) ↑ (up: both good)"
            )
            return True  # Keep listening for valid input

    # Create and start keyboard listener
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

    return result


def print_instructions():
    print("\nImage Comparison Controls:")
    print("←  Left Arrow  : Image 1 is better than Image 2")
    print("→  Right Arrow : Image 2 is better than Image 1")
    print("↓  Down Arrow  : Images are equally bad")
    print("↑  Up Arrow    : Images are equally good")
    print("ESC           : Exit program")
    print("\nWaiting for images to load...\n")


def main():
    # Get username
    if len(sys.argv) != 2:
        print("Usage: python game.py <username>")
        sys.exit(1)
    username = sys.argv[1]

    # Print instructions
    print_instructions()

    # Create results directory if it doesn't exist
    os.makedirs("results", exist_ok=True)

    # Create user's results file if it doesn't exist
    results_file = os.path.join("results", f"{username}.csv")
    if not os.path.exists(results_file):
        with open(results_file, "w") as f:
            f.write("walnut_id,n_views,algorithm1,algorithm2,score\n")

    image_groups = load_image_pairs()

    # Compile regex pattern for parsing filenames
    pattern = r"Walnut(\d+)_n(\d+)_(\w+)\.png"

    # Infinite loop to keep generating comparisons
    while True:
        # Get a random group that has at least 2 images
        valid_groups = [(k, v) for k, v in image_groups.items() if len(v) >= 2]
        if not valid_groups:
            print("No valid image groups found!")
            sys.exit(1)

        key, files = random.choice(valid_groups)
        img1, img2 = random.sample(files, 2)  # Randomly select 2 images from the group

        # Parse filenames for detailed information
        match1 = re.match(pattern, img1)
        match2 = re.match(pattern, img2)

        if match1 and match2:
            walnut_id = match1.group(1)  # Both should have same walnut_id
            n_views = match1.group(2)  # Both should have same n_views
            algo1 = match1.group(3)
            algo2 = match2.group(3)

            # Display images
            combined_image = display_images(img1, img2)

            # Get user response
            score = get_user_response()

            # Close the image
            combined_image.close()

            # Save the result with parsed information
            with open(results_file, "a") as f:
                f.write(f"{walnut_id},{n_views},{algo1},{algo2},{score}\n")


if __name__ == "__main__":
    main()
