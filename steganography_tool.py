import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image

# --- Core Steganography Functions ---

def text_to_binary(text):
    """Converts a string to its binary representation."""
    return ''.join(format(ord(char), '08b') for char in text)

def binary_to_text(binary_string):
    """Converts a binary string to its text representation."""
    text = ""
    for i in range(0, len(binary_string), 8):
        byte = binary_string[i:i+8]
        if len(byte) == 8: # Ensure it's a full byte
            text += chr(int(byte, 2))
    return text

def hide_text(image_path, secret_message, output_path):
    """
    Hides a secret message within an image using LSB steganography.
    Args:
        image_path (str): Path to the cover image.
        secret_message (str): The message to hide.
        output_path (str): Path to save the steganographic image.
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        img = Image.open(image_path)
        # Ensure image is in RGB mode for consistent pixel access
        if img.mode != 'RGB':
            img = img.convert('RGB')

        width, height = img.size
        pixels = img.load()

        # Add a unique delimiter to mark the end of the message
        # This delimiter is crucial for knowing when to stop extracting
        delimiter = '1111111111111110' # 16 bits: 14 ones, then 0
        binary_message = text_to_binary(secret_message) + delimiter
        data_index = 0

        # Calculate maximum capacity
        # Each pixel has 3 color channels (R, G, B), each can store 1 bit
        max_bits_capacity = width * height * 3
        if len(binary_message) > max_bits_capacity:
            messagebox.showerror("Capacity Error",
                                 f"Message is too large for the image. "
                                 f"Max capacity: {max_bits_capacity // 8} characters. "
                                 f"Your message: {len(secret_message)} characters.")
            return False

        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]

                # Modify Red channel LSB
                if data_index < len(binary_message):
                    r = (r & ~1) | int(binary_message[data_index])
                    data_index += 1
                else:
                    pixels[x, y] = (r, g, b) # No change needed, but update pixel
                    continue # Move to next pixel if message is fully embedded

                # Modify Green channel LSB
                if data_index < len(binary_message):
                    g = (g & ~1) | int(binary_message[data_index])
                    data_index += 1
                else:
                    pixels[x, y] = (r, g, b)
                    continue

                # Modify Blue channel LSB
                if data_index < len(binary_message):
                    b = (b & ~1) | int(binary_message[data_index])
                    data_index += 1
                else:
                    pixels[x, y] = (r, g, b)
                    continue

                pixels[x, y] = (r, g, b)

                if data_index >= len(binary_message):
                    break # All data embedded
            if data_index >= len(binary_message):
                break

        img.save(output_path)
        return True
    except Exception as e:
        messagebox.showerror("Error Hiding Message", f"An error occurred: {e}")
        return False

def reveal_text(image_path):
    """
    Reveals a secret message hidden within an image using LSB steganography.
    Args:
        image_path (str): Path to the steganographic image.
    Returns:
        str: The revealed message, or an error message if not found.
    """
    try:
        img = Image.open(image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        pixels = img.load()
        binary_message = ""
        delimiter = '1111111111111110' # Must match the delimiter used for embedding

        for y in range(img.height):
            for x in range(img.width):
                r, g, b = pixels[x, y]

                binary_message += str(r & 1) # Get LSB of Red
                binary_message += str(g & 1) # Get LSB of Green
                binary_message += str(b & 1) # Get LSB of Blue

                # Check for delimiter
                if delimiter in binary_message:
                    # Remove the delimiter and any extra bits after it
                    binary_message = binary_message[:binary_message.find(delimiter)]
                    return binary_to_text(binary_message)

        return "No secret message found or delimiter not reached. The image might not contain a hidden message or is corrupted."
    except Exception as e:
        messagebox.showerror("Error Revealing Message", f"An error occurred: {e}")
        return "Error: Could not reveal message."

# --- Tkinter GUI Application ---

class SteganographyApp:
    def __init__(self, master):
        self.master = master
        master.title("Simple LSB Steganography Tool")
        master.geometry("600x650") # Set a fixed window size for better layout

        self.image_path_hide = ""
        self.image_path_reveal = ""

        # --- Hide Message Section ---
        self.hide_frame = tk.LabelFrame(master, text="Hide Message", padx=10, pady=10)
        self.hide_frame.pack(padx=20, pady=10, fill="x", expand=True)

        tk.Label(self.hide_frame, text="1. Select Cover Image (PNG/BMP):").pack(anchor="w", pady=(5,0))
        self.select_image_btn = tk.Button(self.hide_frame, text="Browse Image", command=self.select_image_for_hide)
        self.select_image_btn.pack(pady=5)
        self.image_label = tk.Label(self.hide_frame, text="No image selected", fg="blue")
        self.image_label.pack(pady=(0,10))

        tk.Label(self.hide_frame, text="2. Enter Secret Message:").pack(anchor="w", pady=(5,0))
        self.message_entry = tk.Entry(self.hide_frame, width=70, font=('Arial', 10))
        self.message_entry.pack(pady=5)

        self.hide_btn = tk.Button(self.hide_frame, text="Hide Message", command=self.perform_hide, bg="lightblue", fg="black", font=('Arial', 10, 'bold'))
        self.hide_btn.pack(pady=15)

        # --- Reveal Message Section ---
        self.reveal_frame = tk.LabelFrame(master, text="Reveal Message", padx=10, pady=10)
        self.reveal_frame.pack(padx=20, pady=10, fill="x", expand=True)

        tk.Label(self.reveal_frame, text="1. Select Steganographic Image (PNG/BMP):").pack(anchor="w", pady=(5,0))
        self.select_stego_btn = tk.Button(self.reveal_frame, text="Browse Stego Image", command=self.select_image_for_reveal)
        self.select_stego_btn.pack(pady=5)
        self.stego_image_label = tk.Label(self.reveal_frame, text="No stego image selected", fg="blue")
        self.stego_image_label.pack(pady=(0,10))

        self.reveal_btn = tk.Button(self.reveal_frame, text="Reveal Message", command=self.perform_reveal, bg="lightgreen", fg="black", font=('Arial', 10, 'bold'))
        self.reveal_btn.pack(pady=15)

        tk.Label(self.reveal_frame, text="Revealed Message:").pack(anchor="w", pady=(5,0))
        self.revealed_message_text = tk.Text(self.reveal_frame, height=8, width=70, font=('Arial', 10), wrap="word")
        self.revealed_message_text.pack(pady=5)
        self.revealed_message_text.config(state=tk.DISABLED) # Make it read-only

    def select_image_for_hide(self):
        self.image_path_hide = filedialog.askopenfilename(
            title="Select Cover Image",
            filetypes=[("PNG files", "*.png"), ("BMP files", "*.bmp"), ("All files", "*.*")]
        )
        if self.image_path_hide:
            self.image_label.config(text=self.image_path_hide.split('/')[-1])
        else:
            self.image_label.config(text="No image selected")

    def perform_hide(self):
        if not self.image_path_hide:
            messagebox.showerror("Input Error", "Please select a cover image first.")
            return
        secret_message = self.message_entry.get()
        if not secret_message:
            messagebox.showerror("Input Error", "Please enter a secret message.")
            return

        output_file_path = filedialog.asksaveasfilename(
            title="Save Steganographic Image As",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("BMP files", "*.bmp")]
        )
        if output_file_path:
            if hide_text(self.image_path_hide, secret_message, output_file_path):
                messagebox.showinfo("Success", f"Message hidden successfully in:\n{output_file_path}")
                self.message_entry.delete(0, tk.END) # Clear message input
                self.image_path_hide = "" # Clear selected image path
                self.image_label.config(text="No image selected")
            # Error messages are handled within hide_text function via messagebox

    def select_image_for_reveal(self):
        self.image_path_reveal = filedialog.askopenfilename(
            title="Select Steganographic Image",
            filetypes=[("PNG files", "*.png"), ("BMP files", "*.bmp"), ("All files", "*.*")]
        )
        if self.image_path_reveal:
            self.stego_image_label.config(text=self.image_path_reveal.split('/')[-1])
        else:
            self.stego_image_label.config(text="No stego image selected")

    def perform_reveal(self):
        if not self.image_path_reveal:
            messagebox.showerror("Input Error", "Please select a steganographic image first.")
            return

        self.revealed_message_text.config(state=tk.NORMAL) # Enable for writing
        self.revealed_message_text.delete(1.0, tk.END) # Clear previous text

        revealed_msg = reveal_text(self.image_path_reveal)
        self.revealed_message_text.insert(tk.END, revealed_msg)
        self.revealed_message_text.config(state=tk.DISABLED) # Disable again

        if "No secret message found" not in revealed_msg and "Error:" not in revealed_msg:
            messagebox.showinfo("Result", "Message revealed successfully!")
        elif "Error:" in revealed_msg:
            pass # Error message already shown by reveal_text
        else:
            messagebox.showinfo("Result", "No hidden message found in the selected image.")
        self.image_path_reveal = "" # Clear selected image path
        self.stego_image_label.config(text="No stego image selected")


# --- Main execution block ---
if __name__ == "__main__":
    root = tk.Tk()
    app = SteganographyApp(root)
    root.mainloop()
