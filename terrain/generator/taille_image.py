from PIL import Image
import numpy as np
import argparse

def pixeliser_image(input_path, output_path, n, m):
 
    img = Image.open(input_path).convert("RGB")
    width, height = img.size

    arr = np.array(img)

    
    block_w = width // n
    block_h = height // m

    
    pixel_img = Image.new("RGB", (n, m))
    pixels = pixel_img.load()

    
    for i in range(n):
        for j in range(m):
            block = arr[
                j * block_h:(j + 1) * block_h,
                i * block_w:(i + 1) * block_w
            ]

            mean_color = block.mean(axis=(0, 1)).astype(int)
            pixels[i, j] = tuple(mean_color)

    
    pixel_img.save(output_path)
    print("Image n×m créée :", output_path)

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", required=True, help="image d'entrée")
    parser.add_argument("--output", "-o", required=True, help="image de sortie")
    parser.add_argument("--width", "-W", type=int, default=256, help="largeur en pixels")
    parser.add_argument("--height", "-H", type=int, default=256, help="hauteur en pixels")
    args = parser.parse_args()

    pixeliser_image(args.input, args.output, args.width, args.height)
