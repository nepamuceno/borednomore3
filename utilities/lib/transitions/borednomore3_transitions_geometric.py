"""
Geometric Transitions: Box, Circle, Split, Radial, Checkerboard, Cube, Diamond
"""
import cv2
import numpy as np
import random


class GeometricTransitions:
    def __init__(self, screen_width, screen_height, debug, tmp_dir):
        self.w = screen_width
        self.h = screen_height
        self.debug = debug
        self.tmp_dir = tmp_dir
    
    def generate(self, family, old_img, new_img, direction, num_frames):
        if family == "split":
            return self.split(old_img, new_img, direction, num_frames)
        elif family == "box":
            return self.box(old_img, new_img, direction, num_frames)
        elif family == "circle":
            return self.circle(old_img, new_img, direction, num_frames)
        elif family == "radial":
            return self.radial(old_img, new_img, direction, num_frames)
        elif family == "checkerboard":
            return self.checkerboard(old_img, new_img, direction, num_frames)
        elif family == "cube":
            return self.cube(old_img, new_img, direction, num_frames)
        elif family == "diamond":
            return self.diamond(old_img, new_img, direction, num_frames)
        return []
    
    def split(self, old_img, new_img, direction, num_frames):
        frames = []
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            frame = new_img.copy()
            
            if direction == "horizontal":
                half_h = self.h // 2
                gap = int(progress * half_h)
                if gap < half_h:
                    frame[:half_h - gap, :] = old_img[:half_h - gap, :]
                    frame[half_h + gap:, :] = old_img[half_h + gap:, :]
            else:  # vertical
                half_w = self.w // 2
                gap = int(progress * half_w)
                if gap < half_w:
                    frame[:, :half_w - gap] = old_img[:, :half_w - gap]
                    frame[:, half_w + gap:] = old_img[:, half_w + gap:]
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        return frames
    
    def box(self, old_img, new_img, direction, num_frames):
        frames = []
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            
            if direction == "in":
                frame = old_img.copy()
                box_w, box_h = int(progress * self.w), int(progress * self.h)
                x1, y1 = (self.w - box_w) // 2, (self.h - box_h) // 2
                x2, y2 = x1 + box_w, y1 + box_h
                if box_w > 0 and box_h > 0:
                    frame[y1:y2, x1:x2] = new_img[y1:y2, x1:x2]
            else:
                frame = new_img.copy()
                box_w, box_h = int((1.0 - progress) * self.w), int((1.0 - progress) * self.h)
                x1, y1 = (self.w - box_w) // 2, (self.h - box_h) // 2
                x2, y2 = x1 + box_w, y1 + box_h
                if box_w > 0 and box_h > 0:
                    frame[y1:y2, x1:x2] = old_img[y1:y2, x1:x2]
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        return frames
    
    def circle(self, old_img, new_img, direction, num_frames):
        frames = []
        center = (self.w // 2, self.h // 2)
        max_radius = int(np.sqrt(self.w**2 + self.h**2) / 2) + 50
        
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            
            if direction == "in":
                radius = int(progress * max_radius)
                frame = old_img.copy()
                mask = np.zeros((self.h, self.w), dtype=np.uint8)
                cv2.circle(mask, center, radius, 255, -1)
                mask = cv2.merge([mask, mask, mask])
                frame = np.where(mask > 0, new_img, old_img)
            else:
                radius = int((1.0 - progress) * max_radius)
                frame = new_img.copy()
                mask = np.zeros((self.h, self.w), dtype=np.uint8)
                cv2.circle(mask, center, radius, 255, -1)
                mask = cv2.merge([mask, mask, mask])
                frame = np.where(mask > 0, old_img, new_img)
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        return frames
    
    def radial(self, old_img, new_img, direction, num_frames):
        frames = []
        center = (self.w // 2, self.h // 2)
        
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            frame = old_img.copy()
            mask = np.zeros((self.h, self.w), dtype=np.uint8)
            
            if direction == "cw":
                end_angle = progress * 360
                cv2.ellipse(mask, center, (self.w, self.h), -90, 0, end_angle, 255, -1)
            else:  # ccw
                start_angle = 360 - (progress * 360)
                cv2.ellipse(mask, center, (self.w, self.h), -90, start_angle, 360, 255, -1)
            
            mask = cv2.merge([mask, mask, mask])
            frame = np.where(mask > 0, new_img, old_img)
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        return frames
    
    def checkerboard(self, old_img, new_img, pattern, num_frames):
        frames = []
        checker_size = 40
        
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            frame = old_img.copy()
            
            for y in range(0, self.h, checker_size):
                for x in range(0, self.w, checker_size):
                    checker_row = y // checker_size
                    checker_col = x // checker_size
                    
                    is_checker = (checker_row + checker_col) % 2 == (0 if pattern == "normal" else 1)
                    reveal_threshold = progress + random.random() * 0.1
                    
                    if is_checker and reveal_threshold > 0.5:
                        y2, x2 = min(y + checker_size, self.h), min(x + checker_size, self.w)
                        frame[y:y2, x:x2] = new_img[y:y2, x:x2]
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        return frames
    
    def cube(self, old_img, new_img, direction, num_frames):
        frames = []
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            scale = abs(np.cos(progress * np.pi / 2))
            
            if direction in ["left", "right"]:
                base = old_img if progress < 0.5 else new_img
                if (progress < 0.5 and direction == "right") or (progress >= 0.5 and direction == "left"):
                    base = cv2.flip(base, 1)
                new_w = max(1, int(self.w * scale))
                offset = (self.w - new_w) // 2
                resized = cv2.resize(base, (new_w, self.h))
                frame = np.zeros((self.h, self.w, 3), dtype=np.uint8)
                frame[:, offset:offset+new_w] = resized
            else:  # up, down
                base = old_img if progress < 0.5 else new_img
                if (progress < 0.5 and direction == "down") or (progress >= 0.5 and direction == "up"):
                    base = cv2.flip(base, 0)
                new_h = max(1, int(self.h * scale))
                offset = (self.h - new_h) // 2
                resized = cv2.resize(base, (self.w, new_h))
                frame = np.zeros((self.h, self.w, 3), dtype=np.uint8)
                frame[offset:offset+new_h, :] = resized
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        return frames
    
    def diamond(self, old_img, new_img, direction, num_frames):
        frames = []
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            mask = np.zeros((self.h, self.w), dtype=np.uint8)
            
            size = int(progress * max(self.w, self.h)) if direction == "in" else int((1.0 - progress) * max(self.w, self.h))
            
            center_x, center_y = self.w // 2, self.h // 2
            pts = np.array([
                [center_x, center_y - size],
                [center_x + size, center_y],
                [center_x, center_y + size],
                [center_x - size, center_y]
            ], np.int32)
            cv2.fillPoly(mask, [pts], 255)
            
            mask = cv2.merge([mask, mask, mask])
            frame = np.where(mask > 0, new_img if direction == "in" else old_img, 
                           old_img if direction == "in" else new_img)
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        return frames
