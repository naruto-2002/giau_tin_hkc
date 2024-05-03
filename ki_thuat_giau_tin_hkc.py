from queue import Full
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np

class HKCApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HKC Image Steganography")

        self.canvas = tk.Canvas(root, width=400, height=600)
        self.canvas.pack()

        self.load_button = tk.Button(root, text="Load Image", command=self.load_image)
        self.load_button.pack()

        self.hide_save_button = tk.Button(root, text="Hide and Save Message", command=self.hide_and_save_message)
        self.hide_save_button.pack()

        self.extract_button = tk.Button(root, text="Extract Message", command=self.extract_message)
        self.extract_button.pack()

        # Tạo một Frame mới để chứa message_label và message_entry
        frame = tk.Frame(root)
        frame.pack()

        self.message_label = tk.Label(frame, text="Enter Message to Hide:")
        self.message_label.grid(row=0, column=0, sticky="e")  # Căn phải

        self.message_entry = tk.Entry(frame, width=50)
        self.message_entry.grid(row=0, column=1, sticky="w")  # Căn trái

        self.image_path = None
        self.hidden_image_path = None

        self.loaded_image = None
        self.loaded_hidden_image = None

        self.hidden_image_id = None

    def load_image(self):
        
        self.image_path = filedialog.askopenfilename()
        if self.image_path:
            self.loaded_image = Image.open(self.image_path)
            self.loaded_image.thumbnail((400, 400))
            self.render_image()
        if self.hidden_image_id:
            self.canvas.delete(self.hidden_image_id)
        self.hidden_image_path = self.image_path
        self.loaded_hidden_image = None
        self.hidden_image_id = None
        

    def load_hidden_image(self):
        if self.hidden_image_path:
            self.loaded_hidden_image = Image.open(self.hidden_image_path)
            self.loaded_hidden_image.thumbnail((400, 400))
            self.render_hidden_image()

    def render_image(self):
        self.tk_image1 = ImageTk.PhotoImage(self.loaded_image)
        self.canvas.create_text(200, 10, text="Ảnh ban đầu")
        self.canvas.create_image(0, 20, anchor=tk.NW, image=self.tk_image1)

    def render_hidden_image(self):
        self.tk_image2 = ImageTk.PhotoImage(self.loaded_hidden_image)
        self.canvas.create_text(200, 290, text="Ảnh sau khi đã được dấu tin")
        self.hidden_image_id = self.canvas.create_image(0, 300, anchor=tk.NW, image=self.tk_image2)
            
    def hide_and_save_message(self):
        if self.loaded_image:
            message = self.message_entry.get()
            if message:
                encoded_image = self.hkc_hide(self.image_path, message)
                if encoded_image is not None and encoded_image.any():
                    file_path = filedialog.asksaveasfilename(defaultextension=".png")
                    self.hidden_image_path = file_path
                    if file_path:
                        cv2.imwrite(file_path, encoded_image) 
                        messagebox.showinfo("Success", "Message hidden and encoded image saved successfully.")
                        self.load_hidden_image()
                else:
                    messagebox.showerror("Error", "Message is too long to hide.")
            else:
                messagebox.showerror("Error", "Please enter a message to hide.")
        else:
            messagebox.showerror("Error", "Please load an image first.")

    def extract_message(self):
        if self.loaded_image:
            message = self.hkc_retrieve(self.hidden_image_path, self.image_path)
            
            if message.replace('\0', '') != '':
                messagebox.showinfo("Extracted Message", message)
            else:
                messagebox.showerror("Error", "No message found in the image.")
        else:
            messagebox.showerror("Error", "Please load an image first.")

    def text_to_binary(self, text):
        return ''.join(format(i, '08b') for i in text.encode('utf-8'))

    def binary_to_text(self, binary):
        byte_array = bytearray(int(binary[i:i+8], 2) for i in range(0, len(binary), 8))
        return byte_array.decode('utf-8')

    def hkc_hide(self, image_path, data):
        # Convert text to binary
        data = self.text_to_binary(data)

        # Load the image
        image = cv2.imread(image_path)

        # Calculate histogram for each channel
        hist_r = cv2.calcHist([image[:,:,0]], [0], None, [256], [0,256])
        hist_g = cv2.calcHist([image[:,:,1]], [0], None, [256], [0,256])
        hist_b = cv2.calcHist([image[:,:,2]], [0], None, [256], [0,256])

        # Find peak point for each channel
        peak_r = np.argmax(hist_r)
        peak_g = np.argmax(hist_g)
        peak_b = np.argmax(hist_b)

        # Hide data in each channel
        data_idx = 0
        for i in range(image.shape[0]):
            for j in range(image.shape[1]):
                for k in range(image.shape[2]):
                    peak = peak_r if k == 0 else peak_g if k == 1 else peak_b
                    if image[i, j, k] == peak - 2 or image[i, j, k] == peak + 2:
                        if data[data_idx] == '1':
                            image[i, j, k] += 1 if image[i, j, k] == peak - 2 else -1
                        data_idx += 1
                        if data_idx >= len(data):
                            return image
        return image

    def hkc_retrieve(self, image_path, original_image_path):
        # Load the images
        image = cv2.imread(image_path)
        original_image = cv2.imread(original_image_path)

        # Calculate histogram for each channel
        hist_r = cv2.calcHist([original_image[:,:,0]], [0], None, [256], [0,256])
        hist_g = cv2.calcHist([original_image[:,:,1]], [0], None, [256], [0,256])
        hist_b = cv2.calcHist([original_image[:,:,2]], [0], None, [256], [0,256])

        # Find peak point for each channel
        peak_r = np.argmax(hist_r)
        peak_g = np.argmax(hist_g)
        peak_b = np.argmax(hist_b)

        # Retrieve data from each channel
        data = ''
        for i in range(image.shape[0]):
            for j in range(image.shape[1]):
                for k in range(image.shape[2]):
                    peak = peak_r if k == 0 else peak_g if k == 1 else peak_b
                    if original_image[i, j, k] == peak - 2 or original_image[i, j, k] == peak + 2:
                        if original_image[i, j, k] != image[i, j, k]:
                            data += '1'
                        else:
                            data += '0'

        # Convert binary to text
        data = self.binary_to_text(data)
        return data


if __name__ == "__main__":
    root = tk.Tk()
    app = HKCApp(root)
    root.mainloop()